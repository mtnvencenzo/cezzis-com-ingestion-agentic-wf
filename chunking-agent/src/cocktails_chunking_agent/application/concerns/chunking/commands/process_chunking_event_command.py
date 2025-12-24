import logging

from cezzis_kafka import KafkaConsumerSettings, KafkaProducer
from cezzis_otel import get_propagation_headers
from injector import inject
from mediatr import GenericQuery, Mediator
from opentelemetry import trace

from cocktails_chunking_agent.application.concerns.chunking.models.cocktail_chunking_model import (
    CocktailChunkingModel,
)
from cocktails_chunking_agent.application.concerns.chunking.models.cocktail_extraction_model import (
    CocktailExtractionModel,
)
from cocktails_chunking_agent.domain.config.app_options import AppOptions
from cocktails_chunking_agent.infrastructure.llm.llm_content_chunker import LLMContentChunker


class ProcessChunkingEventCommand(GenericQuery[bool]):
    def __init__(self, model: CocktailExtractionModel) -> None:
        self.model = model


@Mediator.behavior
class ProcessChunkingEventCommandValidator:
    def handle(self, command: ProcessChunkingEventCommand, next) -> None:
        if not command.model or not command.model.cocktail_model or not command.model.cocktail_model.id:
            raise ValueError("Invalid cocktail model provided for chunking processing")

        if command.model.extraction_text.strip() == "":
            raise ValueError("Received empty extraction text in cocktail chunking message")

        return next()


@Mediator.handler
class ProcessChunkingEventCommandHandler:
    @inject
    def __init__(
        self,
        kafka_producer: KafkaProducer,
        app_options: AppOptions,
        kafka_consumer_options: KafkaConsumerSettings,
        llm_content_chunker: LLMContentChunker,
    ) -> None:
        self.kafka_producer = kafka_producer
        self.kafka_consiumer_settings = kafka_consumer_options
        self.app_options = app_options
        self.logger = logging.getLogger("process_chunking_event_command_handler")
        self.tracer = trace.get_tracer("chunking_agent")
        self.llm_content_chunker = llm_content_chunker

    async def handle(self, command: ProcessChunkingEventCommand) -> bool:
        assert command.model.cocktail_model is not None

        self.logger.info("Processing chunking event")
        self.logger.info(
            msg="Processing cocktail chunking message item",
            extra={
                "cocktail.id": command.model.cocktail_model.id,
            },
        )

        chunks = await self.llm_content_chunker.chunk_content(
            command.model.extraction_text,
        )

        if not chunks or len(chunks) == 0:
            self.logger.warning(
                msg="No chunks were created from cocktail extraction text, skipping sending to embedding topic",
                extra={
                    "cocktail.id": command.model.cocktail_model.id,
                },
            )
            return False

        self.logger.info(
            msg="Sending cocktail chunking model to embedding topic",
            extra={
                "messaging.kafka.bootstrap_servers": self.kafka_consiumer_settings.bootstrap_servers,
                "messaging.kafka.topic_name": self.app_options.results_topic_name,
                "cocktail.id": command.model.cocktail_model.id,
            },
        )

        chunking_model = CocktailChunkingModel(
            cocktail_model=command.model.cocktail_model,
            chunks=chunks,
        )

        self.kafka_producer.send_and_wait(
            topic=self.app_options.results_topic_name,
            key=command.model.cocktail_model.id,
            message=chunking_model.as_serializable_json(),
            headers=get_propagation_headers(),
            timeout=30.0,
        )

        return True
