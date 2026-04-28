import json
import logging
import re
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
            array_result = self._parse_and_validate_chunk_result(result_content, extraction_text, cocktail_id)
            return [CocktailDescriptionChunk(**item) for item in array_result]
        except (json.JSONDecodeError, ValueError) as e:
            self._logger.warning(
                "Initial chunking output validation failed, attempting to fix the output.",
                extra={"error": str(e), "cocktail_id": cocktail_id},
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
                array_result = self._parse_and_validate_chunk_result(result_content_retry, extraction_text, cocktail_id)
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

    def _parse_and_validate_chunk_result(
        self, result_content: str, extraction_text: str, cocktail_id: str
    ) -> list[dict[str, str]]:
        array_result = json.loads(result_content)
        self._validate_chunk_output(array_result, extraction_text, cocktail_id)
        return cast(list[dict[str, str]], array_result)

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

    def _validate_chunk_output(self, array_result: Any, extraction_text: str, cocktail_id: str) -> None:
        if not isinstance(array_result, list):
            raise ValueError("Chunking output must be a JSON array")

        invalid_shapes: list[str] = []
        invalid_categories: list[str] = []
        content_type_errors: list[str] = []
        reconstructed_parts: list[str] = []

        for item in array_result:
            if not isinstance(item, dict):
                invalid_shapes.append("<non-object>")
                continue

            if set(item.keys()) != {"category", "content"}:
                invalid_shapes.append(str(sorted(item.keys())))

            category = item.get("category")
            content = item.get("content")

            if not isinstance(category, str) or category not in ALLOWED_CHUNK_CATEGORIES:
                invalid_categories.append(str(category))

            if not isinstance(content, str):
                content_type_errors.append(str(type(content).__name__))
                continue

            reconstructed_parts.append(content)

        invalid_shapes = sorted(set(invalid_shapes))
        if invalid_shapes:
            self._logger.warning(
                "Chunking output contained invalid object shapes.",
                extra={"cocktail_id": cocktail_id, "invalid_shapes": invalid_shapes},
            )
            raise ValueError(f"Chunking output contained invalid object shapes: {invalid_shapes}")

        invalid_categories = sorted(set(invalid_categories))
        if invalid_categories:
            self._logger.warning(
                "Chunking output contained invalid categories.",
                extra={"cocktail_id": cocktail_id, "invalid_categories": invalid_categories},
            )
            raise ValueError(f"Chunking output contained invalid categories: {invalid_categories}")

        content_type_errors = sorted(set(content_type_errors))
        if content_type_errors:
            self._logger.warning(
                "Chunking output contained non-string content fields.",
                extra={"cocktail_id": cocktail_id, "content_type_errors": content_type_errors},
            )
            raise ValueError(f"Chunking output contained non-string content fields: {content_type_errors}")

        reconstructed_text = "".join(reconstructed_parts)
        normalized_expected_text = self._normalize_text_for_validation(extraction_text)
        normalized_reconstructed_text = self._normalize_text_for_validation(reconstructed_text)

        if normalized_reconstructed_text != normalized_expected_text:
            mismatch_index = self._first_mismatch_index(normalized_expected_text, normalized_reconstructed_text)
            self._logger.warning(
                "Chunking output content did not reconstruct the original source text.",
                extra={
                    "cocktail_id": cocktail_id,
                    "mismatch_index": mismatch_index,
                    "expected_length": len(normalized_expected_text),
                    "actual_length": len(normalized_reconstructed_text),
                },
            )
            raise ValueError(
                "Chunking output content did not exactly match the original source text in order and completeness"
            )

    def _normalize_text_for_validation(self, text: str) -> str:
        normalized_line_endings = text.replace("\r\n", "\n").replace("\r", "\n")
        return re.sub(r"[ \t]*\n+[ \t]*", " ", normalized_line_endings)

    def _first_mismatch_index(self, expected_text: str, actual_text: str) -> int:
        for index, (expected_char, actual_char) in enumerate(zip(expected_text, actual_text)):
            if expected_char != actual_char:
                return index

        return min(len(expected_text), len(actual_text))

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
