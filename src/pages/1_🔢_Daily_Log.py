"""Daily Meal Log page with enhanced UI."""
from __future__ import annotations

from datetime import date

import streamlit as st

from collections import defaultdict
from typing import Dict

from core.db import Database
from tools.calorie_tracker import (
    add_reference_food,
    calculate_reference_macros,
    list_reference_foods,
    log_reference_food,
)
from ui.components import macro_ring_chart

MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack"]
MEAL_ICONS = {
    "breakfast": "🌅",
    "lunch": "☀️",
    "dinner": "🌙",
    "snack": "🍎"
}
MEAL_COLORS = {
    "breakfast": "#F59E0B",
    "lunch": "#10B981",
    "dinner": "#6366F1",
    "snack": "#EC4899"
}


def _render_day_summary(db: Database, day: date) -> None:
    """Render the daily meal summary with enhanced styling."""
    meals = db.meals_for_date(day)
    
    if not meals:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); padding: 2rem; border-radius: 16px; text-align: center; margin: 1rem 0;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">🍽️</div>
            <h3 style="color: #92400E; margin-bottom: 0.5rem;">No meals logged yet</h3>
            <p style="color: #A16207;">Start tracking your nutrition by logging your first meal above!</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    totals = db.daily_totals(day)
    
    # Summary header
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #2D6A4F 0%, #40916C 100%); padding: 1.5rem 2rem; border-radius: 16px; color: white; margin-bottom: 1.5rem;">
        <h3 style="color: white !important; margin: 0 0 0.5rem 0;">📊 Daily Summary - {day.strftime("%A, %B %d")}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Macro cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); padding: 1.25rem; border-radius: 14px; text-align: center;">
            <p style="color: #92400E; font-size: 0.85rem; margin: 0;">🔥 Calories</p>
            <h2 style="color: #78350F; margin: 0.5rem 0 0 0; font-size: 1.8rem;">{totals['calories']:.0f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%); padding: 1.25rem; border-radius: 14px; text-align: center;">
            <p style="color: #1E40AF; font-size: 0.85rem; margin: 0;">💪 Protein</p>
            <h2 style="color: #1E3A8A; margin: 0.5rem 0 0 0; font-size: 1.8rem;">{totals['protein_g']:.1f}g</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%); padding: 1.25rem; border-radius: 14px; text-align: center;">
            <p style="color: #065F46; font-size: 0.85rem; margin: 0;">🍞 Carbs</p>
            <h2 style="color: #064E3B; margin: 0.5rem 0 0 0; font-size: 1.8rem;">{totals['carb_g']:.1f}g</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #FCE7F3 0%, #FBCFE8 100%); padding: 1.25rem; border-radius: 14px; text-align: center;">
            <p style="color: #9D174D; font-size: 0.85rem; margin: 0;">🥑 Fat</p>
            <h2 style="color: #831843; margin: 0.5rem 0 0 0; font-size: 1.8rem;">{totals['fat_g']:.1f}g</h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Visual chart
    macro_ring_chart(totals)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Group meals by type
    grouped: Dict[str, Dict[str, object]] = defaultdict(
        lambda: {
            "calories": 0.0,
            "protein_g": 0.0,
            "carb_g": 0.0,
            "fat_g": 0.0,
            "entries": [],
        }
    )
    for meal in meals:
        entry = grouped[meal["meal_type"]]
        entry["calories"] += meal.get("calories", meal.get("total_cal", 0.0))
        entry["protein_g"] += meal.get("protein_g", 0.0)
        entry["carb_g"] += meal.get("carb_g", 0.0)
        entry["fat_g"] += meal.get("fat_g", 0.0)
        entry["entries"].append(
            {
                "meal_id": meal["id"],
                "items": db.meal_items(meal["id"]),
            }
        )

    # Render each meal type
    for meal_type in MEAL_TYPES:
        if meal_type not in grouped:
            continue
        
        entry = grouped[meal_type]
        icon = MEAL_ICONS.get(meal_type, "🍽️")
        color = MEAL_COLORS.get(meal_type, "#6B7280")
        
        st.markdown(f"""
        <div style="background: white; padding: 1.25rem; border-radius: 14px; margin-bottom: 1rem; border-left: 4px solid {color}; box-shadow: 0 2px 10px rgba(0,0,0,0.03);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                <h4 style="margin: 0; color: #1F2937;">{icon} {meal_type.title()}</h4>
                <span style="background: {color}20; color: {color}; padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: 600; font-size: 0.9rem;">
                    {entry['calories']:.0f} kcal
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        for payload in entry["entries"]:
            items = payload["items"]
            meal_id = payload["meal_id"]
            
            for item in items:
                col1, col2 = st.columns([10, 1])
                with col1:
                    st.markdown(f"""
                    <div style="padding: 0.5rem 1rem; margin: 0.25rem 0;">
                        <span style="color: #374151;">• {item.quantity:g} {item.unit} <strong>{item.name}</strong></span>
                        <span style="color: #6B7280; font-size: 0.85rem;"> — {item.calories:.0f} kcal | P: {item.protein_g:.1f}g | C: {item.carb_g:.1f}g | F: {item.fat_g:.1f}g</span>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("🗑️", key=f"delete-meal-{meal_id}-{item.name}", help="Remove this entry"):
                        db.delete_meal(meal_id)
                        st.rerun()


def main() -> None:
    # Page header
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="margin-bottom: 0.5rem;">🔢 Daily Meal Log</h1>
        <p style="color: #52796F; font-size: 1.1rem;">Track your nutrition by logging foods with precise gram measurements.</p>
    </div>
    """, unsafe_allow_html=True)

    db = Database()
    
    # Date selector with nice styling
    st.markdown("""
    <div style="background: white; padding: 1.5rem; border-radius: 16px; margin-bottom: 1.5rem; box-shadow: 0 2px 10px rgba(0,0,0,0.03);">
        <h4 style="color: #2D6A4F; margin-bottom: 1rem;">📅 Select Date</h4>
    </div>
    """, unsafe_allow_html=True)
    
    selected_date = st.date_input("", value=date.today(), label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Log food section
    st.markdown("""
    <div style="background: linear-gradient(135deg, #D8F3DC 0%, #B7E4C7 100%); padding: 1.5rem; border-radius: 16px; margin-bottom: 1rem;">
        <h3 style="color: #1B4332; margin: 0;">➕ Log Your Food</h3>
        <p style="color: #2D6A4F; margin: 0.5rem 0 0 0; font-size: 0.9rem;">Select a food from our database and enter the amount in grams.</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        food_options = list_reference_foods()
    except FileNotFoundError as exc:
        st.error(str(exc))
        food_options = []
    
    if food_options:
        with st.form("log_known_food"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                selected_food = st.selectbox("🍎 Food Item", food_options, help="Choose from our database of 200+ foods")
            
            with col2:
                grams = st.number_input(
                    "⚖️ Amount (grams)",
                    min_value=1.0,
                    value=100.0,
                    step=5.0,
                    key="known_food_grams",
                )
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                known_meal_type = st.selectbox(
                    "🕐 Meal Type", 
                    MEAL_TYPES, 
                    key="known_food_meal_type",
                    format_func=lambda x: f"{MEAL_ICONS.get(x, '')} {x.title()}"
                )
            
            with col2:
                if grams > 0:
                    preview = calculate_reference_macros(selected_food, grams)
                    st.markdown(f"""
                    <div style="background: white; padding: 1rem; border-radius: 10px; margin-top: 1.4rem;">
                        <span style="color: #6B7280; font-size: 0.9rem;">📊 Preview: </span>
                        <span style="color: #2D6A4F; font-weight: 600;">
                            {preview['calories']:.0f} kcal • {preview['protein_g']:.1f}g protein • {preview['carb_g']:.1f}g carbs • {preview['fat_g']:.1f}g fat
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            submit_known = st.form_submit_button("✅ Log This Food", use_container_width=True, type="primary")
        
        if submit_known:
            try:
                log_reference_food(
                    selected_food,
                    grams,
                    selected_date,
                    known_meal_type,
                    db=db,
                )
                st.success(f"✅ Logged {grams:g}g of {selected_food} for {known_meal_type}!")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    else:
        st.warning("📝 Add foods to the reference dataset below before using the gram-based logger.")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Daily summary
    _render_day_summary(db, selected_date)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Add missing foods section
    with st.expander("🆕 Can't find your food? Add it here!", expanded=False):
        st.markdown("""
        <p style="color: #52796F; margin-bottom: 1rem;">
            Extend our food database by adding nutrition information for any food item.
            Enter the macros for your specified portion size - we'll automatically scale to per-100g values.
        </p>
        """, unsafe_allow_html=True)
        
        with st.form("add_food_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                food_name = st.text_input("🏷️ Food Name", placeholder="e.g., Cheese crackers")
            with col2:
                reference_grams = st.number_input(
                    "⚖️ Reference Amount (grams)", 
                    min_value=1.0, 
                    value=100.0, 
                    step=5.0,
                    help="The portion size your macros are based on"
                )
            
            st.markdown("##### Nutrition Values (for the amount above)")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                calories = st.number_input(
                    "🔥 Calories", min_value=0.0, value=100.0, step=5.0
                )
            with col2:
                protein = st.number_input(
                    "💪 Protein (g)", min_value=0.0, value=5.0, step=0.5
                )
            with col3:
                carbs = st.number_input(
                    "🍞 Carbs (g)", min_value=0.0, value=10.0, step=0.5
                )
            with col4:
                fat = st.number_input(
                    "🥑 Fat (g)", min_value=0.0, value=3.0, step=0.5
                )
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("➕ Add to Food Database", use_container_width=True)
        
        if submitted:
            try:
                add_reference_food(
                    food_name,
                    calories,
                    protein,
                    carbs,
                    fat,
                    reference_grams=reference_grams,
                )
                st.success(f"✅ Added **{food_name.strip()}** to the nutrition database!")
            except ValueError as exc:
                st.error(str(exc))


if __name__ == "__main__":
    main()
