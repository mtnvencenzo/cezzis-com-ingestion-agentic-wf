import logging

from cezzis_kafka import KafkaProducer
from cezzis_otel import get_propagation_headers
from injector import inject
from mediatr import GenericQuery, Mediator
from opentelemetry import trace

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
    ) -> None:
        self.kafka_producer = kafka_producer
        self.app_options = app_options
        self.llm_content_cleaner = llm_content_cleaner
        self.logger = logging.getLogger("process_extraction_event_command_handler")
        self.tracer = trace.get_tracer("extraction_agent")

    async def handle(self, command: ProcessExtractionEventCommand) -> bool:
        self.logger.info("Processing extraction event")

        self.logger.info(
            msg="Processing cocktail extraction message item",
            extra={
                "cocktail_id": command.model.id,
            },
        )

        result_content = ""

        if not self.app_options.use_llm:
            # ----------------------------------------------------------------------------
            # If not using LLM, use basic cleaning tools
            # ----------------------------------------------------------------------------
            result_content = await remove_markdown.ainvoke(command.model.content or "")
            result_content = await remove_html_tags.ainvoke(result_content or "")
            result_content = await remove_emojis.ainvoke(result_content or "")
            result_content = await remove_special_json_characters.ainvoke(result_content or "")
        else:
            result_content = await self.llm_content_cleaner.clean_content(command.model.content or "")

        # Take the cleaned content and create the extraction model
        extraction_model = CocktailExtractionModel(
            cocktail_model=command.model,
            extraction_text=result_content or "",
        )

        if extraction_model.extraction_text.strip() == "":
            self.logger.warning(
                msg="Empty extraction text received after processing",
                extra={
                    "cocktail_id": command.model.id,
                },
            )
            return True

        self.logger.info(
            msg="Sending cocktail extraction model to chunking topic",
            extra={
                "messaging.kafka.bootstrap_servers": self.kafka_producer.settings.bootstrap_servers,
                "messaging.kafka.topic_name": self.app_options.results_topic_name,
                "cocktail_id": command.model.id,
            },
        )

        self.kafka_producer.send_and_wait(
            topic=self.app_options.results_topic_name,
            key=command.model.id,
            message=extraction_model.as_serializable_json(),
            headers=get_propagation_headers(),
            timeout=30.0,
        )

        self.logger.info(
            msg="Cocktail extraction succeeded",
            extra={
                "messaging.kafka.bootstrap_servers": self.kafka_producer.settings.bootstrap_servers,
                "messaging.kafka.topic_name": self.app_options.results_topic_name,
                "cocktail_id": command.model.id,
                "cocktail_ingestion_state": "extraction-succeeded",
            },
        )

        return True
