"""Meal planner tool."""
from __future__ import annotations

import csv
from datetime import date, timedelta
from typing import Dict, List

from config import RAW_DATA_DIR
from core.schemas import MacroTargets, MealItem, PlanDay, PlanMeal
from core.utils import clamp_calories


MEAL_PLAN_FILE = RAW_DATA_DIR / "healthy_meal_plans.csv"


def _load_meals() -> List[Dict[str, str]]:
    with MEAL_PLAN_FILE.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _bool(value: str | None) -> bool:
    return str(value or "").strip() in {"1", "true", "True"}


def _filter_meals(meals: List[Dict[str, str]], targets: MacroTargets) -> List[Dict[str, str]]:
    def _meal_satisfies(meal: Dict[str, str]) -> bool:
        tags = []
        for field, label in [
            ("vegan", "vegan"),
            ("vegetarian", "vegetarian"),
            ("keto", "keto"),
            ("paleo", "paleo"),
            ("gluten_free", "gluten-free"),
            ("mediterranean", "mediterranean"),
            ("is_healthy", "healthy"),
        ]:
            if _bool(meal.get(field)):
                tags.append(label)
        meal["tags"] = ",".join(tags)

        if targets.diet_tags and not any(tag in tags for tag in targets.diet_tags):
            return False
        if targets.exclusions:
            name = meal.get("meal_name", "").lower()
            for exclusion in targets.exclusions:
                if exclusion and exclusion.lower() in name:
                    return False
        return True

    filtered = [meal for meal in meals if _meal_satisfies(meal)]
    return filtered or meals


def _build_plan_meal(meal: Dict[str, str], meal_type: str) -> PlanMeal:
    calories = float(meal.get("calories", 0.0) or 0.0) * 900
    protein = float(meal.get("protein", 0.0) or 0.0) * 100
    fat = float(meal.get("fat", 0.0) or 0.0) * 100
    carbs = float(meal.get("carbs", 0.0) or 0.0) * 100
    item = MealItem(
        name=meal.get("meal_name", "Meal"),
        quantity=1,
        unit="serving",
        calories=calories,
        protein_g=protein,
        carb_g=carbs,
        fat_g=fat,
        estimated=True,
    )
    return PlanMeal(
        name=meal.get("meal_name", "Meal"),
        meal_type=meal_type,
        items=[item],
        notes=meal.get("tags"),
    )


def generate_plan(targets: MacroTargets, days: int = 7) -> List[PlanDay]:
    meals = _load_meals()
    filtered = _filter_meals(meals, targets)
    plan_days: List[PlanDay] = []
    pointer = 0
    meal_types = ["breakfast", "lunch", "dinner"]
    if targets.meals_per_day == 4:
        meal_types.append("snack")
    for offset in range(days):
        meals_for_day: List[PlanMeal] = []
        for idx in range(targets.meals_per_day):
            meal = filtered[pointer % len(filtered)]
            meal_type = meal_types[idx % len(meal_types)]
            meals_for_day.append(_build_plan_meal(meal, meal_type))
            pointer += 1
        plan_day = PlanDay(date=date.today() + timedelta(days=offset), meals=meals_for_day)
        totals = plan_day.totals()
        if totals["calories"] < targets.calories * 0.8:
            scale = clamp_calories(targets.calories) / max(totals["calories"], 1)
            scaled_meals = []
            for meal in meals_for_day:
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
