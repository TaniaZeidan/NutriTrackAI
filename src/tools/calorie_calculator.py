"""Calorie and macro calculator tool for personalized meal planning."""
from __future__ import annotations

from typing import Dict, Literal


def calculate_bmr(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: Literal["male", "female"]
) -> float:
    """Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation."""
    if sex.lower() == "male":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    
    return round(bmr, 2)


def calculate_tdee(
    bmr: float,
    activity_level: Literal["sedentary", "light", "moderate", "active", "very_active"]
) -> float:
    """Calculate Total Daily Energy Expenditure."""
    multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9
    }
    
    multiplier = multipliers.get(activity_level.lower(), 1.2)
    return round(bmr * multiplier, 2)


def calculate_goal_calories(
    tdee: float,
    goal: Literal["lose_fat", "maintain", "gain_muscle"]
) -> float:
    """Adjust TDEE based on fitness goal."""
    adjustments = {
        "lose_fat": -500,
        "maintain": 0,
        "gain_muscle": 300
    }
    
    adjustment = adjustments.get(goal.lower(), 0)
    target = tdee + adjustment
    
    # Safety bounds
    return max(1200, round(target, 2))


def calculate_macros(
    calories: float,
    goal: Literal["lose_fat", "maintain", "gain_muscle"],
    weight_kg: float = 70.0
) -> Dict[str, int]:
    """Calculate macro distribution based on goal using body weight.
    
    Research-Based Approach:
    - Protein based on body weight (g/kg)
    - Fat as percentage of calories
    - Carbs fill remaining calories
    
    This ensures thermodynamic accuracy: P×4 + C×4 + F×9 = Total Calories
    """
    # Calculate protein based on body weight
    if goal == "lose_fat":
        protein_g = round(weight_kg * 2.0)  # 2.0g/kg for fat loss
    elif goal == "gain_muscle":
        protein_g = round(weight_kg * 1.8)  # 1.8g/kg for muscle gain
    else:  # maintain
        protein_g = round(weight_kg * 1.4)  # 1.4g/kg for maintenance
    
    # Calculate fat as percentage of calories
    if goal == "lose_fat":
        fat_pct = 0.25  # 25% of calories
    elif goal == "gain_muscle":
        fat_pct = 0.20  # 20% of calories
    else:  # maintain
        fat_pct = 0.30  # 30% of calories
    
    fat_g = round((calories * fat_pct) / 9)
    
    # Calculate carbs from remaining calories
    protein_calories = protein_g * 4
    fat_calories = fat_g * 9
    remaining_calories = calories - protein_calories - fat_calories
    carb_g = round(remaining_calories / 4)
    
    # Ensure carbs are positive (minimum 100g for brain function)
    if carb_g < 100:
        carb_g = 100
        remaining_for_fat = calories - protein_calories - (carb_g * 4)
        fat_g = round(remaining_for_fat / 9)
    
    # Final verification
    calculated_calories = (protein_g * 4) + (carb_g * 4) + (fat_g * 9)
    
    # Adjust carbs if there's a discrepancy
    if abs(calculated_calories - calories) > 20:
        calorie_diff = calories - calculated_calories
        carb_adjustment = round(calorie_diff / 4)
        carb_g += carb_adjustment
    
    return {
        "protein": int(protein_g),
        "carbs": int(carb_g),
        "fat": int(fat_g)
    }


def validate_macros(protein_g: int, carb_g: int, fat_g: int, target_calories: int) -> Dict[str, object]:
    """Validate that macros add up to target calories correctly."""
    calculated_calories = (protein_g * 4) + (carb_g * 4) + (fat_g * 9)
    difference = calculated_calories - target_calories
    accuracy_pct = (calculated_calories / target_calories) * 100
    
    return {
        "calculated_calories": calculated_calories,
        "target_calories": target_calories,
        "difference": difference,
        "accuracy_pct": round(accuracy_pct, 1),
        "is_valid": abs(difference) <= 50
    }


def get_personalized_targets(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: Literal["male", "female"],
    activity_level: Literal["sedentary", "light", "moderate", "active", "very_active"],
    goal: Literal["lose_fat", "maintain", "gain_muscle"]
) -> Dict[str, object]:
    """Calculate complete personalized nutrition targets.
    
    Main function for meal planning agent.
    Uses body weight to calculate protein needs (more accurate than percentages).
    """
    bmr = calculate_bmr(weight_kg, height_cm, age, sex)
    tdee = calculate_tdee(bmr, activity_level)
    target_calories = calculate_goal_calories(tdee, goal)
    macros = calculate_macros(target_calories, goal, weight_kg)
    
    # Validate macros
    validation = validate_macros(
        macros["protein"],
        macros["carbs"],
        macros["fat"],
        int(target_calories)
    )
    
    # Calculate g/kg ratios for transparency
    protein_per_kg = macros["protein"] / weight_kg
    fat_per_kg = macros["fat"] / weight_kg
    
    return {
        "bmr": bmr,
        "tdee": tdee,
        "target_calories": int(target_calories),
        "protein_g": macros["protein"],
        "carb_g": macros["carbs"],
        "fat_g": macros["fat"],
        "protein_per_kg": round(protein_per_kg, 1),
        "fat_per_kg": round(fat_per_kg, 1),
        "goal": goal,
        "activity_level": activity_level,
        "validation": validation
    }


__all__ = [
    "calculate_bmr",
    "calculate_tdee",
    "calculate_goal_calories",
    "calculate_macros",
    "validate_macros",
    "get_personalized_targets"
]