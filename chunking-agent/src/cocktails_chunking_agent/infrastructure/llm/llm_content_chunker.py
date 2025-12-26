import json
import logging
import time
from typing import Any, List, cast

from injector import inject
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langfuse.langchain import CallbackHandler

from cocktails_chunking_agent.domain.config import AppOptions, LLMModelOptions
from cocktails_chunking_agent.domain.models.cocktail_chunking_model import (
    CocktailDescriptionChunk,
)
from cocktails_chunking_agent.domain.prompts.chunking_prompts import (
    chunking_sys_prompt,
    chunking_user_prompt,
)
from cocktails_chunking_agent.infrastructure.llm.ollama_llm_factory import OllamaLLMFactory


class LLMContentChunker:
    """A markdown to text converter using an LLM model."""

    @inject
    def __init__(
        self, ollama_llm_factory: OllamaLLMFactory, llm_model_options: LLMModelOptions, app_options: AppOptions
    ) -> None:
        """Initialize the LLMContentChunker with LLM options and model settings.

        Args:
            ollama_llm_factory (OllamaLLMFactory): The factory to create Ollama LLM instances.
            model_options (LLMModelOptions): The model settings for configuration.
        """
        self.llm = ollama_llm_factory.get_ollama_chat(name=f"chunk_content [{llm_model_options.model}]")
        self.agent = create_agent(model=self.llm)
        self.llm_timeout = llm_model_options.timeout_seconds or 60
        self.langfuse_handler = CallbackHandler(update_trace=True)
        self._logger = logging.getLogger("llm_content_chunker")
        self._app_options = app_options

    async def chunk_content(self, cocktail_id: str, extraction_text: str) -> List[CocktailDescriptionChunk] | None:
        """Convert exracted plain text content into chunks using LLM.

        Args:
            extraction_text (str): The extracted plain text content to chunk.

        Returns:
            List[CocktailDescriptionChunk]: The list of content chunks.
        """
        self._logger.info("Starting content chunking using LLM agent.")

        agent_messages = [
            SystemMessage(content=chunking_sys_prompt),
            HumanMessage(content=chunking_user_prompt.format(input_text=extraction_text)),
        ]

        agent_result = await self.agent.ainvoke(
            {"messages": agent_messages},
            config={"callbacks": [self.langfuse_handler]},
            timeout=self.llm_timeout,
        )

        self.langfuse_handler.client.flush()

        result_content = self._parse_agent_result(agent_result)
        if not result_content:
            return None

        try:
            array_result = json.loads(result_content)
            return [CocktailDescriptionChunk(**item) for item in array_result]
        except json.JSONDecodeError as e:
            self._logger.warning(
                "Initial JSON parsing failed, attempting to fix the output.",
                extra={"error": str(e), "cocktail_id": cocktail_id},
            )
            # Attempt to fix the output by asking the agent to correct its response, including the error message
            fix_prompt = (
                "The previous response was not valid JSON. "
                "Please return only a valid JSON array as specified in the original instructions. "
                f"\n\nError details: {str(e)}"
                f"\n\nHere is your previous json response, please fix this json and return only the fixed json array according to the original instructions: \n\n{result_content}"
            )
            agent_messages.append(AIMessage(content=result_content))
            agent_messages.append(HumanMessage(content=fix_prompt))
            agent_result_retry = await self.agent.ainvoke(
                {"messages": agent_messages},
                config={"callbacks": [self.langfuse_handler]},
                timeout=self.llm_timeout,
            )
            self.langfuse_handler.client.flush()
            result_content_retry = self._parse_agent_result(agent_result_retry)
            if not result_content_retry:
                return None

            try:
                array_result = json.loads(result_content_retry)
                return [CocktailDescriptionChunk(**item) for item in array_result]
            except:
                self._log_content_json(cocktail_id, result_content_retry)
                raise
        except:
            self._log_content_json(cocktail_id, result_content)
            raise

    def _parse_agent_result(self, agent_result: dict[str, Any] | Any) -> str | None:
        result_list = cast(list[BaseMessage], agent_result["messages"])
        result_content = result_list[-1].content if result_list else ""

        if not result_content:
            return None

        if isinstance(result_content, list):
            return "\n".join(s if isinstance(s, str) else json.dumps(s) for s in result_content)
        elif not isinstance(result_content, str):
            return str(result_content)

        return result_content

    def _log_content_json(self, cocktail_id: str, result_content: str) -> None:
        """Logs the content JSON in chunks to avoid exceeding log size limits."""

        if self._app_options.log_dir:
            epoch = int(time.time())
            output_path = f"{self._app_options.log_dir}/{cocktail_id}-{epoch}.json"

            try:
                with open(output_path, "w") as f:
                    f.write(result_content)
            except Exception as e:
                self._logger.error(
                    "Failed to write chunking output to file.",
                    extra={"error": str(e)},
                )
