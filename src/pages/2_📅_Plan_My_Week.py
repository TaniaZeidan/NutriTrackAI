"""Enhanced Meal Planning page with personalized calculations."""
from __future__ import annotations

from typing import Literal

import streamlit as st

from agent.planning_agent import MealPlanningAgent
from ui.components import plan_table


def _ensure_session() -> None:
    """Initialize session state."""
    if "planning_agent" not in st.session_state:
        st.session_state["planning_agent"] = MealPlanningAgent()
    if "user_profile" not in st.session_state:
        st.session_state["user_profile"] = {
            "weight_kg": 70.0,
            "height_cm": 175.0,
            "age": 25,
            "sex": "male",
            "activity_level": "moderate",
            "goal": "maintain"
        }


def main() -> None:
    st.title("📅 Personalized Meal Planner")
    st.caption(
        "Get a customized meal plan based on your body metrics and fitness goals. "
        "The AI calculates your exact calorie needs and creates a balanced weekly plan."
    )
    
    _ensure_session()
    
    # Sidebar: User Profile
    with st.sidebar:
        st.header("Your Profile")
        
        profile = st.session_state["user_profile"]
        
        weight = st.number_input(
            "Weight (kg)",
            min_value=30.0,
            max_value=200.0,
            value=profile["weight_kg"],
            step=0.5,
            help="Your current body weight"
        )
        
        height = st.number_input(
            "Height (cm)",
            min_value=100.0,
            max_value=250.0,
            value=profile["height_cm"],
            step=1.0,
            help="Your height"
        )
        
        age = st.number_input(
            "Age (years)",
            min_value=15,
            max_value=100,
            value=profile["age"],
            step=1,
            help="Your age"
        )
        
        sex = st.selectbox(
            "Sex",
            options=["male", "female"],
            index=0 if profile["sex"] == "male" else 1,
            help="Biological sex affects BMR calculation"
        )
        
        activity_level = st.selectbox(
            "Activity Level",
            options=[
                "sedentary",
                "light",
                "moderate",
                "active",
                "very_active"
            ],
            index=2,
            help=(
                "Sedentary: Little/no exercise\n"
                "Light: 1-3 days/week\n"
                "Moderate: 3-5 days/week\n"
                "Active: 6-7 days/week\n"
                "Very Active: Physical job + training"
            )
        )
        
        goal = st.selectbox(
            "Goal",
            options=["lose_fat", "maintain", "gain_muscle"],
            index=1,
            format_func=lambda x: {
                "lose_fat": "🔥 Lose Fat",
                "maintain": "⚖️ Maintain Weight",
                "gain_muscle": "💪 Gain Muscle"
            }[x]
        )
        
        st.divider()
        
        st.subheader("Plan Settings")
        
        days = st.selectbox(
            "Plan Duration",
            options=[3, 5, 7],
            index=2,
            format_func=lambda x: f"{x} days"
        )
        
        meals_per_day = st.selectbox(
            "Meals Per Day",
            options=[3, 4],
            index=0
        )
        
        diet_tags = st.text_input(
            "Dietary Preferences",
            placeholder="e.g., vegetarian, high-protein",
            help="Comma-separated tags like 'vegetarian, high-protein, keto'"
        )
        
        exclusions = st.text_input(
            "Food Exclusions",
            placeholder="e.g., dairy, gluten",
            help="Comma-separated foods to avoid"
        )
        
        # Update profile
        st.session_state["user_profile"].update({
            "weight_kg": weight,
            "height_cm": height,
            "age": age,
            "sex": sex,
            "activity_level": activity_level,
            "goal": goal
        })
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Generate Your Plan")
        
        if st.button("🎯 Calculate & Generate Plan", use_container_width=True, type="primary"):
            with st.spinner("Calculating your personalized nutrition targets..."):
                try:
                    agent = st.session_state["planning_agent"]
                    
                    result = agent.create_plan(
                        weight_kg=profile["weight_kg"],
                        height_cm=profile["height_cm"],
                        age=profile["age"],
                        sex=profile["sex"],
                        activity_level=profile["activity_level"],
                        goal=profile["goal"],
                        days=days,
                        meals_per_day=meals_per_day,
                        diet_tags=[t.strip() for t in diet_tags.split(",") if t.strip()],
                        exclusions=[e.strip() for e in exclusions.split(",") if e.strip()]
                    )
                    
                    st.session_state["weekly_plan"] = result["plan"]
                    st.session_state["plan_targets"] = result["targets"]
                    st.session_state["plan_summary"] = result["summary"]
                    
                    st.success("✅ Your personalized meal plan is ready!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error generating plan: {str(e)}")
    
    with col2:
        if "plan_targets" in st.session_state:
            targets = st.session_state["plan_targets"]
            
            st.metric("BMR", f"{targets['bmr']:.0f} kcal")
            st.metric("TDEE", f"{targets['tdee']:.0f} kcal")
            st.metric("Target Calories", f"{targets['target_calories']} kcal")
    
    # Display existing plan
    if "weekly_plan" in st.session_state and st.session_state["weekly_plan"]:
        st.divider()
        
        # Show targets
        if "plan_targets" in st.session_state:
            with st.expander("📊 Your Nutrition Targets", expanded=True):
                targets = st.session_state["plan_targets"]
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Daily Calories", f"{targets['target_calories']} kcal")
                
                with col2:
                    protein_cals = targets['protein_g'] * 4
                    protein_per_kg = targets.get('protein_per_kg', 0)
                    st.metric(
                        "Protein", 
                        f"{targets['protein_g']}g",
                        f"{protein_per_kg}g/kg · {protein_cals} kcal"
                    )
                
                with col3:
                    carb_cals = targets['carb_g'] * 4
                    st.metric("Carbs", f"{targets['carb_g']}g", f"{carb_cals} kcal")
                
                with col4:
                    fat_cals = targets['fat_g'] * 9
                    st.metric("Fat", f"{targets['fat_g']}g", f"{fat_cals} kcal")
                
                st.info(
                    f"**Goal:** {targets['goal'].replace('_', ' ').title()} | "
                    f"**Activity:** {targets['activity_level'].replace('_', ' ').title()}"
                )
                
                st.markdown("---")
                st.markdown("**How we calculated this:**")
                st.markdown(
                    f"1. **BMR (Basal Metabolic Rate):** {targets['bmr']:.0f} kcal/day "
                    f"(calories your body needs at rest)"
                )
                st.markdown(
                    f"2. **TDEE (Total Daily Energy Expenditure):** {targets['tdee']:.0f} kcal/day "
                    f"(BMR × activity multiplier)"
                )
                
                if targets['goal'] == "lose_fat":
                    adjustment = "−500 kcal deficit for healthy fat loss (~0.5kg/week)"
                elif targets['goal'] == "gain_muscle":
                    adjustment = "+300 kcal surplus for lean muscle gain"
                else:
                    adjustment = "No adjustment (maintenance)"
                
                st.markdown(f"3. **Goal Adjustment:** {adjustment}")
                
                # Show macro math
                protein_cals = targets['protein_g'] * 4
                carb_cals = targets['carb_g'] * 4
                fat_cals = targets['fat_g'] * 9
                total_from_macros = protein_cals + carb_cals + fat_cals
                
                st.markdown("---")
                st.markdown("**Macro Math Verification:**")
                st.markdown(
                    f"- Protein: {targets['protein_g']}g × 4 cal/g = **{protein_cals} kcal**\n"
                    f"- Carbs: {targets['carb_g']}g × 4 cal/g = **{carb_cals} kcal**\n"
                    f"- Fat: {targets['fat_g']}g × 9 cal/g = **{fat_cals} kcal**\n"
                    f"- **Total: {total_from_macros} kcal** (Target: {targets['target_calories']} kcal)"
                )
                
                accuracy = (total_from_macros / targets['target_calories']) * 100
                if abs(accuracy - 100) <= 2:
                    st.success(f"✅ Macros are accurate ({accuracy:.1f}% of target)")
                else:
                    st.info(f"ℹ️ Macros total to {accuracy:.1f}% of target (small rounding difference)")
        
        # Show plan
        st.subheader("Your Weekly Meal Plan")
        plan_table(st.session_state["weekly_plan"])
        
        # Actions
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🛒 Generate Grocery List", use_container_width=True):
                from tools.grocery_list import build_list_from_plan
                groceries = build_list_from_plan(st.session_state["weekly_plan"])
                st.session_state["groceries"] = groceries
                st.success("Grocery list ready! Check the Grocery List page.")
        
        with col2:
            if "plan_summary" in st.session_state:
                summary = st.session_state["plan_summary"]
                st.download_button(
                    "📄 Download Plan",
                    data=summary,
                    file_name="meal_plan.txt",
                    mime="text/plain",
                    use_container_width=True
                )
    else:
        st.info(
            "👆 Fill in your profile in the sidebar and click "
            "'Calculate & Generate Plan' to get started!"
        )
        
        st.markdown("### Why Personalized Planning?")
        st.markdown(
            """
            Our AI agent calculates your exact calorie needs using:
            
            1. **BMR (Basal Metabolic Rate)**: How many calories your body burns at rest
            2. **TDEE (Total Daily Energy Expenditure)**: BMR adjusted for your activity level
            3. **Goal Adjustment**: 
               - Fat loss: 500 calorie deficit
               - Muscle gain: 300 calorie surplus
               - Maintenance: No adjustment
            
            Then it creates a balanced meal plan that hits your targets perfectly!
            """
        )


if __name__ == "__main__":
    main()