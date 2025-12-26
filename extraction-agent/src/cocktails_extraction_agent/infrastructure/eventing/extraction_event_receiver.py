import json
import logging

from cezzis_kafka import IAsyncKafkaMessageProcessor, KafkaConsumerSettings
from confluent_kafka import Message
from injector import inject
from mediatr import Mediator
from opentelemetry import trace
from pydantic import ValidationError

from cocktails_extraction_agent.application.concerns.extraction.commands.process_extraction_event_command import (
    ProcessExtractionEventCommand,
)
from cocktails_extraction_agent.domain.base_agent_evt_receiver import BaseAgentEventReceiver
from cocktails_extraction_agent.infrastructure.clients.cocktails_api.cocktail_api import CocktailModel


class ExtractionEventReceiver(BaseAgentEventReceiver):
    """Concrete implementation of IAsyncKafkaMessageProcessor for processing cocktail extraction messages from Kafka.

    Attributes:
        logger (logging.Logger): Logger instance for logging messages.
        kafka_consumer_settings (KafkaConsumerSettings): Kafka consumer settings.
        mediator (Mediator): Mediator instance for sending commands.

    Methods:
        message_received(msg: Message) -> None:
            Process a received Kafka message.
        CreateNew(kafka_settings: KafkaConsumerSettings) -> IAsyncKafkaMessageProcessor:
            Factory method to create a new instance of ExtractionEventReceiver.

    """

    @inject
    def __init__(
        self,
        kafka_consumer_settings: KafkaConsumerSettings,
        mediator: Mediator,
    ) -> None:
        """Initialize the ExtractionEventReceiver
        Args:
            kafka_consumer_settings (KafkaConsumerSettings): The Kafka consumer settings.
            mediator (Mediator): The Mediator instance for sending commands.

        """
        super().__init__(kafka_consumer_settings=kafka_consumer_settings)

        self.logger: logging.Logger = logging.getLogger("extraction_agent")
        self.tracer = trace.get_tracer("extraction_agent")
        self.mediator = mediator

    @staticmethod
    def CreateNew(kafka_settings: KafkaConsumerSettings) -> IAsyncKafkaMessageProcessor:
        """Factory method to create a new instance of ExtractionEventReceiver.

        Args:
            kafka_settings (KafkaConsumerSettings): The Kafka consumer settings.

        Returns:
            IAsyncKafkaMessageProcessor: A new instance of ExtractionEventReceiver.
        """
        from cocktails_extraction_agent.app_module import injector

        return injector.get(ExtractionEventReceiver)

    async def message_received(self, msg: Message) -> None:
        """Process a received Kafka message.

        Args:
            msg (Message): The received Kafka message.

        """

        with super().create_kafka_consumer_read_span(self.tracer, "cocktail-extraction-message-processing", msg):
            try:
                value = msg.value()
                if value is not None:
                    decoded_value = value.decode("utf-8")
                    json_data = json.loads(decoded_value)
                    json_array = json_data["data"] if "data" in json_data else json_data

                    span = trace.get_current_span()
                    span.set_attribute("cocktail_item_count", len(json_array))

                    self.logger.info(
                        msg="Received cocktail extraction message",
                        extra={
                            **super().get_kafka_attributes(msg),
                            "cocktail_item_count": len(json_array),
                        },
                    )

                    for item in json_array:
                        try:
                            cocktail_model = CocktailModel(**item)
                        except ValidationError as ve:
                            self.logger.exception(
                                msg="Failed to parse cocktail extraction message item",
                                extra={
                                    **super().get_kafka_attributes(msg),
                                    "error": str(ve),
                                },
                            )
                            continue

                        cocktail_id = cocktail_model.id
                        if cocktail_id == "unknown":
                            self.logger.warning(
                                msg="Cocktail item missing 'Id' field, skipping",
                                extra={**super().get_kafka_attributes(msg)},
                            )
                            continue

                        # ----------------------------------------
                        # Process the individual cocktail message
                        # ----------------------------------------
                        try:
                            with super().create_processing_read_span(
                                self.tracer,
                                "cocktail-extraction-item-processing",
                                span_attributes={"cocktail_id": cocktail_id},
                            ):
                                await self._process_message(model=cocktail_model)
                        except Exception as e:
                            self.logger.exception(
                                msg="Error processing cocktail extraction message item",
                                extra={
                                    **super().get_kafka_attributes(msg),
                                    "error": str(e),
                                    "cocktail_id": cocktail_id,
                                    "cocktail_ingestion_state": "extraction-failed",
                                },
                            )
                            continue
                else:
                    self.logger.warning(
                        msg="Received cocktail extraction message with no value",
                        extra={
                            **super().get_kafka_attributes(msg),
                            **{
                                "cocktail_ingestion_state": "extraction-failed",
                            },
                        },
                    )
            except Exception as e:
                self.logger.exception(
                    msg="Error processing cocktail extraction message",
                    extra={
                        **super().get_kafka_attributes(msg),
                        "error": str(e),
                        "cocktail_ingestion_state": "extraction-failed",
                    },
                )

    async def _process_message(self, model: CocktailModel) -> None:
        """Process an individual cocktail extraction message.

        Args:
            model (CocktailModel): The cocktail model to process.

        """

        await self.mediator.send_async(ProcessExtractionEventCommand(model=model))
