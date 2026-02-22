"""Agent orchestration using LangGraph."""
from __future__ import annotations

import uuid
from typing import Annotated, Any, List, Optional

from typing_extensions import TypedDict

# LangGraph — guarded so the app degrades gracefully when not installed
try:  # pragma: no cover
    from langgraph.graph import StateGraph, START, END
    from langgraph.prebuilt import ToolNode, tools_condition
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.graph.message import add_messages

    _LANGGRAPH_AVAILABLE = True
except Exception:  # pragma: no cover
    _LANGGRAPH_AVAILABLE = False

# langchain-core messages — guarded for the same reason
try:  # pragma: no cover
    from langchain_core.messages import HumanMessage, SystemMessage

    _LC_CORE_AVAILABLE = True
except Exception:  # pragma: no cover
    _LC_CORE_AVAILABLE = False

# LLM — guarded
ChatGoogleGenerativeAI = None
try:  # pragma: no cover
    from langchain_google_genai import ChatGoogleGenerativeAI as _GoogleChat  # type: ignore

    ChatGoogleGenerativeAI = _GoogleChat
except Exception:  # pragma: no cover
    ChatGoogleGenerativeAI = None  # type: ignore


from config import CHAT_MODEL
from core.llm import GeminiClient
from core.memory import ConversationMemory, PreferenceMemory
from core.prompts import SYSTEM_PROMPT


class NutriTrackAgent:
    """High-level facade for executing agent workflows via a LangGraph StateGraph."""

    def __init__(
        self,
        tools: List[Any],
        gemini: GeminiClient | None = None,
        conversation: ConversationMemory | None = None,
        preferences: PreferenceMemory | None = None,
    ) -> None:
        self.tools = tools
        self.gemini = gemini or GeminiClient()
        self.conversation = conversation or ConversationMemory()
        self.preferences = preferences or PreferenceMemory()
        # One UUID per agent instance — MemorySaver uses it as the thread key so
        # conversation history accumulates across run() calls, just like the old
        # ConversationBufferMemory did.
        self._thread_id = str(uuid.uuid4())
        self._graph = self._build_graph()

    def _build_graph(self):  # pragma: no cover - mostly integration logic
        """Build the LangGraph ReAct graph. Returns None on failure (triggers fallback)."""
        if not (_LANGGRAPH_AVAILABLE and _LC_CORE_AVAILABLE and ChatGoogleGenerativeAI):
            return None
        try:
            # ------------------------------------------------------------------ #
            # State schema                                                         #
            # add_messages is a LangGraph reducer that appends new messages        #
            # instead of overwriting — the direct replacement for                  #
            # ConversationBufferMemory's append behaviour.                         #
            # ------------------------------------------------------------------ #
            class AgentState(TypedDict):
                messages: Annotated[list, add_messages]

            # LLM with tools bound — the model now emits structured tool_calls
            # instead of ReAct-style JSON strings that had to be parsed.
            llm = ChatGoogleGenerativeAI(
                model=CHAT_MODEL,
                convert_system_message_to_human=True,  # Gemini has no system role
            ).bind_tools(self.tools)

            # ------------------------------------------------------------------ #
            # Nodes                                                                #
            # ------------------------------------------------------------------ #
            def call_model(state) -> dict:
                """Invoke the LLM, prepending the system prompt on every turn."""
                messages = list(state["messages"])
                # Inject system prompt if it isn't already the first message.
                if not messages or not isinstance(messages[0], SystemMessage):
                    messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
                response = llm.invoke(messages)
                return {"messages": [response]}

            # ToolNode dispatches tool_calls from the AIMessage, runs each tool,
            # and returns ToolMessage results — replacing handle_parsing_errors.
            tool_node = ToolNode(self.tools)

            # ------------------------------------------------------------------ #
            # Graph: START → call_model ⇄ tools → END                            #
            # tools_condition routes to "tools" when tool_calls are present,      #
            # otherwise routes to END.                                             #
            # ------------------------------------------------------------------ #
            builder = StateGraph(AgentState)
            builder.add_node("call_model", call_model)
            builder.add_node("tools", tool_node)
            builder.add_edge(START, "call_model")
            builder.add_conditional_edges("call_model", tools_condition)
            builder.add_edge("tools", "call_model")  # loop back for multi-hop reasoning
            return builder.compile(checkpointer=MemorySaver())

        except Exception as exc:
            print(f"Failed to initialize LangGraph agent, falling back to GeminiClient: {exc}")
            return None

    def run(self, prompt: str) -> str:
        """Execute the agent against a prompt."""
        self.conversation.add_turn(prompt, "")

        if self._graph is not None:
            try:
                config = {"configurable": {"thread_id": self._thread_id}}
                result = self._graph.invoke(
                    {"messages": [HumanMessage(content=prompt)]},
                    config=config,
                )
                ai_msg = result["messages"][-1]
                response = ai_msg.content if hasattr(ai_msg, "content") else str(ai_msg)
            except Exception as exc:
                print(f"LangGraph invocation failed, falling back to GeminiClient: {exc}")
                response = self.gemini.generate_text(prompt)
        else:
            response = self.gemini.generate_text(prompt)

        self.conversation.buffer[-1] = (prompt, response)
        return response


__all__ = ["NutriTrackAgent"]
