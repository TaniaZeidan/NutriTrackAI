from __future__ import annotations

from typing import Dict, List

import streamlit as st

from tools.cooking_assistant import grounded_cooking_response


def _ensure_session() -> None:
    if "cooking_chat" not in st.session_state:
        st.session_state["cooking_chat"] = []
    if "cooking_servings" not in st.session_state:
        st.session_state["cooking_servings"] = 2


def _render_sources(sources: List[Dict[str, object]], servings: int) -> None:
    if not sources:
        return
    with st.expander("Recipe sources", expanded=False):
        for src in sources:
            per_serving = src["per_serving_macros"]
            scaled = src["scaled_macros"]
            st.markdown(
                f"**{src['title']}** - per serving: "
                f"{per_serving['calories']:.0f} kcal, "
                f"{per_serving['protein_g']:.0f}g protein, "
                f"{per_serving['carb_g']:.0f}g carbs, "
                f"{per_serving['fat_g']:.0f}g fat. "
                f"For {servings} servings: "
                f"{scaled['calories']:.0f} kcal, "
                f"{scaled['protein_g']:.0f}g protein, "
                f"{scaled['carb_g']:.0f}g carbs, "
                f"{scaled['fat_g']:.0f}g fat."
            )


def main() -> None:
    st.title("Cooking Assistant")
    st.caption("Chat with NutriTrackAI to get grounded, macro-aware cooking guidance.")
    _ensure_session()

    servings = st.number_input(
        "Target servings",
        min_value=1,
        max_value=8,
        value=st.session_state["cooking_servings"],
        step=1,
        help="Responses will scale macros and instructions to this serving count.",
    )
    st.session_state["cooking_servings"] = int(servings)

    history = st.session_state["cooking_chat"]
    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                _render_sources(
                    message["sources"],
                    message.get("servings", st.session_state["cooking_servings"]),
                )

    if prompt := st.chat_input("Ask for a recipe, macro target, or cooking style."):
        with st.chat_message("user"):
            st.markdown(prompt)
        history.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("NutriTrack is searching recipes..."):
                try:
                    result = grounded_cooking_response(
                        prompt,
                        servings=st.session_state["cooking_servings"],
                    )
                    reply = {
                        "role": "assistant",
                        "content": result["answer"],
                        "sources": result.get("sources", []),
                        "servings": st.session_state["cooking_servings"],
                    }
                    st.markdown(reply["content"])
                    if reply["sources"]:
                        _render_sources(reply["sources"], reply["servings"])
                except ValueError as exc:
                    reply = {"role": "assistant", "content": str(exc)}
                    st.markdown(reply["content"])
        history.append(reply)


if __name__ == "__main__":
    main()
