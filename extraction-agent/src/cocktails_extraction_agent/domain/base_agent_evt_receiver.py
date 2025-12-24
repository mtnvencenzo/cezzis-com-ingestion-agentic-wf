import logging
from typing import ContextManager, Mapping, Optional

from cezzis_kafka import IAsyncKafkaMessageProcessor, KafkaConsumerSettings
from confluent_kafka import Consumer, Message
from opentelemetry import trace
from opentelemetry.propagate import extract
from opentelemetry.trace import Span


class BaseAgentEventReceiver(IAsyncKafkaMessageProcessor):
    """Base class for agent Kafka message receivers."""

    def __init__(self, kafka_consumer_settings: KafkaConsumerSettings) -> None:
        super().__init__()

        self.logger: logging.Logger = logging.getLogger("base_agent_event_receiver")
        self.kafka_consumer_settings = kafka_consumer_settings

    def kafka_settings(self) -> KafkaConsumerSettings:
        """Get the Kafka consumer settings.

        Args:    None

        Returns:
            KafkaConsumerSettings: The Kafka consumer settings.
        """
        return self.kafka_consumer_settings

    async def consumer_creating(self) -> None:
        pass

    async def consumer_created(self, consumer: Consumer | None) -> None:
        pass

    async def consumer_subscribed(self) -> None:
        pass

    async def consumer_stopping(self) -> None:
        pass

    async def message_received(self, msg: Message) -> None:
        pass

    async def message_error_received(self, msg: Message) -> None:
        pass

    async def message_partition_reached(self, msg: Message) -> None:
        pass

    def create_kafka_consumer_read_span(
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
                        carrier[key] = value.decode("utf-8")
                    except UnicodeDecodeError:
                        self.logger.warning(f"Failed to decode header '{key}' as UTF-8, skipping")

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

        return tracer.start_as_current_span(
            span_name,
            context=parent_context,
            attributes=span_attributes,
        )

    def create_processing_read_span(
        self,
        tracer: trace.Tracer,
        span_name: str,
        span_attributes: Optional[Mapping[str, str | int | float | bool]] = None,
    ) -> ContextManager[Span]:
        """Create a child span for processing each item in the Kafka message.

        Args:
            tracer (trace.Tracer): The OpenTelemetry tracer.
            span_name (str): The name of the span.
            span_attributes (Optional[Mapping[str, str | int | float]]): Attributes to add to the span.

        Returns:
            ContextManager[Span]: A context manager that yields the created child span.
        """

        # Create a child span of the current active span (no context extraction needed)
        return tracer.start_as_current_span(
            span_name,
            attributes=span_attributes,
        )

    def get_kafka_attributes(self, msg: Message) -> Mapping[str, object]:
        """Get Kafka message attributes for logging.

        Args:
            msg (Message): The Kafka message object.
        Returns:
            Mapping[str, object]: A dictionary of Kafka message attributes.
        """
        return {
            "messaging.kafka.bootstrap_servers": self.kafka_consumer_settings.bootstrap_servers,
            "messaging.kafka.consumer_group": self.kafka_consumer_settings.consumer_group,
            "messaging.kafka.topic_name": self.kafka_consumer_settings.topic_name,
            "messaging.kafka.partition": msg.partition(),
        }
