"""Calorie tracker tool implementation."""
from __future__ import annotations

import json
from datetime import date
from typing import Dict, List, Literal, Tuple

from core.db import Database
from core.schemas import Meal, MealItem
from core.utils import normalize_unit
from config import RAW_DATA_DIR

REFERENCE_FILE = RAW_DATA_DIR / "nutrition_reference.json"
_REFERENCE_CACHE: Dict[str, Dict[str, float]] | None = None
_REFERENCE_NAME_MAP: Dict[str, str] | None = None
_REFERENCE_RAW: Dict[str, Dict[str, float]] | None = None


def _refresh_reference() -> Dict[str, Dict[str, float]]:
    global _REFERENCE_CACHE, _REFERENCE_NAME_MAP, _REFERENCE_RAW
    if not REFERENCE_FILE.exists():
        raise FileNotFoundError(f"Missing nutrition reference file at {REFERENCE_FILE}")
    with REFERENCE_FILE.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    _REFERENCE_RAW = raw
    _REFERENCE_CACHE = {name.lower(): values for name, values in raw.items()}
    _REFERENCE_NAME_MAP = {name.lower(): name for name in raw}
    return _REFERENCE_CACHE


def _load_reference() -> Dict[str, Dict[str, float]]:
    if _REFERENCE_CACHE is None:
        return _refresh_reference()
    return _REFERENCE_CACHE


def _reference_display_name(key: str) -> str:
    if _REFERENCE_NAME_MAP is None:
        _refresh_reference()
    assert _REFERENCE_NAME_MAP is not None
    return _REFERENCE_NAME_MAP.get(key, key.title())


def _write_reference(raw: Dict[str, Dict[str, float]]) -> None:
    ordered = dict(sorted(raw.items(), key=lambda item: item[0].lower()))
    with REFERENCE_FILE.open("w", encoding="utf-8") as f:
        json.dump(ordered, f, indent=2, sort_keys=False)
    # refresh caches with new file layout
    global _REFERENCE_CACHE, _REFERENCE_NAME_MAP, _REFERENCE_RAW
    _REFERENCE_RAW = ordered
    _REFERENCE_CACHE = {name.lower(): values for name, values in ordered.items()}
    _REFERENCE_NAME_MAP = {name.lower(): name for name in ordered}


def add_reference_food(
    name: str,
    calories: float,
    protein_g: float,
    carb_g: float,
    fat_g: float,
    reference_grams: float = 100.0,
) -> None:
    """Persist a new ingredient into the nutrition dataset."""
    display_name = name.strip()
    if not display_name:
        raise ValueError("Food name is required.")
    if reference_grams <= 0:
        raise ValueError("Reference grams must be greater than zero.")
    _load_reference()  # ensure caches are populated
    raw = dict(_REFERENCE_RAW or {})
    factor = 100.0 / reference_grams
    raw[display_name] = {
        "calories": float(calories) * factor,
        "protein_g": float(protein_g) * factor,
        "carb_g": float(carb_g) * factor,
        "fat_g": float(fat_g) * factor,
    }
    _write_reference(raw)


def _match_food(token: str) -> Tuple[str, Dict[str, float]]:
    data = _load_reference()
    token_lower = token.lower().strip()
    if token_lower in data:
        return _reference_display_name(token_lower), data[token_lower]
    for food_key, payload in data.items():
        if token_lower in food_key:
            return _reference_display_name(food_key), payload
    raise ValueError(
        f"Unknown food item: {token}. Add it to the nutrition reference below."
    )


def list_reference_foods() -> List[str]:
    """Return the available foods in the reference dataset."""
    _load_reference()
    assert _REFERENCE_NAME_MAP is not None
    return sorted(_REFERENCE_NAME_MAP.values(), key=lambda name: name.lower())


def _meal_item_from_reference(food_name: str, grams: float) -> MealItem:
    if grams <= 0:
        raise ValueError("Amount must be greater than zero grams.")
    ref_name, nutrients = _match_food(food_name)
    factor = grams / 100.0
    return MealItem(
        name=ref_name.title(),
        quantity=grams,
        unit="g",
        calories=nutrients["calories"] * factor,
        protein_g=nutrients["protein_g"] * factor,
        carb_g=nutrients["carb_g"] * factor,
        fat_g=nutrients["fat_g"] * factor,
        estimated=False,
    )


def calculate_reference_macros(food_name: str, grams: float) -> Dict[str, float]:
    """Preview macros for a specific gram amount."""
    item = _meal_item_from_reference(food_name, grams)
    return {
        "calories": round(item.calories, 2),
        "protein_g": round(item.protein_g, 2),
        "carb_g": round(item.carb_g, 2),
        "fat_g": round(item.fat_g, 2),
    }


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


def log_reference_food(
    food_name: str,
    grams: float,
    date: date,
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"],
    db: Database | None = None,
) -> Dict[str, object]:
    """Log a single reference food scaled to the given grams."""
    item = _meal_item_from_reference(food_name, grams)
    meal = Meal(
        description=f"{grams:g} g {item.name}",
        meal_type=meal_type,
        meal_date=date,
        items=[item],
    )
    database = db or Database()
    meal_id = database.log_meal(meal)
    daily = database.daily_totals(date)
    return {
        "meal_id": meal_id,
        "meal": meal,
        "totals": meal.totals,
        "daily_totals": daily,
    }


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


__all__ = [
    "log_meal",
    "log_reference_food",
    "add_reference_food",
    "list_reference_foods",
    "calculate_reference_macros",
]
