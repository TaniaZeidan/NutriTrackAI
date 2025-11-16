"""Ingredient weight estimation helpers."""
from __future__ import annotations

import json
from typing import Dict, List

from config import RAW_DATA_DIR


REFERENCE_FILE = RAW_DATA_DIR / "nutrition_reference.json"
_REFERENCE_CACHE: Dict[str, Dict[str, float]] | None = None


def _load_reference() -> Dict[str, Dict[str, float]]:
    global _REFERENCE_CACHE
    if _REFERENCE_CACHE is None:
        with REFERENCE_FILE.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        _REFERENCE_CACHE = {name.lower(): values for name, values in payload.items()}
    return _REFERENCE_CACHE


def _match_food(name: str) -> tuple[str, Dict[str, float]]:
    data = _load_reference()
    token = name.lower().strip()
    if token in data:
        return name.title(), data[token]
    for candidate, values in data.items():
        if token in candidate:
            return candidate.title(), values
    raise ValueError(f"Ingredient '{name}' is not in the nutrition reference.")


def estimate_ingredient_grams(
    ingredients: List[str],
    calories_per_serving: float,
    servings: int = 1,
) -> List[Dict[str, float]]:
    """Estimate grams per ingredient using nutrition reference data.

    The algorithm distributes total calories evenly across the matched ingredients.
    Each ingredient's calories-per-gram (from the reference, normalized to 100 g)
    is used to compute an approximate gram amount.
    """
    matches = []
    for ingredient in ingredients:
        try:
            display_name, macros = _match_food(ingredient)
        except ValueError:
            continue
        matches.append((display_name, macros))
    if not matches:
        raise ValueError("No ingredients matched the nutrition reference.")
    servings = max(1, int(servings))
    calories_per_serving = max(1.0, float(calories_per_serving))
    calorie_share = calories_per_serving / len(matches)
    estimates: List[Dict[str, float]] = []
    for display_name, macros in matches:
        cal_per_gram = macros["calories"] / 100.0 if macros["calories"] else 0.0
        grams_per_serving = calorie_share / cal_per_gram if cal_per_gram else 0.0
        protein = (macros["protein_g"] / 100.0) * grams_per_serving
        carbs = (macros["carb_g"] / 100.0) * grams_per_serving
        fat = (macros["fat_g"] / 100.0) * grams_per_serving
        estimates.append(
            {
                "ingredient": display_name,
                "grams_per_serving": round(grams_per_serving, 1),
                "grams_total": round(grams_per_serving * servings, 1),
                "calories_per_serving": round(calorie_share, 1),
                "protein_per_serving": round(protein, 1),
                "carb_per_serving": round(carbs, 1),
                "fat_per_serving": round(fat, 1),
            }
        )
    return estimates


__all__ = ["estimate_ingredient_grams"]
