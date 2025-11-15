import json
import logging
from typing import ContextManager

from cezzis_kafka import IAsyncKafkaMessageProcessor, KafkaConsumerSettings
from confluent_kafka import Consumer, Message
from opentelemetry import trace
from opentelemetry.propagate import extract
from opentelemetry.trace import Span

from data_ingestion_agentic_workflow.agents.embedding_agent.emb_agent_app_options import get_emb_agent_options
from data_ingestion_agentic_workflow.models.cocktail_models import CocktailModel


class CocktailsEmbeddingProcessor(IAsyncKafkaMessageProcessor):
    """Concrete implementation of IAsyncKafkaMessageProcessor for processing cocktail embedding messages from Kafka.

    Attributes:
        _logger (logging.Logger): Logger instance for logging messages.
        _kafka_settings (KafkaConsumerSettings): Kafka consumer settings.
        _tracer (trace.Tracer): OpenTelemetry tracer for creating spans.

    Methods:
        kafka_settings() -> KafkaConsumerSettings:
            Get the Kafka consumer settings.

        consumer_creating() -> None:
            Hook called when the consumer is being created.

        consumer_created(consumer: Consumer | None) -> None:
            Hook called after the consumer has been created.

        consumer_subscribed() -> None:
            Hook called after the consumer has subscribed to topics.

        consumer_stopping() -> None:
            Hook called when the consumer is stopping.

        message_received(msg: Message) -> None:
            Process a received Kafka message.

        message_error_received(msg: Message) -> None:
            Hook called when an error message is received.

        message_partition_reached(msg: Message) -> None:
            Hook called when a partition end is reached.
    """

    def __init__(self, kafka_consumer_settings: KafkaConsumerSettings) -> None:
        """Initialize the CocktailsEmbeddingProcessor
        Args:
            kafka_consumer_settings (KafkaConsumerSettings): The Kafka consumer settings.

        Returns:
            None
        """

        self._logger: logging.Logger = logging.getLogger("emb_agent_evt_processor")
        self._tracer = trace.get_tracer("emb_agent_evt_processor")
        self._kafka_consumer_settings = kafka_consumer_settings
        self._options = get_emb_agent_options()

    @staticmethod
    def CreateNew(kafka_settings: KafkaConsumerSettings) -> IAsyncKafkaMessageProcessor:
        """Factory method to create a new instance of CocktailsEmbeddingProcessor.

        Args:
            kafka_settings (KafkaConsumerSettings): The Kafka consumer settings.

        Returns:
            IAsyncKafkaMessageProcessor: A new instance of CocktailsEmbeddingProcessor.
        """
        return CocktailsEmbeddingProcessor(kafka_consumer_settings=kafka_settings)

    def kafka_settings(self) -> KafkaConsumerSettings:
        """Get the Kafka consumer settings.

        Args:
            None

        Returns:
            KafkaConsumerSettings: The Kafka consumer settings.
        """
        return self._kafka_consumer_settings

    async def consumer_creating(self) -> None:
        pass

    async def consumer_created(self, consumer: Consumer | None) -> None:
        pass

    async def consumer_subscribed(self) -> None:
        pass

    async def consumer_stopping(self) -> None:
        pass

    async def message_received(self, msg: Message) -> None:
        # Create a span for processing this Kafka message, linked to the API trace
        with self._create_kafka_consumer_read_span(self._tracer, "cocktail-embedding-message-processing", msg):
            try:
                value = msg.value()
                if value is not None:
                    decoded_value = value.decode("utf-8")
                    json_data = json.loads(decoded_value)
                    self._logger.info(
                        "Received cocktail embedding message",
                        extra={
                            "messaging.kafka.consumer_id": self._kafka_consumer_settings.consumer_id,
                            "messaging.kafka.bootstrap_servers": self._kafka_consumer_settings.bootstrap_servers,
                            "messaging.kafka.consumer_group": self._kafka_consumer_settings.consumer_group,
                            "messaging.kafka.topic_name": self._kafka_consumer_settings.topic_name,
                            "messaging.kafka.partition": msg.partition(),
                        },
                    )

                    cocktail_model = CocktailModel(**json_data)
                    cocktail_id = cocktail_model.id
                    if cocktail_id == "unknown":
                        self._logger.warning(
                            "Cocktail item missing 'Id' field, skipping",
                            extra={
                                "messaging.kafka.consumer_id": self._kafka_consumer_settings.consumer_id,
                                "messaging.kafka.bootstrap_servers": self._kafka_consumer_settings.bootstrap_servers,
                                "messaging.kafka.consumer_group": self._kafka_consumer_settings.consumer_group,
                                "messaging.kafka.topic_name": self._kafka_consumer_settings.topic_name,
                                "messaging.kafka.partition": msg.partition(),
                            },
                        )
                        return

                    # ----------------------------------------
                    # Process the individual cocktail message
                    # ----------------------------------------
                    self._process_message(model=cocktail_model)
                else:
                    self._logger.warning(
                        "Received cocktail embedding message with no value",
                        extra={
                            "messaging.kafka.consumer_id": self._kafka_consumer_settings.consumer_id,
                            "messaging.kafka.bootstrap_servers": self._kafka_consumer_settings.bootstrap_servers,
                            "messaging.kafka.consumer_group": self._kafka_consumer_settings.consumer_group,
                            "messaging.kafka.topic_name": self._kafka_consumer_settings.topic_name,
                            "messaging.kafka.partition": msg.partition(),
                        },
                    )
            except Exception as e:
                self._logger.error(
                    "Error processing cocktail embedding message",
                    extra={
                        "messaging.kafka.consumer_id": self._kafka_consumer_settings.consumer_id,
                        "messaging.kafka.bootstrap_servers": self._kafka_consumer_settings.bootstrap_servers,
                        "messaging.kafka.consumer_group": self._kafka_consumer_settings.consumer_group,
                        "messaging.kafka.topic_name": self._kafka_consumer_settings.topic_name,
                        "messaging.kafka.partition": msg.partition(),
                        "error": str(e),
                    },
                )

    async def message_error_received(self, msg: Message) -> None:
        pass

    async def message_partition_reached(self, msg: Message) -> None:
        pass

    def _create_kafka_consumer_read_span(
        self, tracer: trace.Tracer, span_name: str, msg: Message
    ) -> ContextManager[Span]:
        """Create a child span for Kafka message processing.

        Args:
            tracer (trace.Tracer): The OpenTelemetry tracer.
            span_name (str): The name of the span.
            msg (Message): The Kafka message object.

        Returns:
            ContextManager[Span]: A context manager that yields the created child span.
        """
        # Extract trace context from Kafka message headers for distributed tracing
        carrier: dict[str, str] = {}
        headers = msg.headers()

        if headers is not None:
            for key, value in headers:
                if isinstance(value, bytes):
                    try:
                        decoded_value = value.decode("utf-8")
                        carrier[key] = decoded_value
                    except UnicodeDecodeError:
                        self._logger.warning(f"Failed to decode header '{key}' as UTF-8, skipping")

        # Extract parent context and create a span as a child of the API trace
        parent_context = extract(carrier)

        # Add Kafka-specific attributes to the span using OpenTelemetry semantic conventions
        span_attributes: dict[str, str | int] = {
            "messaging.system": "kafka",
            "messaging.destination.name": msg.topic() or "unknown",  # Updated to semantic convention
            "messaging.operation": "process",
        }

        # Add optional attributes if available
        partition = msg.partition()
        if partition is not None:
            span_attributes["messaging.kafka.partition"] = partition

        offset = msg.offset()
        if offset is not None:
            span_attributes["messaging.kafka.offset"] = offset

        try:
            span_context_manager = tracer.start_as_current_span(
                span_name,
                context=parent_context,
                attributes=span_attributes,
            )
            return span_context_manager
        except Exception as e:
            self._logger.error(f"Failed to create span: {e}")
            # Return a fallback span if creation fails
            return tracer.start_as_current_span(
                f"fallback-{span_name}",
                context=None,
                attributes={"error": "span_creation_failed"},
            )

    def _process_message(self, model: CocktailModel) -> None:
        self._logger.info(
            "Processing cocktail embedding message item",
            extra={
                "cocktail.id": model.id,
            },
        )

        self._logger.info(
            "Sending cocktail embedding result to vector database",
            extra={
                "messaging.kafka.bootstrap_servers": self._kafka_consumer_settings.bootstrap_servers,
                "messaging.kafka.topic_name": self._options.embedding_topic_name,
                "cocktail.id": model.id,
            },
        )
