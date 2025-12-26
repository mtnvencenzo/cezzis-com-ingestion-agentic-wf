import json
from typing import cast

from injector import inject
from langchain.agents import create_agent
from langchain_core.messages import BaseMessage
from langfuse.langchain import CallbackHandler

from cocktails_extraction_agent.domain.config.llm_model_options import LLMModelOptions
from cocktails_extraction_agent.domain.prompts.extraction_prompts import (
    extraction_sys_prompt,
    extraction_user_prompt,
)
from cocktails_extraction_agent.domain.tools import (
    remove_emojis,
    remove_html_tags,
    remove_markdown,
    remove_special_json_characters,
)
from cocktails_extraction_agent.infrastructure.llm.ollama_llm_factory import OllamaLLMFactory


class LLMContentCleaner:
    @inject
    def __init__(self, ollama_llm_factory: OllamaLLMFactory, llm_model_options: LLMModelOptions) -> None:
        """Initialize the LLMContentCleaner with LLM options and model settings.

        Args:
            ollama_llm_factory (OllamaLLMFactory): The factory to create Ollama LLM instances.
            model_options (LLMModelOptions): The model settings for configuration.
        """
        self.llm = ollama_llm_factory.get_ollama_chat(name=f"clean_content [{llm_model_options.model}]")
        self.agent = create_agent(
            model=self.llm, tools=[remove_markdown, remove_html_tags, remove_emojis, remove_special_json_characters]
        )
        self.llm_timeout = llm_model_options.timeout_seconds or 60
        self.langfuse_handler = CallbackHandler(update_trace=True)

    async def clean_content(self, content: str) -> str | None:
        """Clean the provided content by removing markdown, emojis, and HTML tags using an LLM agent.

        Args:
            content (str): The content to be cleaned of markdown, emojis, and HTML tags.

        Returns:
            str | None: The cleaned content as a string, or None if cleaning fails.
        """
        agent_result = await self.agent.ainvoke(
            {
                "messages": [
                    {"role": "system", "content": extraction_sys_prompt},
                    {
                        "role": "user",
                        "content": extraction_user_prompt.format(input_text=content or ""),
                    },
                ]
            },
            config={"callbacks": [self.langfuse_handler]},
            timeout=self.llm_timeout,
        )

        result_list = cast(list[BaseMessage], agent_result["messages"])
        result_content = result_list[-1].content if result_list else ""

        if isinstance(result_content, list):
            result_content = "\n".join(s if isinstance(s, str) else json.dumps(s) for s in result_content)
        elif not isinstance(result_content, str):
            result_content = str(result_content)

        return result_content
