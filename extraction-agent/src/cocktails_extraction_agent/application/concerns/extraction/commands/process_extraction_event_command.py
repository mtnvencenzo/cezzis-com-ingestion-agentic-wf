import json
import logging
from typing import cast

from cezzis_kafka import KafkaConsumerSettings, KafkaProducer
from cezzis_otel import get_propagation_headers
from injector import inject
from langchain.agents import create_agent
from langchain_core.messages import BaseMessage
from mediatr import GenericQuery, Mediator
from opentelemetry import trace

from cocktails_extraction_agent.application.concerns.extraction.models.cocktail_extraction_model import (
    CocktailExtractionModel,
)
from cocktails_extraction_agent.application.prompts.extraction_prompts import (
    extraction_sys_prompt,
    extraction_user_prompt,
)
from cocktails_extraction_agent.application.tools.emoji_remover.emoji_remover import remove_emojis
from cocktails_extraction_agent.application.tools.html_tag_remover.html_tag_remover import remove_html_tags
from cocktails_extraction_agent.application.tools.markdown_remover.markdown_remover import remove_markdown
from cocktails_extraction_agent.domain.config.app_options import AppOptions
from cocktails_extraction_agent.infrastructure.clients.cocktails_api.cocktail_api import CocktailModel
from cocktails_extraction_agent.infrastructure.llm.ollama_llm_factory import OllamaLLMFactory


class ProcessExtractionEventCommand(GenericQuery[bool]):
    def __init__(self, model: CocktailModel) -> None:
        self.model = model


@Mediator.behavior
class ProcessExtractionEventCommandValidator:
    def handle(self, command: ProcessExtractionEventCommand, next) -> None:
        if not command.model or not command.model.id:
            raise ValueError("Invalid cocktail model provided for extraction processing.")
        return next()


@Mediator.handler
class ProcessExtractionEventCommandHandler:
    @inject
    def __init__(
        self,
        kafka_producer: KafkaProducer,
        app_options: AppOptions,
        ollama_llm_factory: OllamaLLMFactory,
    ) -> None:
        self.kafka_producer = kafka_producer
        self.app_options = app_options
        self.ollama_llm_factory = ollama_llm_factory
        self.logger = logging.getLogger("process_extraction_event_command_handler")
        self.tracer = trace.get_tracer("extraction_agent")
        self.llm = self.ollama_llm_factory.get_ollama_chat(name=f"convert_content [{self.app_options.model}]")
        self.agent = create_agent(model=self.llm, tools=[remove_markdown, remove_html_tags, remove_emojis])

    async def handle(self, command: ProcessExtractionEventCommand) -> bool:
        self.logger.info("Processing extraction event")

        self.logger.info(
            msg="Processing cocktail extraction message item",
            extra={
                "cocktail.id": command.model.id,
            },
        )

        result_content = ""

        if not self.app_options.use_llm:
            # ----------------------------------------------------------------------------
            # If not using LLM, use basic cleaning tools
            # ----------------------------------------------------------------------------
            result_content = await remove_markdown.ainvoke(command.model.content or "")
            result_content = await remove_html_tags.ainvoke(result_content or "")
            result_content = await remove_emojis.ainvoke(result_content or "")
        else:
            # ----------------------------------------------------------------------------
            # Using LLM, process with agent
            # ----------------------------------------------------------------------------
            agent_result = await self.agent.ainvoke(
                {
                    "messages": [
                        {"role": "system", "content": extraction_sys_prompt},
                        {
                            "role": "user",
                            "content": extraction_user_prompt.format(input_text=command.model.content or ""),
                        },
                    ]
                }
            )

            result_list = cast(list[BaseMessage], agent_result["messages"])
            result_content = result_list[-1].content if result_list else ""

            if isinstance(result_content, list):
                result_content = "\n".join(s if isinstance(s, str) else json.dumps(s) for s in result_content)
            elif not isinstance(result_content, str):
                result_content = str(result_content)

        # Take the cleaned content and create the extraction model
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
                "messaging.kafka.topic_name": self.app_options.results_topic_name,
                "cocktail.id": command.model.id,
            },
        )

        self.kafka_producer.send_and_wait(
            topic=self.app_options.results_topic_name,
            key=command.model.id,
            message=extraction_model.as_serializable_json(),
            headers=get_propagation_headers(),
            timeout=30.0,
        )

        return True
