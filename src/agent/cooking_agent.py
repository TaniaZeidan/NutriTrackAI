"""Cooking Assistant Agent powered by the NutriTrackAI LangChain agent."""
from __future__ import annotations

from typing import Optional
import re

from agent.orchestrator import NutriTrackAgent
from tools.tool_registry import get_tools
from core.llm import GeminiClient  # kept for type hint / backward-compatibility
from core.prompts import COOKING_PROMPT
from tools.cooking_assistant import grounded_cooking_response


def _is_instruction_query(text: str) -> bool:
    """Lightweight heuristic to detect recipe/instruction requests."""
    lowered = text.lower()
    keywords = [
        "how to",
        "how do i",
        "make",
        "cook",
        "prepare",
        "recipe",
        "steps",
        "instructions",
    ]
    return any(kw in lowered for kw in keywords) or bool(
        re.search(r"\b(recipe for|how do i (cook|make)|how to make)\b", lowered)
    )


class CookingAgent:
    """High-level cooking assistant that delegates to the NutriTrackAI agent.

    This class is what the Streamlit Cooking Assistant page uses.
    Internally it builds a NutriTrackAgent with the registered tools
    (RAG recipe search, ingredient weight estimation, macro targets).
    """

    def __init__(self, llm: Optional[GeminiClient] = None) -> None:
        # llm parameter is kept for backward compatibility but is not required,
        # since NutriTrackAgent manages its own Gemini client.
        tools = get_tools()
        # We ignore the external llm and let NutriTrackAgent construct its own
        # GeminiClient so configuration is centralized in core.llm/config.py.
        self.agent = NutriTrackAgent(tools=tools)

    def chat(self, user_input: str, servings: int = 2) -> str:
        """Generate a response for the given user input.

        The prompt we send to the agent explains how to use the tools.
        The LangChain agent is free to:
        - Call the cooking_rag tool to fetch recipes and macros from the RAG index.
        - Call the ingredient_weights tool to estimate grams per ingredient.
        - Call the macro_targets tool if the user asks for daily calorie/macro needs.
        """
        if isinstance(servings, (int, float)):
            servings_int = int(servings)
        else:
            servings_int = 2
        servings_int = max(1, servings_int)

        # Fast path: if the user is clearly asking for cooking instructions or a recipe,
        # call the grounded cooking RAG tool directly to avoid the agent skipping it.
        if _is_instruction_query(user_input):
            try:
                rag_result = grounded_cooking_response(user_input, servings=servings_int)
                if isinstance(rag_result, dict) and rag_result.get("answer"):
                    return str(rag_result["answer"])
            except Exception as exc:  # pragma: no cover - resilience around tool errors
                print(f"Direct cooking_rag call failed, falling back to agent: {exc}")

        tool_instructions = (
            "You are NutriTrackAI, an expert cooking and nutrition assistant.\n"
            f"The user currently wants help for approximately {servings_int} serving(s).\n\n"
            "CRITICAL ANTI-HALLUCINATION RULES:\n"
            "1. NEVER invent recipes, ingredients, or cooking steps\n"
            "2. ALWAYS use the cooking_rag tool for ANY recipe-related query\n"
            "3. ONLY present information returned by the tools - do not add creative details\n"
            "4. If a recipe is not found in the database, say so explicitly\n\n"
            "TOOLS USAGE RULES:\n"
            "- `cooking_rag`: REQUIRED for ANY recipe, cooking instructions, or ingredient questions. "
            "Input JSON: {\"query\": \"<user question>\", \"servings\": <int>}.\n"
            "- `ingredient_weights`: When they ask how many grams of each ingredient to use or how to scale. "
            "Input JSON: {\"ingredients\": [...], \"calories_per_serving\": <float>, \"servings\": <int>}.\n"
            "- `macro_targets`: When they want daily calorie or macro needs (BMR/TDEE). "
            "Input JSON: {\"weight_kg\": <float>, \"height_cm\": <float>, \"age\": <int>, "
            "\"sex\": \"male|female\", \"activity_level\": \"sedentary|light|moderate|active|very_active\", "
            "\"goal\": \"lose_fat|maintain|gain_muscle\"}.\n\n"
            "Workflow: Call the appropriate tool → Present the tool's response in natural language → Never add information not provided by tools."
        )

        prompt = f"{tool_instructions}\n\n{COOKING_PROMPT}\n\nUser question: {user_input}"

        # Delegate to the LangChain-powered agent. If LangChain or the Gemini
        # chat wrapper is not available, NutriTrackAgent will fall back to a
        # direct GeminiClient completion.
        response = self.agent.run(prompt)
        return response


__all__ = ["CookingAgent"]
