import json
import logging
from typing import cast

from cezzis_kafka import IAsyncKafkaMessageProcessor, KafkaConsumerSettings, KafkaProducer, KafkaProducerSettings
from cezzis_otel import get_propagation_headers
from confluent_kafka import Message
from langchain.agents import create_agent
from langchain_core.messages import BaseMessage
from opentelemetry import trace
from pydantic import ValidationError

from data_ingestion_agentic_workflow.agents.base_agent_evt_receiver import BaseAgentEventReceiver
from data_ingestion_agentic_workflow.agents.extraction_agent.ext_agent_options import get_ext_agent_options
from data_ingestion_agentic_workflow.infra.kafka_options import KafkaOptions, get_kafka_options
from data_ingestion_agentic_workflow.llm.setup.llm_model_options import LLMModelOptions
from data_ingestion_agentic_workflow.llm.setup.llm_options import get_llm_options
from data_ingestion_agentic_workflow.llm.setup.ollama_utils import get_ollama_chat_model
from data_ingestion_agentic_workflow.models.cocktail_extraction_model import CocktailExtractionModel
from data_ingestion_agentic_workflow.models.cocktail_models import CocktailModel
from data_ingestion_agentic_workflow.prompts import extraction_sys_prompt, extraction_user_prompt
from data_ingestion_agentic_workflow.tools.emoji_remover import remove_emojis
from data_ingestion_agentic_workflow.tools.html_tag_remover import remove_html_tags
from data_ingestion_agentic_workflow.tools.markdown_remover import remove_markdown


class CocktailsExtractionEventReceiver(BaseAgentEventReceiver):
    """Concrete implementation of IAsyncKafkaMessageProcessor for processing cocktail extraction messages from Kafka.

    Attributes:
        _logger (logging.Logger): Logger instance for logging messages.
        _kafka_settings (KafkaConsumerSettings): Kafka consumer settings.
        _tracer (trace.Tracer): OpenTelemetry tracer for creating spans.

    Methods:
        message_received(msg: Message) -> None:
            Process a received Kafka message.
        CreateNew(kafka_settings: KafkaConsumerSettings) -> IAsyncKafkaMessageProcessor:
            Factory method to create a new instance of CocktailsExtractionEventReceiver.

    """

    def __init__(self, kafka_consumer_settings: KafkaConsumerSettings) -> None:
        """Initialize the CocktailsExtractionEventReceiver
        Args:
            kafka_consumer_settings (KafkaConsumerSettings): The Kafka consumer settings.
            kafka_producer_settings (KafkaProducerSettings): The Kafka producer settings.

        Returns:
            None
        """
        super().__init__(kafka_consumer_settings=kafka_consumer_settings)

        self._logger: logging.Logger = logging.getLogger("extraction_agent")
        self._tracer = trace.get_tracer("extraction_agent")
        self._options = get_ext_agent_options()

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

        self.llm = get_ollama_chat_model(
            name=f"convert_markdown [{self._options.model}]",
            llm_options=get_llm_options(),
            llm_model_options=LLMModelOptions(
                model=self._options.model,
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
        """Factory method to create a new instance of CocktailsExtractionEventReceiver.

        Args:
            kafka_settings (KafkaConsumerSettings): The Kafka consumer settings.

        Returns:
            IAsyncKafkaMessageProcessor: A new instance of CocktailsExtractionEventReceiver.
        """
        return CocktailsExtractionEventReceiver(kafka_consumer_settings=kafka_settings)

    async def message_received(self, msg: Message) -> None:
        with super().create_kafka_consumer_read_span(self._tracer, "cocktail-extraction-message-processing", msg):
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
        with super().create_processing_read_span(
            self._tracer, "cocktail-extraction-item-processing", span_attributes={"cocktail_id": model.id}
        ):
            self._logger.info(
                msg="Processing cocktail extraction message item",
                extra={
                    "cocktail.id": model.id,
                },
            )

            from data_ingestion_agentic_workflow.tools import remove_emojis, remove_html_tags, remove_markdown
            result_content = await remove_markdown.ainvoke(model.content or "")
            result_content = await remove_html_tags.ainvoke(result_content or "")
            result_content = await remove_emojis.ainvoke(result_content or "")

            # --------------------------------------------------
            # Uncomment to use lang chain tools
            # --------------------------------------------------
            # agent_result = await self.agent.ainvoke(
            #     {
            #         "messages": [
            #             {"role": "system", "content": extraction_sys_prompt},
            #             {"role": "user", "content": extraction_user_prompt.format(input_text=model.content or "")},
            #         ]
            #     }
            # )

            # result_list = cast(list[BaseMessage], agent_result["messages"])
            # result_content = result_list[-1].content if result_list else ""

            # if isinstance(result_content, list):
            #     result_content = "\n".join(s if isinstance(s, str) else json.dumps(s) for s in result_content)
            # elif not isinstance(result_content, str):
            #     result_content = str(result_content)

            extraction_model = CocktailExtractionModel(
                cocktail_model=model,
                extraction_text=result_content,
            )

            if extraction_model.extraction_text.strip() == "":
                self._logger.warning(
                    msg="Empty extraction text received after processing",
                    extra={
                        "cocktail.id": model.id,
                    },
                )
                return

            self._logger.info(
                msg="Sending cocktail extraction model to chunking topic",
                extra={
                    "messaging.kafka.bootstrap_servers": self._kafka_consumer_settings.bootstrap_servers,
                    "messaging.kafka.topic_name": self._options.results_topic_name,
                    "cocktail.id": model.id,
                },
            )

            self.producer.send_and_wait(
                topic=self._options.results_topic_name,
                key=model.id,
                message=extraction_model.as_serializable_json(),
                headers=get_propagation_headers(),
                timeout=30.0,
            )
