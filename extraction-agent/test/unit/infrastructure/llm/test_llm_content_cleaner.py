import asyncio
from typing import Any, cast
from unittest.mock import AsyncMock

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from cocktails_extraction_agent.infrastructure.llm.llm_content_cleaner import LLMContentCleaner


class TestLLMContentCleaner:
    def test_clean_content_invokes_graph_and_returns_final_content(self) -> None:
        cleaner = object.__new__(LLMContentCleaner)
        cleaner.langfuse_handler = cast(Any, object())
        cleaner._initialize_mcp_agent = AsyncMock()
        cleaner.cleaning_graph = AsyncMock()
        cleaner.cleaning_graph.ainvoke = AsyncMock(return_value={"final_content": "Title", "current_content": "Title"})

        result = asyncio.run(cleaner.clean_content("adonis"))

        assert result == "Title"
        cleaner._initialize_mcp_agent.assert_awaited_once()
        cleaner.cleaning_graph.ainvoke.assert_awaited_once()

        graph_input = cleaner.cleaning_graph.ainvoke.await_args.args[0]
        assert graph_input["cocktail_id"] == "adonis"
        assert graph_input["cocktail_payload"] is None
        assert graph_input["current_content"] == ""
        assert graph_input["completed_tools"] == []
        assert graph_input["final_content"] is None
        assert graph_input["messages"] == []

    def test_extract_plain_text_ignores_non_text_blocks(self) -> None:
        cleaner = object.__new__(LLMContentCleaner)

        result = cleaner._extract_plain_text(
            [
                {"type": "text", "text": "cleaned value"},
                {"type": "tool_result", "structuredContent": {"foo": "bar"}},
                "tail",
            ]
        )

        assert result == "cleaned value\ntail"

    def test_model_node_returns_plain_text_when_no_tool_calls_are_present(self) -> None:
        cleaner = object.__new__(LLMContentCleaner)
        cleaner.langfuse_handler = cast(Any, object())
        cleaner.tool_enabled_llm = AsyncMock()
        cleaner.tool_enabled_llm.ainvoke = AsyncMock(return_value=AIMessage(content="Cleaned plain text"))

        result = asyncio.run(
            cleaner._model_node(
                {
                    "messages": [HumanMessage(content="clean this")],
                    "cocktail_id": "adonis",
                    "cocktail_payload": None,
                    "current_content": "## Title",
                    "completed_tools": [],
                    "final_content": None,
                }
            )
        )

        assert result["final_content"] == "Cleaned plain text"

    def test_model_node_returns_textual_tool_plan_as_plain_text(self) -> None:
        cleaner = object.__new__(LLMContentCleaner)
        cleaner.langfuse_handler = cast(Any, object())
        cleaner.tool_enabled_llm = AsyncMock()
        cleaner.tool_enabled_llm.ainvoke = AsyncMock(
            return_value=AIMessage(
                content=(
                    "Here is the JSON for a function call with its proper arguments that best answers the given prompt:\n\n"
                    '{"name": "clean_markdown", "parameters": {"content": "## Title"}}\n\n'
                    '{"name": "remove_html_tags", "parameters": {"content": "stale html"}}'
                )
            )
        )

        result = asyncio.run(
            cleaner._model_node(
                {
                    "messages": [HumanMessage(content="clean this")],
                    "cocktail_id": "adonis",
                    "cocktail_payload": None,
                    "current_content": "## Title",
                    "completed_tools": [],
                    "final_content": None,
                }
            )
        )

        assert isinstance(result["final_content"], str)
        assert '"name": "clean_markdown"' in result["final_content"]

    def test_model_node_limits_tool_calls_to_one(self) -> None:
        cleaner = object.__new__(LLMContentCleaner)
        cleaner.langfuse_handler = cast(Any, object())
        cleaner.processing_tools_by_name = {
            "clean_markdown": object(),
            "remove_html_tags": object(),
        }
        cleaner.tool_enabled_llm = AsyncMock()
        cleaner.tool_enabled_llm.ainvoke = AsyncMock(
            return_value=AIMessage(
                content="",
                tool_calls=[
                    {"name": "clean_markdown", "args": {"content": "## Title"}, "id": "call-1", "type": "tool_call"},
                    {
                        "name": "remove_html_tags",
                        "args": {"content": "<b>Title</b>"},
                        "id": "call-2",
                        "type": "tool_call",
                    },
                ],
            )
        )

        result = asyncio.run(
            cleaner._model_node(
                {
                    "messages": [HumanMessage(content="clean this")],
                    "cocktail_id": "adonis",
                    "cocktail_payload": None,
                    "current_content": "## Title",
                    "completed_tools": [],
                    "final_content": None,
                }
            )
        )

        ai_message = result["messages"][0]
        assert isinstance(ai_message, AIMessage)
        assert len(ai_message.tool_calls) == 1
        assert ai_message.tool_calls[0]["name"] == "clean_markdown"

    def test_model_node_uses_any_matching_tool_call_name(self) -> None:
        cleaner = object.__new__(LLMContentCleaner)
        cleaner.langfuse_handler = cast(Any, object())
        cleaner.processing_tools_by_name = {"convert_to_plaintext": object()}
        cleaner.tool_enabled_llm = AsyncMock()
        cleaner.tool_enabled_llm.ainvoke = AsyncMock(
            return_value=AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "default_api:convert_to_plain_text",
                        "args": {"content": "## Title"},
                        "id": "call-1",
                        "type": "tool_call",
                    },
                    {
                        "name": "convert_to_plaintext",
                        "args": {"content": "## Title"},
                        "id": "call-2",
                        "type": "tool_call",
                    },
                ],
            )
        )

        result = asyncio.run(
            cleaner._model_node(
                {
                    "messages": [HumanMessage(content="clean this")],
                    "cocktail_id": "adonis",
                    "cocktail_payload": None,
                    "current_content": "## Title",
                    "completed_tools": [],
                    "final_content": None,
                }
            )
        )

        ai_message = result["messages"][0]
        assert isinstance(ai_message, AIMessage)
        assert len(ai_message.tool_calls) == 1
        assert ai_message.tool_calls[0]["name"] == "convert_to_plaintext"

    def test_update_after_tool_adds_follow_up_prompt(self) -> None:
        cleaner = object.__new__(LLMContentCleaner)
        cleaner.processing_tools_by_name = {
            "convert_to_plaintext": object(),
            "extract_title": object(),
        }

        result = cleaner._update_after_tool(
            {
                "messages": [ToolMessage(content="Title", tool_call_id="call-1", name="convert_to_plaintext")],
                "cocktail_id": "adonis",
                "cocktail_payload": {"item": {"id": "adonis", "content": "## Title"}},
                "current_content": "## Title",
                "completed_tools": ["get_cocktail"],
                "final_content": None,
            }
        )

        assert result["current_content"] == "Title"
        assert result["completed_tools"] == ["get_cocktail", "convert_to_plaintext"]
        assert isinstance(result["messages"][0], HumanMessage)

    def test_update_after_tool_returns_to_model_after_processing_tool(self) -> None:
        cleaner = object.__new__(LLMContentCleaner)
        cleaner.processing_tools_by_name = {
            "convert_to_plaintext": object(),
            "extract_title": object(),
        }

        result = cleaner._update_after_tool(
            {
                "messages": [ToolMessage(content="Title", tool_call_id="call-2", name="extract_title")],
                "cocktail_id": "adonis",
                "cocktail_payload": {"item": {"id": "adonis", "content": "## Title"}},
                "current_content": "Title",
                "completed_tools": ["get_cocktail", "convert_to_plaintext"],
                "final_content": None,
            }
        )

        assert result["current_content"] == "Title"
        assert result["completed_tools"] == ["get_cocktail", "convert_to_plaintext", "extract_title"]
        assert isinstance(result["messages"][0], HumanMessage)
        assert "final_content" not in result

    def test_update_after_tool_does_not_complete_after_single_processing_tool(self) -> None:
        cleaner = object.__new__(LLMContentCleaner)
        cleaner.processing_tools_by_name = {"convert_to_plaintext": object()}

        result = cleaner._update_after_tool(
            {
                "messages": [ToolMessage(content="Title", tool_call_id="call-1", name="convert_to_plaintext")],
                "cocktail_id": "adonis",
                "cocktail_payload": {"item": {"id": "adonis", "content": "## Title"}},
                "current_content": "## Title",
                "completed_tools": ["get_cocktail"],
                "final_content": None,
            }
        )

        assert result["current_content"] == "Title"
        assert result["completed_tools"] == ["get_cocktail", "convert_to_plaintext"]
        assert isinstance(result["messages"][0], HumanMessage)
        assert "final_content" not in result

    def test_update_after_tool_completes_when_repeated_tool_makes_no_progress(self) -> None:
        cleaner = object.__new__(LLMContentCleaner)
        cleaner.processing_tools_by_name = {"convert_to_plaintext": object()}

        result = cleaner._update_after_tool(
            {
                "messages": [ToolMessage(content="Title", tool_call_id="call-2", name="convert_to_plaintext")],
                "cocktail_id": "adonis",
                "cocktail_payload": {"item": {"id": "adonis", "content": "## Title"}},
                "current_content": "Title",
                "completed_tools": ["get_cocktail", "convert_to_plaintext"],
                "final_content": None,
            }
        )

        assert result["current_content"] == "Title"
        assert result["completed_tools"] == ["get_cocktail", "convert_to_plaintext", "convert_to_plaintext"]
        assert result["final_content"] == "Title"
        assert "messages" not in result

    def test_update_after_tool_allows_first_idempotent_tool_call(self) -> None:
        cleaner = object.__new__(LLMContentCleaner)
        cleaner.processing_tools_by_name = {"extract_title": object()}

        result = cleaner._update_after_tool(
            {
                "messages": [ToolMessage(content="Title", tool_call_id="call-1", name="extract_title")],
                "cocktail_id": "adonis",
                "cocktail_payload": {"item": {"id": "adonis", "content": "## Title"}},
                "current_content": "Title",
                "completed_tools": ["get_cocktail"],
                "final_content": None,
            }
        )

        assert result["current_content"] == "Title"
        assert result["completed_tools"] == ["get_cocktail", "extract_title"]
        assert isinstance(result["messages"][0], HumanMessage)

    def test_update_after_tool_completes_when_tool_name_is_unexpected(self) -> None:
        cleaner = object.__new__(LLMContentCleaner)
        cleaner.processing_tools_by_name = {"convert_to_plaintext": object()}

        result = cleaner._update_after_tool(
            {
                "messages": [
                    ToolMessage(content="Title", tool_call_id="call-3", name="default_api:convert_to_plain_text")
                ],
                "cocktail_id": "adonis",
                "cocktail_payload": {"item": {"id": "adonis", "content": "## Title"}},
                "current_content": "Title",
                "completed_tools": ["get_cocktail", "convert_to_plaintext"],
                "final_content": None,
            }
        )

        assert result["current_content"] == "Title"
        assert result["completed_tools"] == ["get_cocktail", "convert_to_plaintext"]
        assert result["final_content"] == "Title"
        assert "messages" not in result

    def test_update_after_tool_raises_when_tool_iterations_exceed_limit(self) -> None:
        cleaner = object.__new__(LLMContentCleaner)
        cleaner.processing_tools_by_name = {"convert_to_plaintext": object()}

        try:
            cleaner._update_after_tool(
                {
                    "messages": [
                        ToolMessage(content="Cleaned Title", tool_call_id="call-9", name="convert_to_plaintext")
                    ],
                    "cocktail_id": "adonis",
                    "cocktail_payload": {"item": {"id": "adonis", "content": "## Title"}},
                    "current_content": "Title",
                    "completed_tools": ["convert_to_plaintext"] * cleaner._MAX_TOOL_ITERATIONS,
                    "final_content": None,
                }
            )
        except RuntimeError as exc:
            assert "maximum number of tool iterations" in str(exc)
        else:
            raise AssertionError("Expected RuntimeError when tool iterations exceed the limit")
