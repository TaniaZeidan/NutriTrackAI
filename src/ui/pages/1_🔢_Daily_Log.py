from __future__ import annotations

from datetime import date

import streamlit as st

from ...core.db import Database
from ...core.utils import macro_totals
from ...tools.calorie_tracker import log_meal
from ..components import macro_ring_chart


def main() -> None:
    st.title("Daily Meal Log")
    description = st.text_area("Describe what you ate", placeholder="1 cup Greek yogurt with berries")
    meal_type = st.selectbox("Meal type", ["breakfast", "lunch", "dinner", "snack"])
    meal_date = st.date_input("Date", value=date.today())
    if st.button("Log Meal") and description:
        try:
            result = log_meal(description=description, date=meal_date, meal_type=meal_type)
            st.success("Meal logged")
            st.json(result["meal"].model_dump())
            macro_ring_chart(result["daily_totals"])
        except ValueError as exc:
            st.error(str(exc))

    if st.checkbox("Show today's meals"):
        db = Database()
        meals = db.meals_for_date(date.today())
        st.write(meals)


if __name__ == "__main__":
    main()
