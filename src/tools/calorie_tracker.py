"""Calorie tracker tool implementation."""
from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from typing import Dict, List, Literal, Tuple

from ..core.db import Database
from ..core.schemas import Meal, MealItem
from ..core.utils import normalize_unit
from ..config import RAW_DATA_DIR


@lru_cache(maxsize=1)
def _load_reference() -> Dict[str, Dict[str, float]]:
    path = RAW_DATA_DIR / "nutrition_reference.json"
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return {name.lower(): values for name, values in data.items()}


def _match_food(token: str) -> Tuple[str, Dict[str, float]]:
    data = _load_reference()
    token_lower = token.lower().strip()
    if token_lower in data:
        return token_lower, data[token_lower]
    for food in data:
        if token_lower in food:
            return food, data[food]
    raise ValueError(f"Unknown food item: {token}")


def _parse_description(description: str) -> List[MealItem]:
    parts = [p.strip() for p in description.replace("with", ",").replace("and", ",").split(",") if p.strip()]
    items: List[MealItem] = []
    for part in parts:
        tokens = part.split()
        quantity = 1.0
        unit = "serving"
        name_tokens: List[str] = []
        for token in tokens:
            try:
                quantity = float(token)
                continue
            except ValueError:
                pass
            if token.lower() in {"g", "gram", "grams", "ml", "cup", "cups", "tbsp", "tsp", "oz"}:
                unit = token.lower().rstrip("s")
                continue
            name_tokens.append(token)
        if not name_tokens:
            continue
        food_name = " ".join(name_tokens)
        ref_name, nutrients = _match_food(food_name)
        qty, normalized_unit = normalize_unit(quantity, unit)
        factor = qty / 100.0 if normalized_unit == "g" else quantity
        item = MealItem(
            name=ref_name.title(),
            quantity=quantity,
            unit=unit,
            calories=nutrients["calories"] * factor,
            protein_g=nutrients["protein_g"] * factor,
            carb_g=nutrients["carb_g"] * factor,
            fat_g=nutrients["fat_g"] * factor,
            estimated=normalized_unit != "g",
        )
        items.append(item)
    return items


def log_meal(
    description: str,
    date: date,
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"],
    db: Database | None = None,
) -> Dict[str, object]:
    """Parse a free-text description, compute macros, and log to the database."""
    items = _parse_description(description)
    if not items:
        raise ValueError("Unable to parse any meal items from description")
    meal = Meal(description=description, meal_type=meal_type, meal_date=date, items=items)
    database = db or Database()
    meal_id = database.log_meal(meal)
    daily = database.daily_totals(date)
    return {
        "meal_id": meal_id,
        "meal": meal,
        "totals": meal.totals,
        "daily_totals": daily,
    }


__all__ = ["log_meal"]
