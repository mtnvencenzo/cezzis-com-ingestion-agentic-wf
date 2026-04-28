import pytest

from cocktails_chunking_agent.domain.prompts.chunking_prompts import build_fix_prompt
from cocktails_chunking_agent.infrastructure.llm.llm_content_chunker import LLMContentChunker


class TestLLMContentChunker:
    def test_validate_chunk_output_accepts_exact_reconstruction(self, mocker) -> None:
        chunker = LLMContentChunker.__new__(LLMContentChunker)
        chunker._logger = mocker.Mock()

        chunker._validate_chunk_output(
            [
                {"category": "ingredients", "content": "2 oz gin"},
                {"category": "directions", "content": "Shake with ice."},
            ],
            extraction_text="2 oz ginShake with ice.",
            cocktail_id="test-cocktail",
        )

    def test_validate_chunk_output_accepts_newline_only_differences(self, mocker) -> None:
        chunker = LLMContentChunker.__new__(LLMContentChunker)
        chunker._logger = mocker.Mock()

        chunker._validate_chunk_output(
            [
                {"category": "ingredients", "content": "Ingredients 2 oz gin"},
                {"category": "directions", "content": "Directions Shake with ice."},
            ],
            extraction_text="Ingredients\n\n2 oz ginDirections\nShake with ice.",
            cocktail_id="test-cocktail",
        )

    def test_validate_chunk_output_rejects_invalid_categories(self, mocker) -> None:
        chunker = LLMContentChunker.__new__(LLMContentChunker)
        chunker._logger = mocker.Mock()

        with pytest.raises(ValueError, match="invalid categories"):
            chunker._validate_chunk_output(
                [
                    {"category": "ingredients_part1", "content": "2 oz gin"},
                    {"category": "directions", "content": "Serve in a coupe glass."},
                ],
                extraction_text="2 oz ginServe in a coupe glass.",
                cocktail_id="test-cocktail",
            )

    def test_validate_chunk_output_rejects_non_object_items(self, mocker) -> None:
        chunker = LLMContentChunker.__new__(LLMContentChunker)
        chunker._logger = mocker.Mock()

        with pytest.raises(ValueError, match="invalid object shapes"):
            chunker._validate_chunk_output(["bad-item"], extraction_text="", cocktail_id="test-cocktail")

    def test_validate_chunk_output_rejects_content_mismatch(self, mocker) -> None:
        chunker = LLMContentChunker.__new__(LLMContentChunker)
        chunker._logger = mocker.Mock()

        with pytest.raises(ValueError, match="did not exactly match"):
            chunker._validate_chunk_output(
                [{"category": "ingredients", "content": "2 oz vodka"}],
                extraction_text="2 oz gin",
                cocktail_id="test-cocktail",
            )

    def test_validate_chunk_output_rejects_invalid_object_keys(self, mocker) -> None:
        chunker = LLMContentChunker.__new__(LLMContentChunker)
        chunker._logger = mocker.Mock()

        with pytest.raises(ValueError, match="invalid object shapes"):
            chunker._validate_chunk_output(
                [{"category": "ingredients", "content": "2 oz gin", "extra": True}],
                extraction_text="2 oz gin",
                cocktail_id="test-cocktail",
            )

    def test_build_fix_prompt_preserves_content_repair_constraints(self) -> None:
        fix_prompt = build_fix_prompt("bad json", '[{"category": "ingredients"}]')

        assert "Preserve the original source text exactly." in fix_prompt
        assert "fix only JSON syntax or escaping" in fix_prompt
        assert "Return only the corrected JSON array with no explanation." in fix_prompt

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
