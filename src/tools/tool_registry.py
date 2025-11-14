"""Tool registry for the agent."""
from __future__ import annotations

from typing import List

try:  # pragma: no cover
    from langchain.tools import Tool
except Exception:  # pragma: no cover
    Tool = None  # type: ignore

from .calorie_tracker import log_meal
from .meal_planner import generate_plan
from .grocery_list import build_list_from_plan
from .cooking_assistant import recipe_steps
from .ingredient_weights import estimate_ingredient_grams


def get_tools() -> List[object]:
    """Return tool definitions for the agent."""
    if Tool is None:
        return [
            {"name": "calorie_tracker", "func": log_meal},
            {"name": "meal_planner", "func": generate_plan},
            {"name": "grocery_list", "func": build_list_from_plan},
            {"name": "cooking_assistant", "func": recipe_steps},
            {"name": "ingredient_weights", "func": estimate_ingredient_grams},
        ]
    return [
        Tool(name="calorie_tracker", func=log_meal, description="Log meals and compute macros"),
        Tool(name="meal_planner", func=generate_plan, description="Generate weekly meal plans"),
        Tool(name="grocery_list", func=build_list_from_plan, description="Aggregate grocery items"),
        Tool(name="cooking_assistant", func=recipe_steps, description="Provide cooking steps"),
        Tool(
            name="ingredient_weights",
            func=estimate_ingredient_grams,
            description="Estimate grams per ingredient using nutrition references",
        ),
    ]


__all__ = ["get_tools"]
