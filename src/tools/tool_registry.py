"""Tool registry for the NutriTrackAI multi-agent system.

Provides per-agent toolsets so each agent gets its own set of capabilities:
  - Cooking agent:   {cooking_rag, ingredient_weights}
  - Nutrition agent: {macro_targets, meal_planner}
"""
from __future__ import annotations

import json
from typing import Any, List

from langchain_core.tools import Tool

from core.rag import build_index
from .calorie_calculator import get_personalized_targets
from .cooking_assistant import grounded_cooking_response
from .ingredient_weights import estimate_ingredient_grams
from .meal_planner import generate_plan
from core.schemas import MacroTargets


# ── Cooking-agent tools ──────────────────────────────────────────────────────

def _tool_cooking_rag(payload: str) -> str:
    """Search the recipe RAG index for cooking questions.

    Input: JSON string {"query": "<question>", "servings": 2}
    Falls back to treating the payload as plain text if JSON parsing fails.
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
    """Estimate grams per ingredient using the nutrition reference table.

    Input: JSON string {"ingredients": [...], "calories_per_serving": 500, "servings": 2}
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


# ── Nutrition-agent tools ────────────────────────────────────────────────────

def _tool_macro_targets(payload: str) -> str:
    """Calculate personalized daily calories and macro targets.

    Input: JSON string with body stats:
      {"weight_kg": 63, "height_cm": 165, "age": 22,
       "sex": "female", "activity_level": "moderate", "goal": "lose_fat"}
    """
    try:
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("Payload must be a JSON object")

        targets = get_personalized_targets(
            weight_kg=float(data["weight_kg"]),
            height_cm=float(data["height_cm"]),
            age=int(data["age"]),
            sex=str(data["sex"]),  # type: ignore[arg-type]
            activity_level=str(data["activity_level"]),  # type: ignore[arg-type]
            goal=str(data["goal"]),  # type: ignore[arg-type]
        )

        return (
            "Here are your estimated daily energy and macro targets:\n"
            f"- Basal Metabolic Rate (BMR): {targets['bmr']:.0f} kcal/day\n"
            f"- Maintenance calories (TDEE): {targets['tdee']:.0f} kcal/day\n"
            f"- Goal calories: {targets['target_calories']:.0f} kcal/day\n"
            f"- Protein: {targets['protein_g']:.0f} g/day\n"
            f"- Carbohydrates: {targets['carb_g']:.0f} g/day\n"
            f"- Fats: {targets['fat_g']:.0f} g/day\n\n"
            "Use these as a starting point and adjust based on your progress."
        )

    except Exception as exc:
        return f"Error parsing macro_targets payload: {exc!r}"


def _tool_meal_planner(payload: str) -> str:
    """Generate a multi-day meal plan from calorie and macro targets.

    Input: JSON string:
      {"calories": 2000, "protein": 130, "carbs": 220, "fat": 60,
       "days": 7, "meals_per_day": 3, "diet_tags": [], "exclusions": []}
    """
    try:
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("Payload must be a JSON object")

        targets = MacroTargets(
            calories=int(data.get("calories", 2000)),
            protein=int(data.get("protein", 130)),
            carbs=int(data.get("carbs", 220)),
            fat=int(data.get("fat", 60)),
            meals_per_day=int(data.get("meals_per_day", 3)),
            diet_tags=data.get("diet_tags", []),
            exclusions=data.get("exclusions", []),
        )
        days = int(data.get("days", 7))

        plan = generate_plan(targets, days=days)

        lines = [f"Generated a {days}-day meal plan:\n"]
        for day in plan:
            totals = day.totals()
            lines.append(f"**{day.date.strftime('%A, %B %d')}**")
            for meal in day.meals:
                mt = meal.totals
                lines.append(
                    f"  - {meal.meal_type.title()}: {meal.name} "
                    f"({mt['calories']:.0f} kcal | P:{mt['protein_g']:.0f}g "
                    f"C:{mt['carb_g']:.0f}g F:{mt['fat_g']:.0f}g)"
                )
            lines.append(
                f"  Daily total: {totals['calories']:.0f} kcal | "
                f"P:{totals['protein_g']:.0f}g C:{totals['carb_g']:.0f}g "
                f"F:{totals['fat_g']:.0f}g\n"
            )
        return "\n".join(lines)

    except Exception as exc:
        return f"Error generating meal plan: {exc!r}"


# ── Public API ───────────────────────────────────────────────────────────────

def get_cooking_tools() -> List[Tool]:
    """Tools for the Cooking agent: recipe search + ingredient weights."""
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
    ]


def get_nutrition_tools() -> List[Tool]:
    """Tools for the Nutrition agent: macro calculator + meal planner."""
    return [
        Tool(
            name="macro_targets",
            func=_tool_macro_targets,
            description=(
                "Calculate personalized daily calorie and macro targets. "
                "Input: JSON string with body stats and goal."
            ),
        ),
        Tool(
            name="meal_planner",
            func=_tool_meal_planner,
            description=(
                "Generate a multi-day meal plan from calorie and macro targets. "
                "Input: JSON string with calories, protein, carbs, fat, days, "
                "meals_per_day, diet_tags, and exclusions."
            ),
        ),
    ]


def get_tools() -> List[Tool]:
    """All tools combined (backward compatibility)."""
    return get_cooking_tools() + get_nutrition_tools()


__all__ = ["get_tools", "get_cooking_tools", "get_nutrition_tools"]
