import logging
from datetime import datetime, timezone
from typing import Dict

from cezzis_kafka import KafkaProducer
from cezzis_otel import get_propagation_headers
from injector import inject
from mediatr import GenericQuery, Mediator
from opentelemetry import trace

from cocktails_extraction_agent.application.services.cocktails_api_service import CocktailsApiService
from cocktails_extraction_agent.domain.config.app_options import AppOptions
from cocktails_extraction_agent.domain.models.cocktail_extraction_model import (
    CocktailExtractionModel,
)
from cocktails_extraction_agent.domain.tools import remove_emojis, remove_html_tags, remove_markdown
from cocktails_extraction_agent.domain.tools.json_special_char_remover.json_special_char_remover import (
    remove_special_json_characters,
)
from cocktails_extraction_agent.infrastructure.clients.cocktails_api.cocktail_api import CocktailModel
from cocktails_extraction_agent.infrastructure.llm.llm_content_cleaner import LLMContentCleaner


class ProcessExtractionEventCommand(GenericQuery[bool]):
    def __init__(self, model: CocktailModel) -> None:
        self.model = model


@Mediator.behavior
class ProcessExtractionEventCommandValidator:
    def handle(self, command: ProcessExtractionEventCommand, next) -> None:
        if not command.model or not command.model.id:
            raise ValueError("Invalid cocktail model provided for extraction processing.")
        return next()


@Mediator.handler
class ProcessExtractionEventCommandHandler:
    @inject
    def __init__(
        self,
        app_options: AppOptions,
        kafka_producer: KafkaProducer,
        llm_content_cleaner: LLMContentCleaner,
        cocktails_api_service: CocktailsApiService,
    ) -> None:
        self.kafka_producer = kafka_producer
        self.app_options = app_options
        self.llm_content_cleaner = llm_content_cleaner
        self.cocktails_api_service = cocktails_api_service
        self.logger = logging.getLogger("process_extraction_event_command_handler")
        self.tracer = trace.get_tracer("extraction_agent")
        self.cocktail_process_log: Dict[str, datetime] = {}

    async def handle(self, command: ProcessExtractionEventCommand) -> bool:
        self.logger.info("Processing extraction event")

        self.logger.info(
            msg="Processing cocktail extraction message item",
            extra={
                "cocktail_id": command.model.id,
            },
        )

        latest_cocktail_data = await self.cocktails_api_service.get_cocktail(
            id=command.model.id,
            resolve_ingredients=True,
            measurement_system="imperial",
        )

        if not latest_cocktail_data:
            self.logger.error(
                msg="Cocktail data not found from cocktails API, skipping extraction processing",
                extra={
                    "cocktail_id": command.model.id,
                },
            )
            return True

        last_processed_time = self.cocktail_process_log.get(latest_cocktail_data.id)
        utc_now = datetime.now(timezone.utc)

        if (
            last_processed_time
            and (utc_now - last_processed_time).total_seconds() < self.app_options.cocktail_reprocess_cooldown_seconds
        ):
            self.logger.info(
                msg="Skipping cocktail extraction processing due to recent processing",
                extra={
                    "cocktail_id": latest_cocktail_data.id,
                    "last_processed_time": last_processed_time.isoformat(),
                },
            )
            return True

        result_content = ""

        if not self.app_options.use_llm:
            # ----------------------------------------------------------------------------
            # If not using LLM, use basic cleaning tools
            # ----------------------------------------------------------------------------
            result_content = await remove_markdown.ainvoke(latest_cocktail_data.content or "")
            result_content = await remove_html_tags.ainvoke(result_content or "")
            result_content = await remove_emojis.ainvoke(result_content or "")
            result_content = await remove_special_json_characters.ainvoke(result_content or "")
        else:
            result_content = await self.llm_content_cleaner.clean_content(latest_cocktail_data.id)

        # Take the cleaned content and create the extraction model
        extraction_model = CocktailExtractionModel(
            cocktail_model=latest_cocktail_data,
            extraction_text=result_content or "",
        )

        if extraction_model.extraction_text.strip() == "":
            self.logger.warning(
                msg="Empty extraction text received after processing",
                extra={
                    "cocktail_id": latest_cocktail_data.id,
                },
            )
            return True

        self.logger.info(
            msg="Sending cocktail extraction model to chunking topic",
            extra={
                "messaging.kafka.bootstrap_servers": self.kafka_producer.settings.bootstrap_servers,
                "messaging.kafka.topic_name": self.app_options.results_topic_name,
                "cocktail_id": latest_cocktail_data.id,
            },
        )

        self.kafka_producer.send_and_wait(
            topic=self.app_options.results_topic_name,
            key=latest_cocktail_data.id,
            message=extraction_model.as_serializable_json(),
            headers=get_propagation_headers(),
            timeout=30.0,
        )

        # record the processing time for this cocktail to prevent immediate reprocessing
        # if multiple extraction events for the same cocktail are received in a short time frame
        self.cocktail_process_log[latest_cocktail_data.id] = utc_now

        self.logger.info(
            msg="Cocktail extraction succeeded",
            extra={
                "messaging.kafka.bootstrap_servers": self.kafka_producer.settings.bootstrap_servers,
                "messaging.kafka.topic_name": self.app_options.results_topic_name,
                "cocktail_id": latest_cocktail_data.id,
                "cocktail_ingestion_state": "extraction-succeeded",
            },
        )

        return True
