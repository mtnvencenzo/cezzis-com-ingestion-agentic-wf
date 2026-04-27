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

    def test_fetch_cocktail_node_extracts_content_and_builds_initial_prompt(self) -> None:
        cleaner = object.__new__(LLMContentCleaner)
        cleaner.fetch_tool = AsyncMock()
        cleaner.fetch_tool.name = "get_cocktail"
        cleaner.fetch_tool.ainvoke = AsyncMock(return_value={"item": {"id": "adonis", "content": "## Title"}})

        result = asyncio.run(
            cleaner._fetch_cocktail_node(
                {
                    "messages": [],
                    "cocktail_id": "adonis",
                    "cocktail_payload": None,
                    "current_content": "",
                    "completed_tools": [],
                    "final_content": None,
                }
            )
        )

        cleaner.fetch_tool.ainvoke.assert_awaited_once_with({"id": "adonis"})
        assert result["cocktail_payload"] == {"item": {"id": "adonis", "content": "## Title"}}
        assert result["current_content"] == ""
        assert result["completed_tools"] == ["get_cocktail"]
        assert isinstance(result["messages"][0], SystemMessage)
        assert isinstance(result["messages"][1], HumanMessage)
        assert "Cocktail payload:" in result["messages"][1].content
        assert '"content": "## Title"' in result["messages"][1].content

    def test_fetch_cocktail_node_accepts_payload_without_content_field(self) -> None:
        cleaner = object.__new__(LLMContentCleaner)
        cleaner.fetch_tool = AsyncMock()
        cleaner.fetch_tool.name = "get_cocktail"
        cleaner.fetch_tool.ainvoke = AsyncMock(return_value={"item": {"id": "adonis"}})

        result = asyncio.run(
            cleaner._fetch_cocktail_node(
                {
                    "messages": [],
                    "cocktail_id": "adonis",
                    "cocktail_payload": None,
                    "current_content": "",
                    "completed_tools": [],
                    "final_content": None,
                }
            )
        )

        assert result["cocktail_payload"] == {"item": {"id": "adonis"}}
        assert result["current_content"] == ""

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

    def test_update_after_tool_sets_final_content_when_cleaning_complete(self) -> None:
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

        assert result["final_content"] == "Title"

    def test_update_after_tool_sets_final_content_when_only_one_mcp_tool_is_available(self) -> None:
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
        assert result["final_content"] == "Title"
