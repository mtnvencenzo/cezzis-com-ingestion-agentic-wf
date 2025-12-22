import json
import logging

from cezzis_kafka import IAsyncKafkaMessageProcessor, KafkaConsumerSettings
from confluent_kafka import Message
from injector import inject
from langchain.agents import create_agent
from mediatr import Mediator
from opentelemetry import trace
from pydantic import ValidationError

from cocktails_extraction_agent.application.concerns.extraction.commands.process_extration_event_command import (
    ProcessExtractionEventCommand,
)
from cocktails_extraction_agent.application.tools.emoji_remover import remove_emojis
from cocktails_extraction_agent.application.tools.html_tag_remover import remove_html_tags
from cocktails_extraction_agent.application.tools.markdown_remover import remove_markdown
from cocktails_extraction_agent.domain.base_agent_evt_receiver import BaseAgentEventReceiver
from cocktails_extraction_agent.domain.config.ext_agent_options import ExtractionAgentOptions
from cocktails_extraction_agent.domain.config.kafka_options import KafkaOptions
from cocktails_extraction_agent.domain.config.llm_model_options import LLMModelOptions
from cocktails_extraction_agent.domain.config.llm_options import get_llm_options
from cocktails_extraction_agent.infrastructure.clients.cocktails_api.cocktail_api import CocktailModel
from cocktails_extraction_agent.infrastructure.llm.ollama_utils import get_ollama_chat_model


class ExtractionEventReceiver(BaseAgentEventReceiver):
    """Concrete implementation of IAsyncKafkaMessageProcessor for processing cocktail extraction messages from Kafka.

    Attributes:
        _logger (logging.Logger): Logger instance for logging messages.
        _kafka_settings (KafkaConsumerSettings): Kafka consumer settings.
        _tracer (trace.Tracer): OpenTelemetry tracer for creating spans.

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
        ext_agent_options: ExtractionAgentOptions,
        kafka_options: KafkaOptions,
        mediator: Mediator,
    ) -> None:
        """Initialize the ExtractionEventReceiver
        Args:
            kafka_consumer_settings (KafkaConsumerSettings): The Kafka consumer settings.
            kafka_producer_settings (KafkaProducerSettings): The Kafka producer settings.

        Returns:
            None
        """
        super().__init__(kafka_consumer_settings=kafka_consumer_settings)

        self.logger: logging.Logger = logging.getLogger("extraction_agent")
        self.tracer = trace.get_tracer("extraction_agent")
        self.ext_agent_options = ext_agent_options
        self.mediator = mediator

        self.llm = get_ollama_chat_model(
            name=f"convert_markdown [{self.ext_agent_options.model}]",
            llm_options=get_llm_options(),
            llm_model_options=LLMModelOptions(
                model=self.ext_agent_options.model,
                temperature=0.0,
                num_predict=-1,
                verbose=True,
                timeout_seconds=30,
                reasoning=False,
            ),
        )

        self.agent = create_agent(model=self.llm, tools=[remove_markdown, remove_html_tags, remove_emojis])

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
        with super().create_kafka_consumer_read_span(self.tracer, "cocktail-extraction-message-processing", msg):
            try:
                value = msg.value()
                if value is not None:
                    decoded_value = value.decode("utf-8")
                    json_data = json.loads(decoded_value)
                    json_array = json_data["data"] if "data" in json_data else json_data

                    span = trace.get_current_span()
                    span.set_attribute("cocktail_item_count", len(json_array))

                    self._logger.info(
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
                            self._logger.exception(
                                msg="Failed to parse cocktail extraction message item",
                                extra={
                                    **super().get_kafka_attributes(msg),
                                    "error": str(ve),
                                },
                            )
                            continue

                        cocktail_id = cocktail_model.id
                        if cocktail_id == "unknown":
                            self._logger.warning(
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
                            self._logger.exception(
                                msg="Error processing cocktail extraction message item",
                                extra={
                                    **super().get_kafka_attributes(msg),
                                    "error": str(e),
                                },
                            )
                            continue
                else:
                    self._logger.warning(
                        msg="Received cocktail extraction message with no value",
                        extra={**super().get_kafka_attributes(msg)},
                    )
            except Exception:
                self._logger.exception(
                    msg="Error processing cocktail extraction message",
                    extra={**super().get_kafka_attributes(msg)},
                )

    async def _process_message(self, model: CocktailModel) -> None:
        await self.mediator.send_async(ProcessExtractionEventCommand(model=model))
