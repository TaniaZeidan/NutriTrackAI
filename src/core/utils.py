"""Utility helpers for nutrition calculations."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, Tuple

import math

GRAM_EQUIVALENTS: Dict[str, float] = {
    "g": 1.0,
    "gram": 1.0,
    "grams": 1.0,
    "kg": 1000.0,
    "mg": 0.001,
    "lb": 453.592,
    "oz": 28.3495,
    "ml": 1.0,
    "l": 1000.0,
    "cup": 240.0,
    "tbsp": 15.0,
    "tsp": 5.0,
    "piece": 1.0,
    "pcs": 1.0,
    "unit": 1.0,
}


def normalize_unit(quantity: float, unit: str) -> Tuple[float, str]:
    """Normalize various units to grams when possible."""
    unit_lower = unit.lower()
    if unit_lower in {"cup", "tbsp", "tsp", "ml", "l"}:
        grams = quantity * GRAM_EQUIVALENTS[unit_lower]
        return grams, "g"
    if unit_lower in GRAM_EQUIVALENTS:
        grams = quantity * GRAM_EQUIVALENTS[unit_lower]
        return grams, "g"
    return quantity, unit


def macro_totals(items: Iterable[Dict[str, float]]) -> Dict[str, float]:
    """Sum macro nutrients from an iterable of dicts."""
    totals = defaultdict(float)
    for item in items:
        for key in ("calories", "protein_g", "carb_g", "fat_g"):
            totals[key] += float(item.get(key, 0.0))
    return {k: round(v, 2) for k, v in totals.items()}


def macro_delta(targets: Dict[str, float], totals: Dict[str, float]) -> Dict[str, float]:
    """Compute difference between totals and targets."""
    diff = {}
    for key in ("calories", "protein", "carbs", "fat"):
        target_val = float(targets.get(key, 0.0))
        total_key = key if key == "calories" else f"{key[:-1]}_g"
        diff[key] = round(total_key and totals.get(total_key, 0.0) - target_val, 2)
    return diff


def safe_divide(numerator: float, denominator: float) -> float:
    """Avoid ZeroDivisionError when computing ratios."""
    if math.isclose(denominator, 0.0):
        return 0.0
    return numerator / denominator


def clamp_calories(calories: float, minimum: float = 1200.0) -> float:
    """Warn if calories drop below a safe threshold."""
    return max(calories, minimum)


__all__ = [
    "GRAM_EQUIVALENTS",
    "normalize_unit",
    "macro_totals",
    "macro_delta",
    "safe_divide",
    "clamp_calories",
]
