import json
import logging

from cezzis_kafka import IAsyncKafkaMessageProcessor, KafkaConsumerSettings, KafkaProducer, KafkaProducerSettings
from cezzis_otel import get_propagation_headers
from confluent_kafka import Message
from opentelemetry import trace

from cocktails_chunking_agent.application.concerns.chunking.models.cocktail_chunking_model import CocktailChunkingModel
from cocktails_chunking_agent.application.concerns.chunking.models.cocktail_extraction_model import (
    CocktailExtractionModel,
)
from cocktails_chunking_agent.domain.base_agent_evt_receiver import BaseAgentEventReceiver
from cocktails_chunking_agent.domain.config.chunking_agent_options import get_chunking_agent_options
from cocktails_chunking_agent.domain.config.kafka_options import KafkaOptions, get_kafka_options
from cocktails_chunking_agent.domain.config.llm_model_options import LLMModelOptions
from cocktails_chunking_agent.domain.config.llm_options import get_llm_options
from cocktails_chunking_agent.infrastructure.clients.cocktails_api.cocktail_api import CocktailModel
from cocktails_chunking_agent.infrastructure.llm.llm_content_chunker import LLMContentChunker


class ChunkingAgentEventReceiver(BaseAgentEventReceiver):
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

    def __init__(self, kafka_consumer_settings: KafkaConsumerSettings) -> None:
        """Initialize the ChunkingAgentEventReceiver
        Args:
            kafka_consumer_settings (KafkaConsumerSettings): The Kafka consumer settings.
            kafka_producer_settings (KafkaProducerSettings): The Kafka producer settings.

        Returns:
            None
        """
        super().__init__(kafka_consumer_settings=kafka_consumer_settings)

        self._logger: logging.Logger = logging.getLogger("chunking_agent")
        self._tracer = trace.get_tracer("chunking_agent")
        self._options = get_chunking_agent_options()

        kafka_options: KafkaOptions = get_kafka_options()

        self.producer = KafkaProducer(
            settings=KafkaProducerSettings(
                bootstrap_servers=kafka_options.bootstrap_servers,
                on_delivery=lambda err, msg: (
                    self._logger.error(f"Message delivery failed: {err}")
                    if err
                    else self._logger.info(
                        f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}"
                    )
                ),
            )
        )

        self._content_chunker = LLMContentChunker(
            llm_options=get_llm_options(),
            model_options=LLMModelOptions(
                model=self._options.llm_model,
                temperature=0.0,
                num_predict=-1,
                verbose=True,
                timeout_seconds=180,
                reasoning=False,
            ),
        )

    @staticmethod
    def CreateNew(kafka_settings: KafkaConsumerSettings) -> IAsyncKafkaMessageProcessor:
        """Factory method to create a new instance of ChunkingAgentEventReceiver.

        Args:
            kafka_settings (KafkaConsumerSettings): The Kafka consumer settings.

        Returns:
            IAsyncKafkaMessageProcessor: A new instance of ChunkingAgentEventReceiver.
        """
        return ChunkingAgentEventReceiver(kafka_consumer_settings=kafka_settings)

    async def message_received(self, msg: Message) -> None:
        with super().create_kafka_consumer_read_span(self._tracer, "chunking-agent-message-processing", msg):
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
        with super().create_processing_read_span(
            self._tracer,
            "cocktail-chunking-text-processing",
            span_attributes={
                "cocktail_id": extraction_model.cocktail_model.id if extraction_model.cocktail_model else "unknown"
            },
        ):
            if extraction_model.cocktail_model is None:
                self._logger.warning(msg="Received null cocktail model in cocktail chunking message")
                return

            self._logger.info(
                msg="Processing cocktail chunking message item",
                extra={
                    "cocktail.id": extraction_model.cocktail_model.id,
                },
            )

            if extraction_model.extraction_text.strip() == "":
                self._logger.warning(
                    msg="Received empty extraction text in cocktail chunking message",
                    extra={
                        "cocktail.id": extraction_model.cocktail_model.id,
                    },
                )
                return

            chunks = await self._content_chunker.chunk_content(
                extraction_model.extraction_text,
            )

            if not chunks or len(chunks) == 0:
                self._logger.warning(
                    msg="No chunks were created from cocktail extraction text, skipping sending to embedding topic",
                    extra={
                        "cocktail.id": extraction_model.cocktail_model.id,
                    },
                )
                return

            self._logger.info(
                msg="Sending cocktail chunking model to embedding topic",
                extra={
                    "messaging.kafka.bootstrap_servers": self._kafka_consumer_settings.bootstrap_servers,
                    "messaging.kafka.topic_name": self._options.results_topic_name,
                    "cocktail.id": extraction_model.cocktail_model.id,
                },
            )

            chunking_model = CocktailChunkingModel(
                cocktail_model=extraction_model.cocktail_model,
                chunks=chunks,
            )

            self.producer.send_and_wait(
                topic=self._options.results_topic_name,
                key=extraction_model.cocktail_model.id,
                message=chunking_model.as_serializable_json(),
                headers=get_propagation_headers(),
                timeout=30.0,
            )
