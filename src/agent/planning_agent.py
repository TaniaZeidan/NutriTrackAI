"""Simplified Meal Planning Agent - Direct calculation without LangChain complexity."""
from __future__ import annotations

from typing import Dict, List, Literal

from core.schemas import MacroTargets, PlanDay
from tools.calorie_calculator import get_personalized_targets
from tools.meal_planner import generate_plan


class MealPlanningAgent:
    """Simplified meal planning agent with direct calculations."""
    
    def __init__(self):
        """Initialize the planning agent."""
        self.current_targets = None
    
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
        diet_tags: List[str] = None,
        exclusions: List[str] = None
    ) -> Dict[str, object]:
        """Create a personalized meal plan.
        
        Args:
            weight_kg: Body weight in kilograms
            height_cm: Height in centimeters
            age: Age in years
            sex: Biological sex
            activity_level: Activity level
            goal: Fitness goal
            days: Number of days to plan
            meals_per_day: Meals per day (3 or 4)
            diet_tags: Dietary preferences
            exclusions: Foods to exclude
        
        Returns:
            Dictionary with targets and meal plan
        """
        try:
            # Step 1: Calculate personalized targets
            targets = get_personalized_targets(
                weight_kg=float(weight_kg),
                height_cm=float(height_cm),
                age=int(age),
                sex=sex,
                activity_level=activity_level,
                goal=goal
            )
            
            self.current_targets = targets
            
            # Step 2: Create MacroTargets object
            macro_targets = MacroTargets(
                calories=int(targets["target_calories"]),
                protein=int(targets["protein_g"]),
                carbs=int(targets["carb_g"]),
                fat=int(targets["fat_g"]),
                meals_per_day=int(meals_per_day),
                diet_tags=diet_tags or [],
                exclusions=exclusions or []
            )
            
            # Step 3: Generate plan
            plan = generate_plan(macro_targets, days=int(days))
            
            # Step 4: Create summary
            summary = self._create_summary(targets, plan)
            
            return {
                "targets": targets,
                "plan": plan,
                "summary": summary
            }
            
        except Exception as e:
            # Provide helpful error message
            error_msg = f"Error creating meal plan: {str(e)}"
            print(f"DEBUG: {error_msg}")
            import traceback
            traceback.print_exc()
            raise ValueError(error_msg)
    
    def _create_summary(self, targets: Dict, plan: List[PlanDay]) -> str:
        """Create a text summary of the plan."""
        lines = [
            "=== Your Personalized Meal Plan ===\n",
            f"Daily Targets:",
            f"- Calories: {targets['target_calories']} kcal",
            f"- Protein: {targets['protein_g']}g ({targets.get('protein_per_kg', 0):.1f}g/kg body weight)",
            f"- Carbs: {targets['carb_g']}g",
            f"- Fat: {targets['fat_g']}g ({targets.get('fat_per_kg', 0):.1f}g/kg body weight)",
            f"\nGoal: {targets['goal'].replace('_', ' ').title()}",
            f"Activity Level: {targets['activity_level'].replace('_', ' ').title()}",
            f"\nYour BMR (basal calories): {targets['bmr']:.0f} kcal",
            f"Your TDEE (with activity): {targets['tdee']:.0f} kcal\n",
            f"=== {len(plan)}-Day Meal Plan ===\n"
        ]
        
        for day in plan:
            totals = day.totals()
            lines.append(f"\n{day.date.strftime('%A, %B %d')}:")
            
            for meal in day.meals:
                meal_totals = meal.totals
                lines.append(
                    f"  • {meal.meal_type.title()}: {meal.name}\n"
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
        
        return "\n".join(lines)


__all__ = ["MealPlanningAgent"]