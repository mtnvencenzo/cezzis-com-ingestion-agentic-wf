from cocktails_chunking_agent.domain.prompts.chunking_prompts import chunking_sys_prompt


class TestChunkingPrompts:
    def test_chunking_prompt_prefers_single_chunk_per_category_and_absorbs_headings(self) -> None:
        assert "Prefer one object per category." in chunking_sys_prompt
        assert "Section headings and labels belong to the same category as the content they introduce." in (
            chunking_sys_prompt
        )
        assert "do not emit standalone heading-only chunks" in chunking_sys_prompt
        assert "you may create multiple objects with the same category" in chunking_sys_prompt
        assert "Prefer this category over historical_and_geographical when named references are central" in (
            chunking_sys_prompt
        )
        assert "- glassware" not in chunking_sys_prompt
        assert "serving-vessel instructions" in chunking_sys_prompt
