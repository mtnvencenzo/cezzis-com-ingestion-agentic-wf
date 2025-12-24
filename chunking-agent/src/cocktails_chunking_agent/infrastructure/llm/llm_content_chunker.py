import json
from typing import List, cast

from injector import inject
from langchain.agents import create_agent
from langchain_core.messages import BaseMessage
from langfuse.langchain import CallbackHandler

from cocktails_chunking_agent.application.concerns.chunking.models.cocktail_chunking_model import (
    CocktailDescriptionChunk,
)
from cocktails_chunking_agent.application.prompts.chunking_prompts import (
    chunking_sys_prompt,
    chunking_user_prompt,
)
from cocktails_chunking_agent.domain.config.llm_model_options import LLMModelOptions
from cocktails_chunking_agent.infrastructure.llm.ollama_llm_factory import OllamaLLMFactory


class LLMContentChunker:
    """A markdown to text converter using an LLM model."""

    @inject
    def __init__(self, ollama_llm_factory: OllamaLLMFactory, llm_model_options: LLMModelOptions) -> None:
        """Initialize the LLMContentChunker with LLM options and model settings.

        Args:
            llm_options (LLMOptions): The LLM options for configuration.
            model_options (LLMModelOptions): The model settings for configuration.
        """
        self.llm = ollama_llm_factory.get_ollama_chat(name=f"chunk_content [{llm_model_options.model}]")
        self.agent = create_agent(model=self.llm)
        self.llm_timeout = llm_model_options.timeout_seconds or 60
        self.langfuse_handler = CallbackHandler(update_trace=True)

    async def chunk_content(self, extraction_text: str) -> List[CocktailDescriptionChunk] | None:
        """Convet exracted plain text content into chunks using LLM.

        Args:
            extraction_text (str): The extracted plain text content to chunk.

        Returns:
            List[CocktailDescriptionChunk]: The list of content chunks.
        """

        agent_result = await self.agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "system",
                        "content": chunking_sys_prompt
                    },
                    {
                        "role": "user",
                        "content": chunking_user_prompt.format(input_text=extraction_text),
                    },
                ]
            },
            config={"callbacks": [self.langfuse_handler]},
            timeout=self.llm_timeout,
        )

        result_list = cast(list[BaseMessage], agent_result["messages"])
        result_content = result_list[-1].content if result_list else ""

        self.langfuse_handler.client.flush()

        if not result_content:
            return None

        if isinstance(result_content, list):
            result_content = "\n".join(s if isinstance(s, str) else json.dumps(s) for s in result_content)
        elif not isinstance(result_content, str):
            result_content = str(result_content)

        array_result = json.loads(result_content)
        return [CocktailDescriptionChunk(**item) for item in array_result]
