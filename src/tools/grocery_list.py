"""Grocery list aggregation tool."""
from __future__ import annotations

import csv
from io import StringIO
from typing import Iterable, List, Tuple

from ..core.schemas import GroceryItem, MealItem, PlanDay, PlanMeal
from ..core.utils import normalize_unit

CATEGORY_MAP = {
    "spinach": "Produce",
    "kale": "Produce",
    "broccoli": "Produce",
    "chicken": "Protein",
    "beef": "Protein",
    "salmon": "Protein",
    "tofu": "Protein",
    "egg": "Protein",
    "yogurt": "Dairy",
    "milk": "Dairy",
    "cheese": "Dairy",
    "rice": "Pantry",
    "quinoa": "Pantry",
    "pasta": "Pantry",
    "beans": "Pantry",
}


def _categorize(name: str) -> str:
    name_lower = name.lower()
    for key, category in CATEGORY_MAP.items():
        if key in name_lower:
            return category
    return "Other"


def _collect_items(meals: Iterable[PlanMeal]) -> List[MealItem]:
    collected: List[MealItem] = []
    for meal in meals:
        collected.extend(meal.items)
    return collected


def build_list_from_plan(plan: Iterable[PlanDay]) -> List[GroceryItem]:
    """Aggregate grocery items from a plan."""
    aggregate: dict[Tuple[str, str], float] = {}
    for day in plan:
        for meal in day.meals:
            for item in meal.items:
                qty, unit = normalize_unit(item.quantity, item.unit)
                key = (item.name.lower(), unit)
                aggregate[key] = aggregate.get(key, 0.0) + qty
    grocery_items = [
        GroceryItem(category=_categorize(name), name=name.title(), quantity=qty, unit=unit)
        for (name, unit), qty in sorted(aggregate.items())
    ]
    return grocery_items


def export_csv(items: List[GroceryItem]) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["category", "name", "quantity", "unit"])
    for item in items:
        writer.writerow([item.category, item.name, f"{item.quantity:.2f}", item.unit])
    return buffer.getvalue()


__all__ = ["build_list_from_plan", "export_csv"]
