from __future__ import annotations

import streamlit as st

from ...tools.grocery_list import build_list_from_plan, export_csv
from ..components import plan_table


def main() -> None:
    st.title("Grocery List")
    plan = st.session_state.get("weekly_plan")
    if not plan:
        st.info("Generate a plan first from the Plan My Week page.")
        return
    groceries = build_list_from_plan(plan)
    for item in groceries:
        st.write(f"[{item.category}] {item.name}: {item.quantity:.1f} {item.unit}")
    csv_data = export_csv(groceries)
    st.download_button("Download CSV", data=csv_data, file_name="grocery_list.csv")


if __name__ == "__main__":
    main()
