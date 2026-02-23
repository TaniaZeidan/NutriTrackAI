"""Multi-agent orchestration using LangGraph.

Graph topology:
    START -> router -> [route_by_type] -> cooking_agent <-> cooking_tools -> END
                                       -> nutrition_agent <-> nutrition_tools -> END

Three agent roles:
    1. Router       – classifies queries via Structured Output Mode (Pydantic)
    2. CookingAgent – recipes, ingredients, cooking instructions
    3. NutritionAgent – calorie targets, macros, meal planning
"""
from __future__ import annotations

import uuid
from typing import Any, List, Optional

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from config import CHAT_MODEL, get_google_api_key
from core.llm import GeminiClient
from core.memory import ConversationMemory, PreferenceMemory
from core.schemas import NutriTrackState, RouterDecision
from core.prompts import (
    ROUTER_PROMPT,
    COOKING_AGENT_PROMPT,
    NUTRITION_AGENT_PROMPT,
)
from tools.tool_registry import get_cooking_tools, get_nutrition_tools


CONFIDENCE_THRESHOLD = 0.5


def _make_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=CHAT_MODEL,
        google_api_key=get_google_api_key(),
        convert_system_message_to_human=True,
    )


# ── Node functions ───────────────────────────────────────────────────────────

def router_node(state: NutriTrackState) -> dict:
    """Classify the user query using Structured Output Mode."""
    llm = _make_llm().with_structured_output(RouterDecision)
    messages = [
        SystemMessage(content=ROUTER_PROMPT),
        *state.messages,
    ]
    decision: RouterDecision = llm.invoke(messages)
    return {
        "query_type": decision.query_type,
        "confidence": decision.confidence,
        "current_agent": decision.query_type,
    }


def cooking_agent_node(state: NutriTrackState) -> dict:
    """Invoke the cooking specialist LLM with cooking tools."""
    cooking_tools = get_cooking_tools()
    llm = _make_llm().bind_tools(cooking_tools)
    messages = [
        SystemMessage(content=COOKING_AGENT_PROMPT),
        *state.messages,
    ]
    response = llm.invoke(messages)
    return {
        "messages": [response],
        "tool_calls_count": state.tool_calls_count + (
            len(response.tool_calls) if hasattr(response, "tool_calls") and response.tool_calls else 0
        ),
    }


def nutrition_agent_node(state: NutriTrackState) -> dict:
    """Invoke the nutrition specialist LLM with nutrition tools."""
    nutrition_tools = get_nutrition_tools()
    llm = _make_llm().bind_tools(nutrition_tools)
    messages = [
        SystemMessage(content=NUTRITION_AGENT_PROMPT),
        *state.messages,
    ]
    response = llm.invoke(messages)
    return {
        "messages": [response],
        "tool_calls_count": state.tool_calls_count + (
            len(response.tool_calls) if hasattr(response, "tool_calls") and response.tool_calls else 0
        ),
    }


# ── Conditional routing ──────────────────────────────────────────────────────

def route_by_type(state: NutriTrackState) -> str:
    """Route to the appropriate specialist based on the router's classification.

    If confidence is below the threshold, fall back to the cooking agent
    (the most general-purpose specialist).
    """
    if state.confidence < CONFIDENCE_THRESHOLD:
        return "cooking_agent"
    if state.query_type == "nutrition":
        return "nutrition_agent"
    return "cooking_agent"


# ── Graph builder ────────────────────────────────────────────────────────────

def build_graph():
    """Construct and compile the multi-agent LangGraph."""
    cooking_tools = get_cooking_tools()
    nutrition_tools = get_nutrition_tools()

    builder = StateGraph(NutriTrackState)

    builder.add_node("router", router_node)
    builder.add_node("cooking_agent", cooking_agent_node)
    builder.add_node("cooking_tools", ToolNode(cooking_tools))
    builder.add_node("nutrition_agent", nutrition_agent_node)
    builder.add_node("nutrition_tools", ToolNode(nutrition_tools))

    builder.add_edge(START, "router")
    builder.add_conditional_edges(
        "router",
        route_by_type,
        {"cooking_agent": "cooking_agent", "nutrition_agent": "nutrition_agent"},
    )

    builder.add_conditional_edges(
        "cooking_agent",
        tools_condition,
        {"tools": "cooking_tools", END: END},
    )
    builder.add_edge("cooking_tools", "cooking_agent")

    builder.add_conditional_edges(
        "nutrition_agent",
        tools_condition,
        {"tools": "nutrition_tools", END: END},
    )
    builder.add_edge("nutrition_tools", "nutrition_agent")

    return builder.compile(checkpointer=MemorySaver())


# ── Public facade ────────────────────────────────────────────────────────────

class NutriTrackAgent:
    """High-level facade used by Streamlit pages and the CLI demo."""

    def __init__(
        self,
        tools: List[Any] | None = None,
        gemini: GeminiClient | None = None,
        conversation: ConversationMemory | None = None,
        preferences: PreferenceMemory | None = None,
    ) -> None:
        self.gemini = gemini or GeminiClient()
        self.conversation = conversation or ConversationMemory()
        self.preferences = preferences or PreferenceMemory()
        self._thread_id = str(uuid.uuid4())
        self._graph = build_graph()

    def run(self, prompt: str) -> str:
        """Send a user message through the multi-agent graph."""
        self.conversation.add_turn(prompt, "")

        try:
            config = {"configurable": {"thread_id": self._thread_id}}
            result = self._graph.invoke(
                {"messages": [HumanMessage(content=prompt)]},
                config=config,
            )
            ai_msg = result["messages"][-1]
            response = ai_msg.content if hasattr(ai_msg, "content") else str(ai_msg)
        except Exception as exc:
            exc_str = str(exc).lower()
            print(f"LangGraph invocation failed: {exc}")
            if "429" in str(exc) or "resourceexhausted" in exc_str or "quota" in exc_str:
                response = (
                    "The Gemini API rate limit has been reached. The free tier allows "
                    "only ~20 requests/day for gemini-2.5-flash, and each query uses "
                    "2-3 API calls internally.\n\n"
                    "Please wait a minute (for per-minute limits) or try again tomorrow "
                    "(for daily limits). You can also create a new Google Cloud project "
                    "at https://aistudio.google.com to get a fresh quota."
                )
            else:
                response = self.gemini.generate_text(prompt)

        self.conversation.buffer[-1] = (prompt, response)
        return response


__all__ = ["NutriTrackAgent", "build_graph"]
