import logging

from cezzis_kafka import KafkaConsumerSettings, KafkaProducer
from cezzis_otel import get_propagation_headers
from injector import inject
from mediatr import GenericQuery, Mediator
from opentelemetry import trace

from cocktails_extraction_agent.application.concerns.extraction.models.cocktail_extraction_model import (
    CocktailExtractionModel,
)
from cocktails_extraction_agent.application.tools.emoji_remover.emoji_remover import remove_emojis
from cocktails_extraction_agent.application.tools.html_tag_remover.html_tag_remover import remove_html_tags
from cocktails_extraction_agent.application.tools.markdown_remover.markdown_remover import remove_markdown
from cocktails_extraction_agent.domain.config.ext_agent_options import ExtractionAgentOptions
from cocktails_extraction_agent.infrastructure.clients.cocktails_api.cocktail_api import CocktailModel


class ProcessExtractionEventCommand(GenericQuery[bool]):
    def __init__(self, model: CocktailModel) -> None:
        self.model = model


@Mediator.handler
class ProcessExtractionEventCommandHandler:
    @inject
    def __init__(
        self,
        kafka_producer: KafkaProducer,
        ext_agent_options: ExtractionAgentOptions,
        kafka_consumer_options: KafkaConsumerSettings,
    ) -> None:
        self.kafka_producer = kafka_producer
        self.kafka_consiumer_settings = kafka_consumer_options
        self.ext_agent_options = ext_agent_options
        self.logger = logging.getLogger("process_extraction_event_command_handler")
        self.tracer = trace.get_tracer("extraction_agent")

    async def handle(self, command: ProcessExtractionEventCommand) -> bool:
        self.logger.info("Processing extraction event")

        self.logger.info(
            msg="Processing cocktail extraction message item",
            extra={
                "cocktail.id": command.model.id,
            },
        )

        result_content = await remove_markdown.ainvoke(command.model.content or "")
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
            cocktail_model=command.model,
            extraction_text=result_content,
        )

        if extraction_model.extraction_text.strip() == "":
            self.logger.warning(
                msg="Empty extraction text received after processing",
                extra={
                    "cocktail.id": command.model.id,
                },
            )
            return True

        self.logger.info(
            msg="Sending cocktail extraction model to chunking topic",
            extra={
                "messaging.kafka.bootstrap_servers": self.kafka_producer.settings.bootstrap_servers,
                "messaging.kafka.topic_name": self.ext_agent_options.results_topic_name,
                "cocktail.id": command.model.id,
            },
        )

        self.kafka_producer.send_and_wait(
            topic=self.ext_agent_options.results_topic_name,
            key=command.model.id,
            message=extraction_model.as_serializable_json(),
            headers=get_propagation_headers(),
            timeout=30.0,
        )

        return True
