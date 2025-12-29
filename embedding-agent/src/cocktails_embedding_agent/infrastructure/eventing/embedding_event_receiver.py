import json
import logging

from cezzis_kafka import IAsyncKafkaMessageProcessor, KafkaConsumerSettings
from confluent_kafka import Message
from injector import inject
from mediatr import Mediator
from opentelemetry import trace

from cocktails_embedding_agent.application.concerns.embedding.commands.process_embedding_event_command import (
    ProcessEmbeddingEventCommand,
)
from cocktails_embedding_agent.domain.base_agent_evt_receiver import BaseAgentEventReceiver
from cocktails_embedding_agent.domain.models.cocktail_chunking_model import (
    CocktailChunkingModel,
    CocktailDescriptionChunk,
)
from cocktails_embedding_agent.infrastructure.clients.cocktails_api.cocktails_models import CocktailModel


class EmbeddingEventReceiver(BaseAgentEventReceiver):
    """Concrete implementation of IAsyncKafkaMessageProcessor for processing cocktail embedding messages from Kafka.

    Attributes:
        logger (logging.Logger): Logger instance for logging events.
        tracer: OpenTelemetry tracer for tracing operations.
        mediator (Mediator): Mediator instance for sending commands/queries.

    Methods:
        message_received(msg: Message) -> None:
            Process a received Kafka message.
    """

    @inject
    def __init__(self, kafka_consumer_settings: KafkaConsumerSettings, mediator: Mediator) -> None:
        """Initialize the EmbeddingEventReceiver

        Args:
            kafka_consumer_settings (KafkaConsumerSettings): The Kafka consumer settings.
            mediator (Mediator): The Mediator instance for handling commands and queries.

        """
        super().__init__(kafka_consumer_settings=kafka_consumer_settings)

        self.logger: logging.Logger = logging.getLogger("embedding_agent")
        self.tracer = trace.get_tracer("embedding_agent")
        self.mediator = mediator

    @staticmethod
    def CreateNew(kafka_settings: KafkaConsumerSettings) -> IAsyncKafkaMessageProcessor:
        """Factory method to create a new instance of EmbeddingEventReceiver.

        Args:
            kafka_settings (KafkaConsumerSettings): The Kafka consumer settings.

        Returns:
            IAsyncKafkaMessageProcessor: A new instance of EmbeddingEventReceiver.
        """
        from cocktails_embedding_agent.app_module import injector

        return injector.get(EmbeddingEventReceiver)

    async def message_received(self, msg: Message) -> None:
        with super().create_kafka_consumer_read_span(self.tracer, "cocktail-embedding-message-processing", msg):
            try:
                value = msg.value()
                if value is not None:
                    self.logger.info(
                        msg="Received cocktail embedding message",
                        extra={**super().get_kafka_attributes(msg)},
                    )

                    data = json.loads(value.decode("utf-8"))
                    chunking_model = CocktailChunkingModel(
                        cocktail_model=CocktailModel.model_validate(data["cocktail_model"]),
                        chunks=[CocktailDescriptionChunk.from_dict(chunk) for chunk in data["chunks"]],
                    )

                    if not chunking_model.chunks or not chunking_model.cocktail_model:
                        self._logger.warning(
                            msg="Received empty cocktail chunking model",
                            extra={
                                **super().get_kafka_attributes(msg),
                                **{
                                    "cocktail_id": chunking_model.cocktail_model.id
                                    if chunking_model.cocktail_model
                                    else "unknown",
                                    "cocktail_ingestion_state": "embedding-failed",
                                },
                            },
                        )
                        return

                    # ----------------------------------------
                    # Process the individual cocktail message
                    # ----------------------------------------
                    try:
                        with super().create_processing_read_span(
                            self.tracer,
                            "cocktail-embedding-processing",
                            span_attributes={"cocktail_id": chunking_model.cocktail_model.id},
                        ):
                            await self._process_message(chunking_model=chunking_model)
                    except Exception as e:
                        self._logger.exception(
                            msg="Error processing cocktail embedding message item",
                            extra={
                                **super().get_kafka_attributes(msg),
                                **{
                                    "cocktail_id": chunking_model.cocktail_model.id
                                    if chunking_model.cocktail_model
                                    else "unknown",
                                    "cocktail_ingestion_state": "embedding-failed",
                                },
                                "error": str(e),
                            },
                        )
                else:
                    self._logger.warning(
                        msg="Received cocktail embedding message with no value",
                        extra={
                            **super().get_kafka_attributes(msg),
                            **{
                                "cocktail_ingestion_state": "embedding-failed",
                            },
                        },
                    )
            except Exception as e:
                self._logger.exception(
                    msg="Error processing cocktail embedding message",
                    extra={
                        **super().get_kafka_attributes(msg),
                        "error": str(e),
                        "cocktail_ingestion_state": "embedding-failed",
                    },
                )

    async def _process_message(self, chunking_model: CocktailChunkingModel) -> None:
        await self.mediator.send_async(ProcessEmbeddingEventCommand(model=chunking_model))
