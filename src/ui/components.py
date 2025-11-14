"""Reusable Streamlit components."""
from __future__ import annotations

from typing import Dict, Iterable

try:  # pragma: no cover
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None  # type: ignore

import streamlit as st

from core.schemas import MacroTargets, PlanDay


def macro_ring_chart(totals: Dict[str, float], targets: Dict[str, float] | None = None) -> None:
    values = {
        "Calories": totals.get("calories", 0),
        "Protein": totals.get("protein_g", 0),
        "Carbs": totals.get("carb_g", 0),
        "Fat": totals.get("fat_g", 0),
    }
    if pd:
        df = pd.DataFrame({"macro": list(values.keys()), "value": list(values.values())})
        st.bar_chart(df.set_index("macro"))
    else:  # pragma: no cover
        for macro, value in values.items():
            st.write(f"{macro}: {value:.1f}")
    if targets:
        st.caption(
            "Targets: "
            f"{int(targets.get('calories', 0))} kcal, "
            f"{int(targets.get('protein', 0))}g protein"
        )


def targets_sidebar(defaults: MacroTargets | None = None) -> MacroTargets:
    st.sidebar.header("Your Targets")
    calories = st.sidebar.number_input("Daily Calories", value=defaults.calories if defaults else 2000)
    protein = st.sidebar.number_input("Protein (g)", value=defaults.protein if defaults else 140)
    carbs = st.sidebar.number_input("Carbs (g)", value=defaults.carbs if defaults else 200)
    fat = st.sidebar.number_input("Fat (g)", value=defaults.fat if defaults else 60)
    diet_tags = st.sidebar.text_input(
        "Diet Tags", value=",".join(defaults.diet_tags) if defaults else "high-protein"
    )
    exclusions = st.sidebar.text_input(
        "Exclusions", value=",".join(defaults.exclusions) if defaults else ""
    )
    meals_per_day = st.sidebar.selectbox("Meals per day", options=[3, 4], index=0)
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
    for day in plan:
        st.subheader(day.date.strftime("%A, %b %d"))
        for meal in day.meals:
            totals = meal.totals
            st.markdown(
                f"**{meal.meal_type.title()}** - {meal.name}"
                f" ({totals['calories']:.0f} kcal, {totals['protein_g']:.0f}g protein)"
            )
            if meal.notes:
                st.caption(meal.notes)
        st.write("Totals:", day.totals())


__all__ = ["macro_ring_chart", "targets_sidebar", "plan_table"]
