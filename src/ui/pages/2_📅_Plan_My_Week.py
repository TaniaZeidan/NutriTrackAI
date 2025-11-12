from __future__ import annotations

import streamlit as st

from ...core.schemas import MacroTargets
from ...tools.meal_planner import generate_plan
from ...tools.grocery_list import build_list_from_plan
from ..components import plan_table, targets_sidebar


def main() -> None:
    st.title("Plan My Week")
    targets = targets_sidebar(MacroTargets(calories=2000, protein=140, carbs=220, fat=60))
    if st.button("Generate Plan"):
        plan = generate_plan(targets, days=7)
        st.session_state["weekly_plan"] = plan
        st.success("Plan generated")
    plan = st.session_state.get("weekly_plan")
    if plan:
        plan_table(plan)
        if st.button("Build Grocery List"):
            groceries = build_list_from_plan(plan)
            st.session_state["groceries"] = groceries
            st.success("Grocery list ready. Switch to the Grocery List page.")


if __name__ == "__main__":
    main()
