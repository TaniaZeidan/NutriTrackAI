"""Cooking assistant tool."""
from __future__ import annotations

import csv
from typing import Dict, List

from config import RAW_DATA_DIR
from core.schemas import MealItem, PlanMeal, Step


def _load_dataset() -> List[Dict[str, str]]:
    with (RAW_DATA_DIR / "recipes_sample.csv").open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _find_recipe(query: str) -> Dict[str, str]:
    data = _load_dataset()
    query_lower = query.lower()
    for row in data:
        if query_lower in row["title"].lower():
            return row
    for row in data:
        if query_lower in row["ingredients"].lower():
            return row
    raise ValueError(f"Recipe not found for query: {query}")


def recipe_steps(query: str, servings: int = 1) -> Dict[str, List[Step]]:
    row = _find_recipe(query)
    steps_raw = row["steps"].split(".")
    parsed: List[Step] = []
    for idx, step in enumerate(filter(None, [s.strip() for s in steps_raw]), start=1):
        parsed.append(
            Step(
                idx=idx,
                instruction=step,
                estimated_minutes=5,
                tips=["Read the entire step before starting."],
                substitutions=["Swap similar vegetables if needed."],
            )
        )
    base_servings = int(float(row.get("servings", 1))) or 1
    scale = servings / base_servings
    ingredients = []
    for ingredient in row["ingredients"].split("|"):
        ingredients.append(
            MealItem(
                name=ingredient.title(),
                quantity=scale,
                unit="serving",
                calories=float(row["per_serving_calories"]) * scale,
                protein_g=float(row["protein_g"]) * scale,
                carb_g=float(row["carb_g"]) * scale,
                fat_g=float(row["fat_g"]) * scale,
                estimated=True,
            )
        )
    meal = PlanMeal(name=row["title"], meal_type="dinner", items=ingredients, notes=row.get("tags"))
    return {"steps": parsed, "meal": meal}


__all__ = ["recipe_steps"]
