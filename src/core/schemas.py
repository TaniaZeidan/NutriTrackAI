"""Shared Pydantic schemas for NutriTrackAI."""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Literal, Optional

try:  # pragma: no cover
    from pydantic import BaseModel, Field, ConfigDict
except Exception:  # pragma: no cover
    class BaseModel:  # type: ignore
        def __init__(self, **data):
            for key, value in data.items():
                setattr(self, key, value)

        def model_dump(self) -> dict:
            return self.__dict__

    def Field(*args, **kwargs):  # type: ignore
        return kwargs.get("default", kwargs.get("default_factory", None))

    class ConfigDict(dict):  # type: ignore
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)


class MealItem(BaseModel):
    """Represents a single food item within a meal."""

    name: str
    quantity: float
    unit: str
    calories: float
    protein_g: float
    carb_g: float
    fat_g: float
    estimated: bool = False


class Meal(BaseModel):
    """Structured representation of a logged meal."""

    description: str
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"]
    meal_date: date
    items: List[MealItem]

    @property
    def totals(self) -> dict[str, float]:
        total_cal = sum(item.calories for item in self.items)
        protein = sum(item.protein_g for item in self.items)
        carbs = sum(item.carb_g for item in self.items)
        fat = sum(item.fat_g for item in self.items)
        return {
            "calories": round(total_cal, 2),
            "protein_g": round(protein, 2),
            "carb_g": round(carbs, 2),
            "fat_g": round(fat, 2),
        }


class MacroTargets(BaseModel):
    """Daily macro targets for planning and analytics."""

    calories: int
    protein: int
    carbs: int
    fat: int
    diet_tags: List[str]
    exclusions: List[str]
    meals_per_day: int = 3

    def __init__(self, **data):  # type: ignore[override]
        data.setdefault("diet_tags", [])
        data.setdefault("exclusions", [])
        super().__init__(**data)


class PlanMeal(BaseModel):
    """One meal within a planned day."""

    name: str
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"]
    items: List[MealItem]
    notes: Optional[str] = None

    @property
    def totals(self) -> dict[str, float]:
        meal = Meal(
            description=self.name,
            meal_type=self.meal_type,
            meal_date=date.today(),
            items=self.items,
        )
        return meal.totals


class PlanDay(BaseModel):
    """Daily meal plan with aggregated macros."""

    date: date
    meals: List[PlanMeal]

    def totals(self) -> dict[str, float]:
        total = {"calories": 0.0, "protein_g": 0.0, "carb_g": 0.0, "fat_g": 0.0}
        for meal in self.meals:
            macros = meal.totals
            total["calories"] += macros["calories"]
            total["protein_g"] += macros["protein_g"]
            total["carb_g"] += macros["carb_g"]
            total["fat_g"] += macros["fat_g"]
        return {k: round(v, 2) for k, v in total.items()}


class GroceryItem(BaseModel):
    """Shopping list entry grouped by category."""

    category: str
    name: str
    quantity: float
    unit: str


class Step(BaseModel):
    """Cooking step representation."""

    idx: int
    instruction: str
    estimated_minutes: int = 0
    tips: List[str] | None = None
    substitutions: List[str] | None = None

    def __init__(self, **data):  # type: ignore[override]
        data.setdefault("tips", [])
        data.setdefault("substitutions", [])
        super().__init__(**data)


class RecipeDocument(BaseModel):
    """Normalized recipe chunk stored in the vector store."""

    recipe_id: str
    title: str
    text: str
    tags: List[str]
    servings: int
    calories: float
    protein_g: float
    carb_g: float
    fat_g: float


class UserProfile(BaseModel):
    """Persisted user context for personalization."""

    id: int
    created_at: datetime
    name: str
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    goal: Optional[str] = None
    diet_tags: List[str] | None = None
    exclusions: List[str] | None = None
    meals_per_day: int = 3
    calorie_target: Optional[int] = None
    protein_target: Optional[int] = None
    carb_target: Optional[int] = None
    fat_target: Optional[int] = None


__all__ = [
    "MealItem",
    "Meal",
    "MacroTargets",
    "PlanMeal",
    "PlanDay",
    "GroceryItem",
    "Step",
    "RecipeDocument",
    "UserProfile",
]
