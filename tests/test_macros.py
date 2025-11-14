from __future__ import annotations

from src.core.utils import macro_totals, normalize_unit


def test_normalize_unit_converts_to_grams():
    qty, unit = normalize_unit(2, "cup")
    assert unit == "g"
    assert qty == 480


def test_macro_totals_sums_values():
    items = [
        {"calories": 100, "protein_g": 10, "carb_g": 20, "fat_g": 5},
        {"calories": 150, "protein_g": 5, "carb_g": 10, "fat_g": 2},
    ]
    totals = macro_totals(items)
    assert totals["calories"] == 250
    assert totals["protein_g"] == 15
