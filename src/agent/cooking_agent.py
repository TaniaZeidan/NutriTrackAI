"""Cooking Assistant -- thin wrapper around the multi-agent LangGraph."""
from __future__ import annotations

from typing import Optional

from agent.orchestrator import NutriTrackAgent
from core.llm import GeminiClient


class CookingAgent:
    """High-level cooking assistant used by the Streamlit Cooking page.

    All queries go through the LangGraph multi-agent graph, which routes
    cooking questions to the specialised cooking agent automatically.
    """

    def __init__(self, llm: Optional[GeminiClient] = None) -> None:
        self.agent = NutriTrackAgent()

    def chat(self, user_input: str, servings: int = 2) -> str:
        servings_int = max(1, int(servings) if isinstance(servings, (int, float)) else 2)
        prompt = (
            f"(The user wants help for {servings_int} serving(s).)\n\n"
            f"{user_input}"
        )
        return self.agent.run(prompt)


__all__ = ["CookingAgent"]
