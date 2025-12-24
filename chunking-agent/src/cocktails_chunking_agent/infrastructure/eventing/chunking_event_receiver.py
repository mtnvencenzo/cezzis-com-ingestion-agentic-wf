import json
import logging

from cezzis_kafka import IAsyncKafkaMessageProcessor, KafkaConsumerSettings
from confluent_kafka import Message
from injector import inject
from mediatr import Mediator
from opentelemetry import trace

from cocktails_chunking_agent.application.concerns.chunking.commands.process_chunking_event_command import (
    ProcessChunkingEventCommand,
)
from cocktails_chunking_agent.domain.models.cocktail_extraction_model import (
    CocktailExtractionModel,
)
from cocktails_chunking_agent.domain.base_agent_evt_receiver import BaseAgentEventReceiver
from cocktails_chunking_agent.infrastructure.clients.cocktails_api.cocktail_api import CocktailModel


class ChunkingEventReceiver(BaseAgentEventReceiver):
    """Concrete implementation of IAsyncKafkaMessageProcessor for processing cocktail chunking messages from Kafka.

    Attributes:
        _logger (logging.Logger): Logger instance for logging messages.
        _tracer (trace.Tracer): OpenTelemetry tracer for creating spans.

    Methods:
        kafka_settings() -> KafkaConsumerSettings:
            Get the Kafka consumer settings.

        message_received(msg: Message) -> None:
            Process a received Kafka message.
    """

    @inject
    def __init__(self, kafka_consumer_settings: KafkaConsumerSettings, mediator: Mediator) -> None:
        """Initialize the ChunkingEventReceiver
        Args:
            kafka_consumer_settings (KafkaConsumerSettings): The Kafka consumer settings.
            mediator (Mediator): The Mediator instance for sending commands/queries.

        """
        super().__init__(kafka_consumer_settings=kafka_consumer_settings)

        self.logger: logging.Logger = logging.getLogger("chunking_agent")
        self.tracer = trace.get_tracer("chunking_agent")
        self.mediator = mediator

    @staticmethod
    def CreateNew(kafka_settings: KafkaConsumerSettings) -> IAsyncKafkaMessageProcessor:
        """Factory method to create a new instance of ChunkingEventReceiver.

        Args:
            kafka_settings (KafkaConsumerSettings): The Kafka consumer settings.

        Returns:
            IAsyncKafkaMessageProcessor: A new instance of ChunkingEventReceiver.
        """
        from cocktails_chunking_agent.app_module import injector

        return injector.get(ChunkingEventReceiver)

    async def message_received(self, msg: Message) -> None:
        with super().create_kafka_consumer_read_span(self.tracer, "chunking-agent-message-processing", msg):
            try:
                value = msg.value()
                if value is not None:
                    self._logger.info(
                        msg="Received cocktail chunking agent message",
                        extra={**super().get_kafka_attributes(msg)},
                    )

                    data = json.loads(value.decode("utf-8"))
                    extraction_model = CocktailExtractionModel(
                        cocktail_model=CocktailModel.model_validate(data["cocktail_model"]),
                        extraction_text=data["extraction_text"],
                    )

                    if not extraction_model.extraction_text or not extraction_model.cocktail_model:
                        self._logger.warning(
                            msg="Received empty cocktail extraction text",
                            extra={
                                **super().get_kafka_attributes(msg),
                                **{
                                    "cocktail.id": extraction_model.cocktail_model.id
                                    if extraction_model.cocktail_model
                                    else "unknown"
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
                            "cocktail-chunking-text-processing",
                            span_attributes={
                                "cocktail_id": extraction_model.cocktail_model.id
                                if extraction_model.cocktail_model
                                else "unknown"
                            },
                        ):
                            await self._process_message(extraction_model=extraction_model)
                    except Exception as e:
                        self._logger.exception(
                            msg="Error processing cocktail chunking message item",
                            extra={
                                **super().get_kafka_attributes(msg),
                                **{
                                    "cocktail.id": extraction_model.cocktail_model.id
                                    if extraction_model.cocktail_model
                                    else "unknown"
                                },
                                "error": str(e),
                            },
                        )

                else:
                    self._logger.warning(
                        msg="Received cocktail chunking message with no value",
                        extra={**super().get_kafka_attributes(msg)},
                    )
            except Exception as e:
                self._logger.exception(
                    msg="Error processing cocktail chunking message",
                    extra={
                        **super().get_kafka_attributes(msg),
                        "error": str(e),
                    },
                )

    async def _process_message(self, extraction_model: CocktailExtractionModel) -> None:
        await self.mediator.send_async(ProcessChunkingEventCommand(model=extraction_model))
