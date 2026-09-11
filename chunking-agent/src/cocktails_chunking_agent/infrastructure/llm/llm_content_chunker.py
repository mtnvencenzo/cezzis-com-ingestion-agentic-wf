import json
import logging
import time
from typing import Any, List, cast

from injector import inject
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables.config import RunnableConfig
from langfuse.langchain import CallbackHandler

from cocktails_chunking_agent.domain.config import AppOptions, LLMModelOptions
from cocktails_chunking_agent.domain.models.cocktail_chunking_model import (
    CocktailDescriptionChunk,
)
from cocktails_chunking_agent.domain.prompts.chunking_prompts import (
    build_fix_prompt,
    chunking_sys_prompt,
    chunking_user_prompt,
)
from cocktails_chunking_agent.infrastructure.llm.ollama_llm_factory import OllamaLLMFactory

ALLOWED_CHUNK_CATEGORIES = {
    "famous_references",
    "historical_and_geographical",
    "suggestions",
    "flavor_profile",
    "ingredients",
    "directions",
    "occasions",
    "variations",
    "other",
}


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
        initial_langfuse_config = self._build_langfuse_config(
            cocktail_id=cocktail_id,
            attempt_number=1,
            retry_status="initial",
        )

        agent_result = await self.agent.ainvoke(
            {"messages": agent_messages},
            config=initial_langfuse_config,
            timeout=self.llm_timeout,
        )

        self.langfuse_handler.client.flush()

        result_content = self._parse_agent_result(agent_result)
        if not result_content:
            return None

        try:
            array_result = json.loads(result_content)
            return self._build_chunks(array_result)
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            self._logger.warning(
                "Initial chunking output validation failed, attempting to fix the output. "
                "cocktail_id=%s error=%s raw_response=%s",
                cocktail_id,
                e,
                self._truncate(result_content),
            )
            fix_prompt = build_fix_prompt(str(e), result_content)
            agent_messages.append(AIMessage(content=result_content))
            agent_messages.append(HumanMessage(content=fix_prompt))
            retry_langfuse_config = self._build_langfuse_config(
                cocktail_id=cocktail_id,
                attempt_number=2,
                retry_status="repair",
                validation_error=str(e),
            )
            agent_result_retry = await self.agent.ainvoke(
                {"messages": agent_messages},
                config=retry_langfuse_config,
                timeout=self.llm_timeout,
            )
            self.langfuse_handler.client.flush()
            result_content_retry = self._parse_agent_result(agent_result_retry)
            if not result_content_retry:
                return None

            try:
                array_result = json.loads(result_content_retry)
                return self._build_chunks(array_result)
            except (json.JSONDecodeError, TypeError, ValueError) as retry_e:
                self._logger.error(
                    "Repair attempt chunking output validation failed. cocktail_id=%s error=%s raw_response=%s",
                    cocktail_id,
                    retry_e,
                    self._truncate(result_content_retry),
                )
                self._log_content_json(cocktail_id, result_content_retry)
                raise
        except Exception as e:
            self._logger.error(
                "Unexpected error parsing chunking output. cocktail_id=%s error=%s raw_response=%s",
                cocktail_id,
                e,
                self._truncate(result_content),
            )
            self._log_content_json(cocktail_id, result_content)
            raise

    def _build_chunks(self, array_result: Any) -> List[CocktailDescriptionChunk]:
        """Normalize the LLM's parsed JSON output into a list of CocktailDescriptionChunk.

        Handles cases where the LLM double-encodes array items as JSON strings
        instead of returning JSON objects directly, wraps the whole array in a string,
        returns a single chunk dictionary, or wraps the array inside a dictionary key (e.g. {"chunks": [...]}).
        """
        if isinstance(array_result, str):
            array_result = json.loads(array_result)

        if isinstance(array_result, dict):
            if "category" in array_result and "content" in array_result:
                array_result = [array_result]
            elif "chunks" in array_result and isinstance(array_result["chunks"], list):
                array_result = array_result["chunks"]
            elif "data" in array_result and isinstance(array_result["data"], list):
                array_result = array_result["data"]
            elif len(array_result) == 1 and isinstance(next(iter(array_result.values())), list):
                array_result = next(iter(array_result.values()))

        if not isinstance(array_result, list):
            raise ValueError(f"Expected a JSON array of chunk objects, got {type(array_result).__name__}")

        chunks: List[CocktailDescriptionChunk] = []
        for item in array_result:
            if isinstance(item, str):
                item = json.loads(item)

            if not isinstance(item, dict):
                raise ValueError(f"Expected a JSON object for each chunk, got {type(item).__name__}")

            chunks.append(CocktailDescriptionChunk(**item))

        return chunks

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

    def _build_langfuse_config(
        self,
        cocktail_id: str,
        attempt_number: int,
        retry_status: str,
        validation_error: str | None = None,
    ) -> RunnableConfig:
        metadata: dict[str, object] = {
            "cocktail_id": cocktail_id,
            "attempt_number": attempt_number,
            "retry_status": retry_status,
            "langfuse_session_id": cocktail_id,
            "langfuse_tags": ["chunking", f"attempt:{attempt_number}", f"retry_status:{retry_status}"],
        }

        if validation_error:
            metadata["validation_error"] = validation_error

        return {
            "callbacks": [self.langfuse_handler],
            "metadata": metadata,
        }

    def _truncate(self, content: str, max_len: int = 2000) -> str:
        """Truncates content for safe inline logging without exceeding log size limits."""
        return content if len(content) <= max_len else f"{content[:max_len]}...<truncated>"

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
