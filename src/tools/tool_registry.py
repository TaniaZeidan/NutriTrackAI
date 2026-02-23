"""Tool registry for the NutriTrackAI agent."""
from __future__ import annotations

import json
from typing import Any, List

try:  # pragma: no cover
    from langchain_core.tools import Tool
except Exception:  # pragma: no cover
    Tool = None  # type: ignore

from core.rag import build_index
from .calorie_calculator import get_personalized_targets
from .cooking_assistant import grounded_cooking_response
from .ingredient_weights import estimate_ingredient_grams


def _tool_cooking_rag(payload: str) -> str:
    """
    Use the recipe RAG index to answer cooking questions.

    Payload (preferred): JSON string
      {"query": "user question about recipes or cooking", "servings": 2}

    If JSON parsing fails, the payload is treated as plain text and
    2 servings are assumed.

    Returns: human-friendly markdown answer (steps, macros, etc.).
    """
    try:
        data = json.loads(payload)
        if isinstance(data, dict):
            query = str(data.get("query", ""))
            servings = int(data.get("servings", 2))
        else:
            query = str(payload)
            servings = 2
    except Exception:
        query = str(payload)
        servings = 2

    build_index()
    result = grounded_cooking_response(query=query, servings=servings)
    if isinstance(result, dict) and "answer" in result:
        return str(result["answer"])
    return "I could not generate a recipe answer right now."


def _tool_ingredient_weights(payload: str) -> str:
    """
    Estimate grams per ingredient using the nutrition reference table.

    Payload: JSON string
      {"ingredients": [...], "calories_per_serving": 500, "servings": 2}

    Returns: human-friendly list of each ingredient with grams and calories.
    """
    try:
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("Payload must be a JSON object")

        ingredients = [str(x) for x in data.get("ingredients", [])]
        calories_per_serving = float(data.get("calories_per_serving", 0))
        servings = int(data.get("servings", 1))

        estimates = estimate_ingredient_grams(
            ingredients=ingredients,
            calories_per_serving=calories_per_serving,
            servings=servings,
        )

        if not estimates:
            return "I could not estimate ingredient amounts from the given data."

        lines = ["Here are approximate ingredient amounts:"]
        for item in estimates:
            name = item.get("ingredient", "ingredient")
            grams_total = float(item.get("grams_total", 0))
            grams_per_serving = float(item.get("grams_per_serving", 0))
            cals = float(item.get("calories_per_serving", 0))
            lines.append(
                f"- {name}: ~{grams_total:.1f} g total "
                f"({grams_per_serving:.1f} g per serving, ~{cals:.0f} kcal/serving)"
            )

        return "\n".join(lines)

    except Exception as exc:
        return f"Error parsing ingredient_weights payload: {exc!r}"


def _tool_macro_targets(payload: str) -> str:
    """
    Calculate personalized daily calories and macro targets.

    Payload: JSON string with:
      {"weight_kg": 63, "height_cm": 165, "age": 22,
       "sex": "female", "activity_level": "moderate",
       "goal": "lose_fat"}

    Returns: friendly explanation of BMR, TDEE, and macro grams.
    """
    try:
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("Payload must be a JSON object")

        weight_kg = float(data["weight_kg"])
        height_cm = float(data["height_cm"])
        age = int(data["age"])
        sex = str(data["sex"])
        activity_level = str(data["activity_level"])
        goal = str(data["goal"])

        targets = get_personalized_targets(
            weight_kg=weight_kg,
            height_cm=height_cm,
            age=age,
            sex=sex,  # type: ignore[arg-type]
            activity_level=activity_level,  # type: ignore[arg-type]
            goal=goal,  # type: ignore[arg-type]
        )

        bmr = targets["bmr"]
        tdee = targets["tdee"]
        target_cals = targets["target_calories"]
        p = targets["protein_g"]
        c = targets["carb_g"]
        f = targets["fat_g"]

        return (
            "Here are your estimated daily energy and macro targets:\n"
            f"- Basal Metabolic Rate (BMR): {bmr:.0f} kcal/day\n"
            f"- Maintenance calories (TDEE): {tdee:.0f} kcal/day\n"
            f"- Goal calories: {target_cals:.0f} kcal/day\n"
            f"- Protein: {p:.0f} g/day\n"
            f"- Carbohydrates: {c:.0f} g/day\n"
            f"- Fats: {f:.0f} g/day\n\n"
            "Use these as a starting point and adjust based on your progress."
        )

    except Exception as exc:
        return f"Error parsing macro_targets payload: {exc!r}"


def get_tools() -> List[Any]:
    """Return the list of tools for the NutriTrackAI LangChain agent."""
    if Tool is None:
        # Fallback when LangChain isn't installed; not used in the Streamlit agent.
        return [
            {"name": "cooking_rag", "func": _tool_cooking_rag},
            {"name": "ingredient_weights", "func": _tool_ingredient_weights},
            {"name": "macro_targets", "func": _tool_macro_targets},
        ]

    return [
        Tool(
            name="cooking_rag",
            func=_tool_cooking_rag,
            description=(
                "Answer cooking and recipe questions using the NutriTrackAI "
                "recipe RAG index. Input: JSON string with 'query' and optional "
                "'servings'."
            ),
        ),
        Tool(
            name="ingredient_weights",
            func=_tool_ingredient_weights,
            description=(
                "Estimate grams for each ingredient. Input: JSON string with "
                "'ingredients', 'calories_per_serving', and optional 'servings'."
            ),
        ),
        Tool(
            name="macro_targets",
            func=_tool_macro_targets,
            description=(
                "Calculate personalized daily calorie and macro targets. "
                "Input: JSON string with body stats and goal."
            ),
        ),
    ]


__all__ = ["get_tools"]
