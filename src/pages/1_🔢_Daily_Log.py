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


def _render_day_summary(db: Database, day: date) -> None:
    st.subheader(day.strftime("%A, %b %d log"))
    meals = db.meals_for_date(day)
    if not meals:
        st.info("No foods logged for this date yet.")
        return
    totals = db.daily_totals(day)
    macro_ring_chart(totals)
    st.caption(
        f"Total: {totals['calories']:.0f} kcal | "
        f"{totals['protein_g']:.1f}g protein | "
        f"{totals['carb_g']:.1f}g carbs | "
        f"{totals['fat_g']:.1f}g fat"
    )
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

    for meal_type in MEAL_TYPES:
        if meal_type not in grouped:
            continue
        entry = grouped[meal_type]
        st.markdown(f"**{meal_type.title()} - {entry['calories']:.0f} kcal**")
        for payload in entry["entries"]:  # type: ignore[index]
            items = payload["items"]
            meal_id = payload["meal_id"]
            cols = st.columns([10, 1])
            with cols[0]:
                for item in items:
                    st.markdown(
                        f"- {item.quantity:g} {item.unit} {item.name} "
                        f"({item.calories:.0f} kcal; "
                        f"P {item.protein_g:.1f}g / C {item.carb_g:.1f}g / F {item.fat_g:.1f}g)"
                    )
            with cols[1]:
                if st.button("✕", key=f"delete-meal-{meal_id}", help="Remove this entry"):
                    db.delete_meal(meal_id)
                    st.experimental_rerun()


def main() -> None:
    st.title("Daily Meal Log")
    st.caption("Select a day, log foods by weight, and review past entries.")

    db = Database()
    selected_date = st.date_input("Date to view & log", value=date.today())

    st.subheader("Log Your Food")
    try:
        food_options = list_reference_foods()
    except FileNotFoundError as exc:
        st.error(str(exc))
        food_options = []
    if food_options:
        with st.form("log_known_food"):
            selected_food = st.selectbox("Food", food_options)
            grams = st.number_input(
                "Amount (grams)",
                min_value=1.0,
                value=100.0,
                step=5.0,
                key="known_food_grams",
            )
            known_meal_type = st.selectbox(
                "Meal type for this food", MEAL_TYPES, key="known_food_meal_type"
            )
            if grams > 0:
                preview = calculate_reference_macros(selected_food, grams)
                st.caption(
                    f"Estimated: {preview['calories']:.0f} kcal, "
                    f"{preview['protein_g']:.1f}g protein, "
                    f"{preview['carb_g']:.1f}g carbs, "
                    f"{preview['fat_g']:.1f}g fat"
                )
            submit_known = st.form_submit_button("Log This Food")
        if submit_known:
            try:
                log_reference_food(
                    selected_food,
                    grams,
                    selected_date,
                    known_meal_type,
                    db=db,
                )
                st.success(
                    f"Logged {grams:g} g of {selected_food} on {selected_date:%b %d}."
                )
            except ValueError as exc:
                st.error(str(exc))
    else:
        st.info("Add foods to the reference dataset below before using the gram-based logger.")

    _render_day_summary(db, selected_date)

    st.divider()
    st.subheader("Add Missing Foods")
    st.caption(
        "Keep the ingredient list fresh by adding macros for any gram amount when something isn't found."
    )
    with st.form("add_food_form"):
        food_name = st.text_input("Food name", placeholder="Cheese crackers")
        reference_grams = st.number_input(
            "Reference amount (grams)", min_value=1.0, value=100.0, step=5.0
        )
        calories = st.number_input(
            "Calories for this amount", min_value=0.0, value=100.0, step=5.0
        )
        protein = st.number_input(
            "Protein (g) for this amount", min_value=0.0, value=5.0, step=0.5
        )
        carbs = st.number_input(
            "Carbs (g) for this amount", min_value=0.0, value=10.0, step=0.5
        )
        fat = st.number_input(
            "Fat (g) for this amount", min_value=0.0, value=3.0, step=0.5
        )
        submitted = st.form_submit_button("Add to Food Reference")
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
            st.success(
                f"Added {food_name.strip() or 'new food'} "
                f"(scaled from {reference_grams:g} g) to the nutrition reference."
            )
        except ValueError as exc:
            st.error(str(exc))


if __name__ == "__main__":
    main()
