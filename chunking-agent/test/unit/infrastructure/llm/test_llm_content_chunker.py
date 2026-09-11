import pytest

from cocktails_chunking_agent.domain.prompts.chunking_prompts import build_fix_prompt
from cocktails_chunking_agent.infrastructure.llm.llm_content_chunker import LLMContentChunker


class TestLLMContentChunker:
    def test_build_fix_prompt_preserves_content_repair_constraints(self) -> None:
        fix_prompt = build_fix_prompt("bad json", '{"chunks": [{"category": "ingredients"}]}')

        assert "Preserve the original source text exactly." in fix_prompt
        assert "fix only JSON syntax or escaping" in fix_prompt
        assert "Return only the corrected JSON object with no explanation." in fix_prompt

    def test_build_langfuse_config_includes_trace_metadata_for_initial_attempt(self, mocker) -> None:
        chunker = LLMContentChunker.__new__(LLMContentChunker)
        chunker.langfuse_handler = mocker.sentinel.langfuse_handler

        config = chunker._build_langfuse_config(
            cocktail_id="cocktail-123",
            attempt_number=1,
            retry_status="initial",
        )

        callbacks = config.get("callbacks")
        metadata = config.get("metadata")

        assert callbacks == [mocker.sentinel.langfuse_handler]
        assert metadata is not None
        assert metadata["cocktail_id"] == "cocktail-123"
        assert metadata["attempt_number"] == 1
        assert metadata["retry_status"] == "initial"
        assert metadata["langfuse_session_id"] == "cocktail-123"
        assert metadata["langfuse_tags"] == ["chunking", "attempt:1", "retry_status:initial"]
        assert "validation_error" not in metadata

    def test_build_langfuse_config_includes_validation_error_for_retry(self, mocker) -> None:
        chunker = LLMContentChunker.__new__(LLMContentChunker)
        chunker.langfuse_handler = mocker.sentinel.langfuse_handler

        config = chunker._build_langfuse_config(
            cocktail_id="cocktail-123",
            attempt_number=2,
            retry_status="repair",
            validation_error="invalid json",
        )

        metadata = config.get("metadata")

        assert metadata is not None
        assert metadata["validation_error"] == "invalid json"
        assert metadata["langfuse_tags"] == ["chunking", "attempt:2", "retry_status:repair"]

    def test_build_chunks_accepts_single_dict(self) -> None:
        chunker = LLMContentChunker.__new__(LLMContentChunker)
        result = chunker._build_chunks({"category": "ingredients", "content": "1 oz gin"})
        assert len(result) == 1
        assert result[0].category == "ingredients"
        assert result[0].content == "1 oz gin"

    def test_build_chunks_accepts_dict_wrapping_chunks_list(self) -> None:
        chunker = LLMContentChunker.__new__(LLMContentChunker)
        result = chunker._build_chunks({"chunks": [{"category": "directions", "content": "Stir well"}]})
        assert len(result) == 1
        assert result[0].category == "directions"
        assert result[0].content == "Stir well"

    def test_build_chunks_accepts_standard_list(self) -> None:
        chunker = LLMContentChunker.__new__(LLMContentChunker)
        result = chunker._build_chunks(
            [
                {"category": "ingredients", "content": "1 oz gin"},
                {"category": "directions", "content": "Stir with ice"},
            ]
        )
        assert len(result) == 2
        assert result[0].category == "ingredients"
        assert result[1].category == "directions"
