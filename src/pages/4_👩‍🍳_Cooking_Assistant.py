from __future__ import annotations

from typing import Dict, List

import streamlit as st

from tools.cooking_assistant import grounded_cooking_response


def _ensure_session() -> None:
    if "cooking_chat" not in st.session_state:
        st.session_state["cooking_chat"] = []
    if "cooking_servings" not in st.session_state:
        st.session_state["cooking_servings"] = 2


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
                        "servings": st.session_state["cooking_servings"],
                    }
                    st.markdown(reply["content"])
                except ValueError as exc:
                    reply = {"role": "assistant", "content": str(exc)}
                    st.markdown(reply["content"])
        history.append(reply)


if __name__ == "__main__":
    main()
