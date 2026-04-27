import json
from typing import Annotated, Any, TypedDict, cast

from injector import inject
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import Connection, SSEConnection, StreamableHttpConnection, WebsocketConnection
from langfuse.langchain import CallbackHandler
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from cocktails_extraction_agent.domain.config.app_options import AppOptions
from cocktails_extraction_agent.domain.config.llm_model_options import LLMModelOptions
from cocktails_extraction_agent.domain.prompts.extraction_prompts import (
    build_extraction_stepped_user_prompt,
    extraction_sys_prompt,
)
from cocktails_extraction_agent.infrastructure.llm.ollama_llm_factory import OllamaLLMFactory


class CleanerState(TypedDict):
    messages: Annotated[list[Any], add_messages]
    cocktail_id: str
    cocktail_payload: dict[str, Any] | None
    current_content: str
    completed_tools: list[str]
    final_content: str | None


class LLMContentCleaner:
    _MAX_TOOL_ITERATIONS = 8

    @inject
    def __init__(
        self, ollama_llm_factory: OllamaLLMFactory, llm_model_options: LLMModelOptions, app_options: AppOptions
    ) -> None:
        """Initialize the LLMContentCleaner with LLM options and model settings.

        Args:
            ollama_llm_factory (OllamaLLMFactory): The factory to create Ollama LLM instances.
            model_options (LLMModelOptions): The model settings for configuration.
            app_options (AppOptions): The application options instance.
        """
        self.llm = ollama_llm_factory.get_ollama_chat(name=f"clean_content [{llm_model_options.model}]")
        self.langfuse_handler = CallbackHandler(update_trace=True)
        self.app_options = app_options

        self.tool_enabled_llm = None
        self.cleaning_graph = None
        self.processing_tools_by_name: dict[str, Any] = {}

    async def clean_content(self, cocktail_id: str) -> str | None:
        """Retrieve a cocktail and transform its content using the MCP-backed graph.

        Args:
            cocktail_id (str): The cocktail identifier used by the MCP retrieval tool.

        Returns:
            str | None: The cleaned content as a string, or None if cleaning fails.
        """
        await self._initialize_mcp_agent()

        if self.cleaning_graph is None:
            raise RuntimeError("LLM cleaning graph is not initialized. Cannot clean content.")

        result = await self.cleaning_graph.ainvoke(
            {
                "messages": [],
                "cocktail_id": cocktail_id,
                "cocktail_payload": None,
                "current_content": "",
                "completed_tools": [],
                "final_content": None,
            },
            config={"callbacks": [self.langfuse_handler], "recursion_limit": self._MAX_TOOL_ITERATIONS * 3 + 1},
        )

        final_content = cast(str | None, result.get("final_content") or result.get("current_content") or None)
        return final_content

    async def _model_node(self, state: CleanerState) -> dict[str, Any]:
        if self.tool_enabled_llm is None:
            raise RuntimeError("LLM tool-enabled model is not initialized. Cannot call model node.")

        messages = (
            state["messages"]
            if len(state["messages"]) > 0
            else [
                SystemMessage(content=extraction_sys_prompt.strip()),
                HumanMessage(
                    content=build_extraction_stepped_user_prompt(
                        state.get("cocktail_id"),
                        state.get("cocktail_payload"),
                        state.get("current_content"),
                        state.get("completed_tools", []),
                    )
                ),
            ]
        )

        ai_message = await self.tool_enabled_llm.ainvoke(
            messages,
            config={"callbacks": [self.langfuse_handler]},
        )

        valid_tool_calls = [
            tool_call for tool_call in ai_message.tool_calls if tool_call.get("name") in self.processing_tools_by_name
        ]
        if valid_tool_calls:
            if len(valid_tool_calls) > 1:
                ai_message = ai_message.model_copy(update={"tool_calls": [valid_tool_calls[0]]})
            else:
                ai_message = ai_message.model_copy(update={"tool_calls": valid_tool_calls})
            return {"messages": [ai_message]}

        if ai_message.content:
            return {"messages": [ai_message], "final_content": self._extract_plain_text(ai_message.content)}
        else:
            return {"messages": [ai_message], "final_content": state.get("current_content")}

    def _route_after_model(self, state: CleanerState) -> str:
        if state.get("final_content"):
            return "end"

        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"

        return "end"

    def _update_after_tool(self, state: CleanerState) -> dict[str, Any]:
        last_message = state["messages"][-1]
        if not isinstance(last_message, ToolMessage):
            return {}

        if last_message.name not in self.processing_tools_by_name:
            return {
                "cocktail_id": state["cocktail_id"],
                "cocktail_payload": state["cocktail_payload"],
                "current_content": state["current_content"],
                "completed_tools": list(state["completed_tools"]),
                "final_content": state["current_content"],
            }

        completed_tools = list(state["completed_tools"])
        updates: dict[str, Any] = {
            "cocktail_id": state["cocktail_id"],
            "cocktail_payload": state["cocktail_payload"],
            "current_content": state["current_content"],
            "completed_tools": completed_tools,
        }

        if last_message.name:
            updates["completed_tools"].append(last_message.name)

        if last_message.name == "get_cocktail":
            updates["cocktail_payload"] = (
                json.loads(last_message.content) if isinstance(last_message.content, str) else last_message.content
            )
            updates["current_content"] = ""
        else:
            updates["current_content"] = self._extract_plain_text(last_message.content) or state["current_content"]
            if (
                last_message.name is not None
                and state["completed_tools"]
                and state["completed_tools"][-1] == last_message.name
                and state["current_content"] == updates["current_content"]
            ):
                updates["final_content"] = updates["current_content"]
                return updates

        if self._processing_tool_call_count(updates["completed_tools"]) > self._MAX_TOOL_ITERATIONS:
            raise RuntimeError("LLM cleaning exceeded the maximum number of tool iterations.")

        updates["messages"] = [
            HumanMessage(
                content=build_extraction_stepped_user_prompt(
                    updates["cocktail_id"],
                    updates.get("cocktail_payload"),
                    updates["current_content"],
                    updates["completed_tools"],
                )
            )
        ]
        return updates

    def _route_after_tool(self, state: CleanerState) -> str:
        if state.get("final_content"):
            return "end"

        return "model"

    def _processing_tool_call_count(self, completed_tools: list[str]) -> int:
        return sum(1 for tool_name in completed_tools if tool_name in self.processing_tools_by_name)

    def _extract_plain_text(self, result_content: object) -> str | None:
        if result_content is None:
            return None

        if isinstance(result_content, str):
            return result_content.strip()

        if isinstance(result_content, list):
            text_parts: list[str] = []
            for item in result_content:
                if isinstance(item, str):
                    text_parts.append(item)
                    continue

                if isinstance(item, dict):
                    text_value = item.get("text")
                    if isinstance(text_value, str):
                        text_parts.append(text_value)

            plain_text = "\n".join(part.strip() for part in text_parts if part and part.strip())
            return plain_text or None

        return str(result_content)

    def _build_mcp_connection(self) -> Connection:
        transport = self.app_options.llm_mcp_transport

        if transport == "stdio":
            raise RuntimeError(
                "MCP stdio transport is not supported by the current extraction agent configuration. "
                "Configure a URL-based transport or add stdio command/args settings."
            )

        if transport == "sse":
            return SSEConnection(url=self.app_options.llm_mcp_url, transport="sse")

        if transport == "websocket":
            return WebsocketConnection(url=self.app_options.llm_mcp_url, transport="websocket")

        return StreamableHttpConnection(url=self.app_options.llm_mcp_url, transport="streamable_http")

    async def _initialize_mcp_agent(self):
        """Asynchronously load tools from the MCP server and bind them to the model."""
        if self.tool_enabled_llm is not None and self.cleaning_graph is not None:
            return

        connection = self._build_mcp_connection()
        client = MultiServerMCPClient({"content_tools": connection})

        # Fetch tools defined on the MCP server
        mcp_tools = await client.get_tools()
        mcp_tools_by_name = {tool.name: tool for tool in mcp_tools}

        self.processing_tools_by_name = {
            tool_name: tool
            for tool_name, tool in mcp_tools_by_name.items()  # if tool_name != self.fetch_tool.name
        }
        if not self.processing_tools_by_name:
            raise RuntimeError("MCP server does not expose any processing tools beyond get_cocktail.")

        processing_tools = list(self.processing_tools_by_name.values())
        self.tool_enabled_llm = self.llm.bind_tools(processing_tools, tool_choice="any")

        workflow = StateGraph(CleanerState)
        workflow.add_node("model", self._model_node)
        workflow.add_node("tools", ToolNode(processing_tools))
        workflow.add_node("update_after_tool", self._update_after_tool)
        workflow.add_edge(START, "model")
        workflow.add_conditional_edges("model", self._route_after_model, {"tools": "tools", "end": END})
        workflow.add_edge("tools", "update_after_tool")
        workflow.add_conditional_edges("update_after_tool", self._route_after_tool, {"model": "model", "end": END})
        self.cleaning_graph = workflow.compile()
