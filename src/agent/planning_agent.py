"""Meal Planning Agent with deterministic calculations and optional LLM narration."""
from __future__ import annotations

from typing import Dict, List, Literal, Optional

from core.schemas import MacroTargets, PlanDay
from tools.calorie_calculator import get_personalized_targets
from tools.meal_planner import generate_plan


class MealPlanningAgent:
    """Deterministic planner that can optionally ask the NutriTrack agent to narrate the plan."""

    def __init__(self):
        """Initialize the planning agent."""
        self.current_targets: Optional[Dict] = None
        self._narrator = None

    def create_plan(
        self,
        weight_kg: float,
        height_cm: float,
        age: int,
        sex: Literal["male", "female"],
        activity_level: Literal["sedentary", "light", "moderate", "active", "very_active"],
        goal: Literal["lose_fat", "maintain", "gain_muscle"],
        days: int = 7,
        meals_per_day: int = 3,
        diet_tags: List[str] | None = None,
        exclusions: List[str] | None = None,
    ) -> Dict[str, object]:
        """Create a personalized meal plan using deterministic calculations."""
        try:
            targets = get_personalized_targets(
                weight_kg=float(weight_kg),
                height_cm=float(height_cm),
                age=int(age),
                sex=sex,
                activity_level=activity_level,
                goal=goal,
            )

            self.current_targets = targets

            macro_targets = MacroTargets(
                calories=int(targets["target_calories"]),
                protein=int(targets["protein_g"]),
                carbs=int(targets["carb_g"]),
                fat=int(targets["fat_g"]),
                meals_per_day=int(meals_per_day),
                diet_tags=diet_tags or [],
                exclusions=exclusions or [],
            )

            plan = generate_plan(macro_targets, days=int(days))
            summary = self._create_summary(targets, plan)

            return {"targets": targets, "plan": plan, "summary": summary}

        except Exception as exc:  # pragma: no cover - integration error path
            error_msg = f"Error creating meal plan: {exc}"
            print(f"DEBUG: {error_msg}")
            import traceback

            traceback.print_exc()
            raise ValueError(error_msg)

    def _create_summary(self, targets: Dict, plan: List[PlanDay]) -> str:
        """Create a deterministic text summary for the plan."""
        lines = [
            "=== Your Personalized Meal Plan ===\n",
            "Daily Targets:",
            f"- Calories: {targets['target_calories']} kcal",
            f"- Protein: {targets['protein_g']}g ({targets.get('protein_per_kg', 0):.1f}g/kg body weight)",
            f"- Carbs: {targets['carb_g']}g",
            f"- Fat: {targets['fat_g']}g ({targets.get('fat_per_kg', 0):.1f}g/kg body weight)",
            f"\nGoal: {targets['goal'].replace('_', ' ').title()}",
            f"Activity Level: {targets['activity_level'].replace('_', ' ').title()}",
            f"\nYour BMR (basal calories): {targets['bmr']:.0f} kcal",
            f"Your TDEE (with activity): {targets['tdee']:.0f} kcal\n",
            f"=== {len(plan)}-Day Meal Plan ===\n",
        ]

        for day in plan:
            totals = day.totals()
            lines.append(f"\n{day.date.strftime('%A, %B %d')}:")

            for meal in day.meals:
                meal_totals = meal.totals
                lines.append(
                    f"  - {meal.meal_type.title()}: {meal.name}\n"
                    f"    {meal_totals['calories']:.0f} kcal | "
                    f"P: {meal_totals['protein_g']:.0f}g | "
                    f"C: {meal_totals['carb_g']:.0f}g | "
                    f"F: {meal_totals['fat_g']:.0f}g"
                )

            lines.append(
                f"\n  Daily Total: {totals['calories']:.0f} kcal | "
                f"P: {totals['protein_g']:.0f}g | "
                f"C: {totals['carb_g']:.0f}g | "
                f"F: {totals['fat_g']:.0f}g"
            )

        summary_text = "\n".join(lines)
        return self._llm_enhance_summary(summary_text)

    def _llm_enhance_summary(self, summary_text: str) -> str:
        """Optionally rewrite the deterministic summary with the NutriTrack agent."""
        try:
            if self._narrator is None:
                from agent.orchestrator import NutriTrackAgent
                from tools.tool_registry import get_tools

                self._narrator = NutriTrackAgent(tools=get_tools())

            prompt = (
                "Rewrite the meal plan summary below into a concise, motivating overview. "
                "Keep all calorie and macro numbers exactly the same, and highlight how the plan "
                "supports the user's goal.\n\n"
                f"{summary_text}"
            )
            return self._narrator.run(prompt)
        except Exception:
            return summary_text


__all__ = ["MealPlanningAgent"]
