"""Tool registry for the agent."""
from __future__ import annotations

from typing import List

try:  # pragma: no cover
    from langchain.tools import Tool
except Exception:  # pragma: no cover
    Tool = None  # type: ignore

from .calorie_tracker import log_meal
from .calorie_calculator import get_personalized_targets
from .meal_planner import generate_plan
from .grocery_list import build_list_from_plan
from .cooking_assistant import recipe_steps
from .ingredient_weights import estimate_ingredient_grams


def get_tools() -> List[object]:
    """Return tool definitions for the agent."""
    if Tool is None:
        return [
            {"name": "calorie_tracker", "func": log_meal},
            {"name": "calorie_calculator", "func": get_personalized_targets},
            {"name": "meal_planner", "func": generate_plan},
            {"name": "grocery_list", "func": build_list_from_plan},
            {"name": "cooking_assistant", "func": recipe_steps},
            {"name": "ingredient_weights", "func": estimate_ingredient_grams},
        ]
    
    return [
        Tool(
            name="calorie_tracker",
            func=log_meal,
            description="Log meals and compute macros from food descriptions"
        ),
        Tool(
            name="calorie_calculator",
            func=get_personalized_targets,
            description=(
                "Calculate personalized calorie and macro targets based on "
                "body metrics, activity level, and fitness goals"
            )
        ),
        Tool(
            name="meal_planner",
            func=generate_plan,
            description="Generate balanced weekly meal plans matching macro targets"
        ),
        Tool(
            name="grocery_list",
            func=build_list_from_plan,
            description="Aggregate and categorize grocery items from meal plans"
        ),
        Tool(
            name="cooking_assistant",
            func=recipe_steps,
            description="Provide detailed cooking steps and ingredient lists for recipes"
        ),
        Tool(
            name="ingredient_weights",
            func=estimate_ingredient_grams,
            description=(
                "Estimate ingredient amounts in grams based on total calories "
                "and nutrition references"
            )
        ),
    ]


__all__ = ["get_tools"]