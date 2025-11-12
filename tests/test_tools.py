from __future__ import annotations

from datetime import date
from pathlib import Path

from src.core.db import Database
from src.core.schemas import MacroTargets
from src.tools.calorie_tracker import log_meal
from src.tools.grocery_list import build_list_from_plan
from src.tools.meal_planner import generate_plan


def test_log_meal_creates_records(tmp_path: Path):
    db_path = tmp_path / "test.db"
    db = Database(db_path=db_path)
    result = log_meal("1 cup greek yogurt and 1 banana", date.today(), "breakfast", db=db)
    assert result["totals"]["calories"] > 0
    meals = db.meals_for_date(date.today())
    assert len(meals) == 1


def test_generate_plan_respects_meal_count():
    targets = MacroTargets(calories=2000, protein=140, carbs=220, fat=60, meals_per_day=3)
    plan = generate_plan(targets, days=2)
    assert len(plan) == 2
    assert all(len(day.meals) == 3 for day in plan)


def test_grocery_list_aggregates_plan():
    targets = MacroTargets(calories=2000, protein=140, carbs=220, fat=60, meals_per_day=3)
    plan = generate_plan(targets, days=1)
    groceries = build_list_from_plan(plan)
    assert groceries
    names = {item.name for item in groceries}
    assert any("Quinoa" in name for name in names)
