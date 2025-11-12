"""Meal planner tool."""
from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List

from ..core.schemas import MacroTargets, MealItem, PlanDay, PlanMeal
from ..core.utils import clamp_calories
from ..config import RAW_DATA_DIR


def _load_recipes() -> List[Dict[str, str]]:
    path = RAW_DATA_DIR / "recipes_sample.csv"
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _filter_recipes(recipes: List[Dict[str, str]], targets: MacroTargets) -> List[Dict[str, str]]:
    filtered = []
    for recipe in recipes:
        if targets.diet_tags:
            if not any(tag.lower() in recipe.get("tags", "").lower() for tag in targets.diet_tags):
                continue
        exclusion_hit = False
        for exclusion in targets.exclusions:
            if exclusion and exclusion.lower() in recipe.get("ingredients", "").lower():
                exclusion_hit = True
                break
        if exclusion_hit:
            continue
        filtered.append(recipe)
    return filtered or recipes


def _build_plan_meal(recipe: Dict[str, str], meal_type: str) -> PlanMeal:
    item = MealItem(
        name=recipe["title"],
        quantity=1,
        unit="serving",
        calories=float(recipe["per_serving_calories"]),
        protein_g=float(recipe["protein_g"]),
        carb_g=float(recipe["carb_g"]),
        fat_g=float(recipe["fat_g"]),
        estimated=False,
    )
    return PlanMeal(name=recipe["title"], meal_type=meal_type, items=[item], notes=recipe.get("tags"))


def generate_plan(targets: MacroTargets, days: int = 7) -> List[PlanDay]:
    recipes = _load_recipes()
    filtered = _filter_recipes(recipes, targets)
    plan_days: List[PlanDay] = []
    pointer = 0
    meal_types = ["breakfast", "lunch", "dinner"]
    if targets.meals_per_day == 4:
        meal_types.append("snack")
    for offset in range(days):
        meals: List[PlanMeal] = []
        for idx in range(targets.meals_per_day):
            recipe = filtered[pointer % len(filtered)]
            meal_type = meal_types[idx % len(meal_types)]
            meals.append(_build_plan_meal(recipe, meal_type))
            pointer += 1
        plan_day = PlanDay(date=date.today() + timedelta(days=offset), meals=meals)
        totals = plan_day.totals()
        if totals["calories"] < targets.calories * 0.8:
            scale = clamp_calories(targets.calories) / max(totals["calories"], 1)
            scaled_meals = []
            for meal in meals:
                scaled_items = [
                    MealItem(
                        name=item.name,
                        quantity=item.quantity * scale,
                        unit=item.unit,
                        calories=item.calories * scale,
                        protein_g=item.protein_g * scale,
                        carb_g=item.carb_g * scale,
                        fat_g=item.fat_g * scale,
                        estimated=True,
                    )
                    for item in meal.items
                ]
                scaled_meals.append(
                    PlanMeal(name=meal.name, meal_type=meal.meal_type, items=scaled_items, notes=meal.notes)
                )
            plan_day = PlanDay(date=plan_day.date, meals=scaled_meals)
        plan_days.append(plan_day)
    return plan_days


__all__ = ["generate_plan"]
