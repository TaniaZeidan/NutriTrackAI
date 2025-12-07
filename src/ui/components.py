"""Reusable Streamlit components with enhanced styling."""
from __future__ import annotations

from typing import Dict, Iterable

try:  # pragma: no cover
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None  # type: ignore

import streamlit as st

from core.schemas import MacroTargets, PlanDay


MEAL_TYPE_ICONS = {
    "breakfast": "🌅",
    "lunch": "☀️",
    "dinner": "🌙",
    "snack": "🍎"
}

MEAL_TYPE_COLORS = {
    "breakfast": {"primary": "#F59E0B", "bg": "#FEF3C7"},
    "lunch": {"primary": "#10B981", "bg": "#D1FAE5"},
    "dinner": {"primary": "#6366F1", "bg": "#E0E7FF"},
    "snack": {"primary": "#EC4899", "bg": "#FCE7F3"}
}


def macro_ring_chart(totals: Dict[str, float], targets: Dict[str, float] | None = None) -> None:
    """Display macros with a beautiful horizontal bar visualization."""
    
    calories = totals.get("calories", 0)
    protein = totals.get("protein_g", 0)
    carbs = totals.get("carb_g", 0)
    fat = totals.get("fat_g", 0)
    
    # Calculate macro percentages of calories
    protein_cals = protein * 4
    carb_cals = carbs * 4
    fat_cals = fat * 9
    total_macro_cals = protein_cals + carb_cals + fat_cals
    
    if total_macro_cals > 0:
        protein_pct = (protein_cals / total_macro_cals) * 100
        carb_pct = (carb_cals / total_macro_cals) * 100
        fat_pct = (fat_cals / total_macro_cals) * 100
    else:
        protein_pct = carb_pct = fat_pct = 33.3
    
    st.markdown(f"""
    <div style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0;">
        <h4 style="color: #0F172A; margin-bottom: 1rem; font-size: 0.95rem;">📊 Macro Breakdown</h4>
        
        <!-- Stacked bar visualization -->
        <div style="height: 20px; border-radius: 10px; overflow: hidden; display: flex; margin-bottom: 1.25rem; background: #F1F5F9;">
            <div style="width: {protein_pct}%; background: #3B82F6; transition: width 0.3s;"></div>
            <div style="width: {carb_pct}%; background: #22C55E; transition: width 0.3s;"></div>
            <div style="width: {fat_pct}%; background: #EC4899; transition: width 0.3s;"></div>
        </div>
        
        <!-- Legend -->
        <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 0.75rem;">
            <div style="text-align: center;">
                <div style="display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.2rem;">
                    <div style="width: 10px; height: 10px; background: #3B82F6; border-radius: 2px;"></div>
                    <span style="color: #64748B; font-size: 0.8rem;">Protein</span>
                </div>
                <span style="color: #0F172A; font-weight: 600; font-size: 0.9rem;">{protein:.1f}g</span>
                <span style="color: #94A3B8; font-size: 0.75rem;"> ({protein_pct:.0f}%)</span>
            </div>
            <div style="text-align: center;">
                <div style="display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.2rem;">
                    <div style="width: 10px; height: 10px; background: #22C55E; border-radius: 2px;"></div>
                    <span style="color: #64748B; font-size: 0.8rem;">Carbs</span>
                </div>
                <span style="color: #0F172A; font-weight: 600; font-size: 0.9rem;">{carbs:.1f}g</span>
                <span style="color: #94A3B8; font-size: 0.75rem;"> ({carb_pct:.0f}%)</span>
            </div>
            <div style="text-align: center;">
                <div style="display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.2rem;">
                    <div style="width: 10px; height: 10px; background: #EC4899; border-radius: 2px;"></div>
                    <span style="color: #64748B; font-size: 0.8rem;">Fat</span>
                </div>
                <span style="color: #0F172A; font-weight: 600; font-size: 0.9rem;">{fat:.1f}g</span>
                <span style="color: #94A3B8; font-size: 0.75rem;"> ({fat_pct:.0f}%)</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if targets:
        st.markdown(f"""
        <div style="background: #F0FDF4; padding: 0.75rem 1rem; border-radius: 8px; margin-top: 1rem; border: 1px solid #BBF7D0;">
            <span style="color: #166534; font-size: 0.85rem;">
                🎯 <strong>Targets:</strong> {int(targets.get('calories', 0))} kcal • {int(targets.get('protein', 0))}g protein
            </span>
        </div>
        """, unsafe_allow_html=True)


def targets_sidebar(defaults: MacroTargets | None = None) -> MacroTargets:
    """Render a styled sidebar for macro targets input."""
    
    st.markdown("""
    <p style="font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px; color: #94A3B8; margin: 0 0 0.75rem 0; font-weight: 600;">🎯 Your Targets</p>
    """, unsafe_allow_html=True)
    
    calories = st.number_input(
        "🔥 Daily Calories", 
        value=defaults.calories if defaults else 2000,
        min_value=1200,
        max_value=5000,
        step=50
    )
    protein = st.number_input(
        "💪 Protein (g)", 
        value=defaults.protein if defaults else 140,
        min_value=50,
        max_value=300,
        step=5
    )
    carbs = st.number_input(
        "🍞 Carbs (g)", 
        value=defaults.carbs if defaults else 200,
        min_value=50,
        max_value=500,
        step=5
    )
    fat = st.number_input(
        "🥑 Fat (g)", 
        value=defaults.fat if defaults else 60,
        min_value=20,
        max_value=200,
        step=5
    )
    
    st.markdown("---")
    
    diet_tags = st.text_input(
        "🥗 Diet Tags", 
        value=",".join(defaults.diet_tags) if defaults else "high-protein",
        placeholder="e.g., vegetarian, keto",
        help="Comma-separated dietary preferences"
    )
    exclusions = st.text_input(
        "🚫 Exclusions", 
        value=",".join(defaults.exclusions) if defaults else "",
        placeholder="e.g., dairy, gluten",
        help="Foods to avoid"
    )
    meals_per_day = st.selectbox(
        "🍽️ Meals per day", 
        options=[3, 4], 
        index=0,
        format_func=lambda x: f"{x} meals"
    )
    
    return MacroTargets(
        calories=int(calories),
        protein=int(protein),
        carbs=int(carbs),
        fat=int(fat),
        diet_tags=[t.strip() for t in diet_tags.split(",") if t.strip()],
        exclusions=[e.strip() for e in exclusions.split(",") if e.strip()],
        meals_per_day=int(meals_per_day),
    )


def plan_table(plan: Iterable[PlanDay]) -> None:
    """Display meal plan with beautiful card-based layout."""
    
    for day in plan:
        day_totals = day.totals()
        
        # Day header
        st.markdown(f"""
        <div style="background: white; padding: 1.25rem; border-radius: 12px; margin-bottom: 1rem; border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.75rem;">
                <h3 style="color: #0F172A; margin: 0; font-size: 1.1rem;">📅 {day.date.strftime("%A, %B %d")}</h3>
                <div style="background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%); color: white; padding: 0.4rem 1rem; border-radius: 20px; font-size: 0.8rem; font-weight: 500;">
                    {day_totals['calories']:.0f} kcal • P {day_totals['protein_g']:.0f}g • C {day_totals['carb_g']:.0f}g • F {day_totals['fat_g']:.0f}g
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Meals grid
        cols = st.columns(len(day.meals))
        
        for idx, meal in enumerate(day.meals):
            totals = meal.totals
            icon = MEAL_TYPE_ICONS.get(meal.meal_type, "🍽️")
            colors = MEAL_TYPE_COLORS.get(meal.meal_type, {"primary": "#6B7280", "bg": "#F3F4F6"})
            
            with cols[idx]:
                st.markdown(f"""
                <div style="background: #F8FAFC; padding: 1.25rem; border-radius: 12px; border: 1px solid #E2E8F0; height: 100%;">
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                        <span style="font-size: 1.25rem;">{icon}</span>
                        <span style="color: {colors['primary']}; font-weight: 600; text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.5px;">{meal.meal_type}</span>
                    </div>
                    <h4 style="color: #0F172A; margin: 0 0 0.75rem 0; font-size: 0.95rem; line-height: 1.3; font-weight: 600;">{meal.name}</h4>
                    <div style="background: white; padding: 0.75rem; border-radius: 8px; border: 1px solid #E2E8F0;">
                        <p style="margin: 0; font-size: 0.8rem; color: #64748B;">
                            <strong style="color: #0F172A;">{totals['calories']:.0f}</strong> kcal<br>
                            <span style="color: #3B82F6;">P {totals['protein_g']:.0f}g</span> · 
                            <span style="color: #22C55E;">C {totals['carb_g']:.0f}g</span> · 
                            <span style="color: #EC4899;">F {totals['fat_g']:.0f}g</span>
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if meal.notes:
                    st.caption(f"🏷️ {meal.notes}")
        
        st.markdown("<br>", unsafe_allow_html=True)


__all__ = ["macro_ring_chart", "targets_sidebar", "plan_table"]
