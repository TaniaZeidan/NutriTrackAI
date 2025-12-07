"""Enhanced Meal Planning page with personalized calculations and beautiful UI."""
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
    # Page header
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="margin-bottom: 0.5rem;">📅 Personalized Meal Planner</h1>
        <p style="color: #52796F; font-size: 1.1rem;">Get a customized meal plan based on your body metrics and fitness goals.</p>
    </div>
    """, unsafe_allow_html=True)
    
    _ensure_session()
    
    # Sidebar: User Profile with clean styling
    with st.sidebar:
        st.markdown("""
        <div style="padding: 0.5rem 0.5rem 0.75rem 0.5rem; margin-bottom: 0.5rem;">
            <p style="font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px; color: #94A3B8; margin: 0 0 0.5rem 0; font-weight: 600;">👤 Your Profile</p>
        </div>
        """, unsafe_allow_html=True)
        
        profile = st.session_state["user_profile"]
        
        weight = st.number_input(
            "⚖️ Weight (kg)",
            min_value=30.0,
            max_value=200.0,
            value=profile["weight_kg"],
            step=0.5,
            help="Your current body weight"
        )
        
        height = st.number_input(
            "📏 Height (cm)",
            min_value=100.0,
            max_value=250.0,
            value=profile["height_cm"],
            step=1.0,
            help="Your height"
        )
        
        age = st.number_input(
            "🎂 Age (years)",
            min_value=15,
            max_value=100,
            value=profile["age"],
            step=1,
            help="Your age"
        )
        
        sex = st.selectbox(
            "⚧ Sex",
            options=["male", "female"],
            index=0 if profile["sex"] == "male" else 1,
            help="Biological sex affects BMR calculation",
            format_func=lambda x: "♂️ Male" if x == "male" else "♀️ Female"
        )
        
        st.markdown("---")
        
        st.markdown("""
        <p style="font-size: 0.75rem; color: #64748B; margin: 0 0 0.25rem 0;">🏃 Activity Level</p>
        """, unsafe_allow_html=True)
        
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
            label_visibility="collapsed",
            format_func=lambda x: {
                "sedentary": "🛋️ Sedentary (Little/no exercise)",
                "light": "🚶 Light (1-3 days/week)",
                "moderate": "🏃 Moderate (3-5 days/week)",
                "active": "💪 Active (6-7 days/week)",
                "very_active": "🔥 Very Active (Physical job + training)"
            }[x]
        )
        
        st.markdown("""
        <p style="font-size: 0.75rem; color: #64748B; margin: 1rem 0 0.25rem 0;">🎯 Fitness Goal</p>
        """, unsafe_allow_html=True)
        
        goal = st.selectbox(
            "Goal",
            options=["lose_fat", "maintain", "gain_muscle"],
            index=1,
            label_visibility="collapsed",
            format_func=lambda x: {
                "lose_fat": "🔥 Lose Fat (-500 kcal)",
                "maintain": "⚖️ Maintain Weight",
                "gain_muscle": "💪 Gain Muscle (+300 kcal)"
            }[x]
        )
        
        st.markdown("---")
        
        st.markdown("""
        <p style="font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px; color: #94A3B8; margin: 0 0 0.5rem 0; font-weight: 600;">📋 Plan Settings</p>
        """, unsafe_allow_html=True)
        
        days = st.selectbox(
            "Plan Duration",
            options=[3, 5, 7],
            index=2,
            format_func=lambda x: f"📆 {x} days"
        )
        
        meals_per_day = st.selectbox(
            "Meals Per Day",
            options=[3, 4],
            index=0,
            format_func=lambda x: f"🍽️ {x} meals/day"
        )
        
        diet_tags = st.text_input(
            "🥗 Dietary Preferences",
            placeholder="e.g., vegetarian, high-protein",
            help="Comma-separated tags like 'vegetarian, high-protein, keto'"
        )
        
        exclusions = st.text_input(
            "🚫 Food Exclusions",
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
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div style="background: white; padding: 2rem; border-radius: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); margin-bottom: 1.5rem;">
            <h3 style="color: #2D6A4F; margin-bottom: 1rem;">🧮 Generate Your Personalized Plan</h3>
            <p style="color: #52796F;">Fill in your profile in the sidebar, then click the button below to calculate your personalized nutrition targets and generate a meal plan.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🎯 Calculate & Generate My Plan", use_container_width=True, type="primary"):
            with st.spinner("🔄 Calculating your personalized nutrition targets..."):
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
                    st.error(f"❌ Error generating plan: {str(e)}")
    
    with col2:
        if "plan_targets" in st.session_state:
            targets = st.session_state["plan_targets"]
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1B4332 0%, #2D6A4F 100%); padding: 1.5rem; border-radius: 16px; color: white;">
                <h4 style="color: white !important; margin-bottom: 1rem; opacity: 0.9;">📊 Quick Stats</h4>
                <div style="margin-bottom: 0.75rem;">
                    <span style="opacity: 0.7; font-size: 0.85rem;">BMR</span>
                    <h3 style="color: #95D5B2 !important; margin: 0;">{targets['bmr']:.0f} kcal</h3>
                </div>
                <div style="margin-bottom: 0.75rem;">
                    <span style="opacity: 0.7; font-size: 0.85rem;">TDEE</span>
                    <h3 style="color: #95D5B2 !important; margin: 0;">{targets['tdee']:.0f} kcal</h3>
                </div>
                <div>
                    <span style="opacity: 0.7; font-size: 0.85rem;">Target</span>
                    <h3 style="color: #52B788 !important; margin: 0;">{targets['target_calories']} kcal</h3>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #F3F4F6 0%, #E5E7EB 100%); padding: 1.5rem; border-radius: 16px; text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📋</div>
                <p style="color: #6B7280; margin: 0; font-size: 0.9rem;">Generate a plan to see your stats here</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Display existing plan
    if "weekly_plan" in st.session_state and st.session_state["weekly_plan"]:
        st.markdown("---")
        
        # Show targets in an expander
        if "plan_targets" in st.session_state:
            with st.expander("📊 Your Nutrition Targets - Click to expand", expanded=True):
                targets = st.session_state["plan_targets"]
                
                # Macro cards
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); padding: 1.25rem; border-radius: 14px; text-align: center;">
                        <p style="color: #92400E; font-size: 0.8rem; margin: 0;">🔥 Daily Calories</p>
                        <h2 style="color: #78350F; margin: 0.5rem 0 0 0; font-size: 1.6rem;">{targets['target_calories']}</h2>
                        <p style="color: #A16207; font-size: 0.75rem; margin: 0;">kcal</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    protein_per_kg = targets.get('protein_per_kg', 0)
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%); padding: 1.25rem; border-radius: 14px; text-align: center;">
                        <p style="color: #1E40AF; font-size: 0.8rem; margin: 0;">💪 Protein</p>
                        <h2 style="color: #1E3A8A; margin: 0.5rem 0 0 0; font-size: 1.6rem;">{targets['protein_g']}g</h2>
                        <p style="color: #3B82F6; font-size: 0.75rem; margin: 0;">{protein_per_kg}g/kg</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%); padding: 1.25rem; border-radius: 14px; text-align: center;">
                        <p style="color: #065F46; font-size: 0.8rem; margin: 0;">🍞 Carbs</p>
                        <h2 style="color: #064E3B; margin: 0.5rem 0 0 0; font-size: 1.6rem;">{targets['carb_g']}g</h2>
                        <p style="color: #10B981; font-size: 0.75rem; margin: 0;">{targets['carb_g'] * 4} kcal</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #FCE7F3 0%, #FBCFE8 100%); padding: 1.25rem; border-radius: 14px; text-align: center;">
                        <p style="color: #9D174D; font-size: 0.8rem; margin: 0;">🥑 Fat</p>
                        <h2 style="color: #831843; margin: 0.5rem 0 0 0; font-size: 1.6rem;">{targets['fat_g']}g</h2>
                        <p style="color: #EC4899; font-size: 0.75rem; margin: 0;">{targets['fat_g'] * 9} kcal</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Goal info card
                goal_text = targets['goal'].replace('_', ' ').title()
                activity_text = targets['activity_level'].replace('_', ' ').title()
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #2D6A4F 0%, #40916C 100%); padding: 1.25rem; border-radius: 14px; color: white;">
                    <div style="display: flex; justify-content: space-around; text-align: center;">
                        <div>
                            <span style="opacity: 0.7; font-size: 0.85rem;">🎯 Goal</span>
                            <h4 style="color: white !important; margin: 0.25rem 0 0 0;">{goal_text}</h4>
                        </div>
                        <div>
                            <span style="opacity: 0.7; font-size: 0.85rem;">🏃 Activity</span>
                            <h4 style="color: white !important; margin: 0.25rem 0 0 0;">{activity_text}</h4>
                        </div>
                        <div>
                            <span style="opacity: 0.7; font-size: 0.85rem;">⚡ BMR</span>
                            <h4 style="color: white !important; margin: 0.25rem 0 0 0;">{targets['bmr']:.0f} kcal</h4>
                        </div>
                        <div>
                            <span style="opacity: 0.7; font-size: 0.85rem;">📈 TDEE</span>
                            <h4 style="color: white !important; margin: 0.25rem 0 0 0;">{targets['tdee']:.0f} kcal</h4>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Calculation explanation
                with st.expander("🧮 How we calculated your targets"):
                    st.markdown(f"""
                    **Step 1: BMR (Basal Metabolic Rate)**
                    - Your body burns **{targets['bmr']:.0f} kcal/day** at complete rest
                    - Calculated using the Mifflin-St Jeor equation
                    
                    **Step 2: TDEE (Total Daily Energy Expenditure)**  
                    - BMR × Activity Multiplier = **{targets['tdee']:.0f} kcal/day**
                    - This is your maintenance calories
                    
                    **Step 3: Goal Adjustment**
                    """)
                    
                    if targets['goal'] == "lose_fat":
                        st.info("🔥 **Fat Loss**: -500 kcal deficit for healthy weight loss (~0.5kg/week)")
                    elif targets['goal'] == "gain_muscle":
                        st.info("💪 **Muscle Gain**: +300 kcal surplus for lean muscle building")
                    else:
                        st.info("⚖️ **Maintenance**: No calorie adjustment")
                    
                    st.markdown("---")
                    
                    # Macro math verification
                    protein_cals = targets['protein_g'] * 4
                    carb_cals = targets['carb_g'] * 4
                    fat_cals = targets['fat_g'] * 9
                    total_from_macros = protein_cals + carb_cals + fat_cals
                    
                    st.markdown(f"""
                    **Macro Breakdown:**
                    | Macro | Grams | Calories |
                    |-------|-------|----------|
                    | Protein | {targets['protein_g']}g | {protein_cals} kcal |
                    | Carbs | {targets['carb_g']}g | {carb_cals} kcal |
                    | Fat | {targets['fat_g']}g | {fat_cals} kcal |
                    | **Total** | | **{total_from_macros} kcal** |
                    """)
                    
                    accuracy = (total_from_macros / targets['target_calories']) * 100
                    if abs(accuracy - 100) <= 2:
                        st.success(f"✅ Macros are thermodynamically accurate ({accuracy:.1f}% of target)")
        
        # Show the meal plan
        st.markdown("""
        <div style="background: linear-gradient(135deg, #2D6A4F 0%, #40916C 100%); padding: 1.5rem; border-radius: 16px; color: white; margin: 1.5rem 0;">
            <h2 style="color: white !important; margin: 0;">🍽️ Your Weekly Meal Plan</h2>
        </div>
        """, unsafe_allow_html=True)
        
        plan_table(st.session_state["weekly_plan"])
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🛒 Generate Grocery List", use_container_width=True):
                from tools.grocery_list import build_list_from_plan
                groceries = build_list_from_plan(st.session_state["weekly_plan"])
                st.session_state["groceries"] = groceries
                st.success("✅ Grocery list ready! Check the Grocery List page.")
        
        with col2:
            if "plan_summary" in st.session_state:
                summary = st.session_state["plan_summary"]
                st.download_button(
                    "📄 Download Plan as Text",
                    data=summary,
                    file_name="meal_plan.txt",
                    mime="text/plain",
                    use_container_width=True
                )
    
    else:
        # Empty state
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: white; padding: 3rem; border-radius: 20px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.05);">
            <div style="font-size: 4rem; margin-bottom: 1rem;">🎯</div>
            <h3 style="color: #2D6A4F; margin-bottom: 1rem;">Ready to Get Your Personalized Plan?</h3>
            <p style="color: #52796F; max-width: 500px; margin: 0 auto 1.5rem auto;">
                Fill in your profile details in the sidebar and click "Calculate & Generate My Plan" to receive an AI-powered meal plan tailored to your goals!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # How it works cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="background: #FEF3C7; padding: 1.5rem; border-radius: 16px; height: 180px;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">1️⃣</div>
                <h4 style="color: #92400E; margin-bottom: 0.5rem;">Enter Your Info</h4>
                <p style="color: #A16207; font-size: 0.9rem; margin: 0;">Fill in weight, height, age, and activity level in the sidebar.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: #DBEAFE; padding: 1.5rem; border-radius: 16px; height: 180px;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">2️⃣</div>
                <h4 style="color: #1E40AF; margin-bottom: 0.5rem;">Set Your Goal</h4>
                <p style="color: #3B82F6; font-size: 0.9rem; margin: 0;">Choose fat loss, maintenance, or muscle gain for calorie adjustment.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="background: #D1FAE5; padding: 1.5rem; border-radius: 16px; height: 180px;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">3️⃣</div>
                <h4 style="color: #065F46; margin-bottom: 0.5rem;">Get Your Plan</h4>
                <p style="color: #10B981; font-size: 0.9rem; margin: 0;">Receive a personalized meal plan with exact macro targets!</p>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
