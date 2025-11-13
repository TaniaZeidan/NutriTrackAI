from __future__ import annotations

import streamlit as st

from tools.cooking_assistant import recipe_steps


def main() -> None:
    st.title("Cooking Assistant")
    query = st.text_input("Recipe name or ingredient", "Salmon")
    servings = st.number_input("Servings", min_value=1, value=2)
    if st.button("Get Steps") and query:
        try:
            result = recipe_steps(query, servings=int(servings))
            for step in result["steps"]:
                st.write(f"Step {step.idx}: {step.instruction}")
                if step.tips:
                    st.caption("Tips: " + "; ".join(step.tips))
                if step.substitutions:
                    st.caption("Substitutions: " + "; ".join(step.substitutions))
        except ValueError as exc:
            st.error(str(exc))


if __name__ == "__main__":
    main()
