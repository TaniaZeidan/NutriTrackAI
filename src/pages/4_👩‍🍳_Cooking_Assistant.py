"""Enhanced Cooking Assistant page wired to the NutriTrackAI agent."""
from __future__ import annotations

import streamlit as st

from agent.cooking_agent import CookingAgent


def _ensure_session() -> None:
    """Initialize session state variables."""
    if "cooking_chat" not in st.session_state:
        st.session_state["cooking_chat"] = []
    if "cooking_servings" not in st.session_state:
        st.session_state["cooking_servings"] = 2
    if "cooking_agent" not in st.session_state:
        try:
            st.session_state["cooking_agent"] = CookingAgent()
        except Exception as exc:
            st.error("Failed to initialize the cooking agent. Please check your API key setup.")
            st.session_state["cooking_agent"] = None
            print(f"Cooking agent init error: {exc}")


def _process_message(prompt: str) -> None:
    """Process a message and get agent response."""
    st.session_state["cooking_chat"].append({"role": "user", "content": prompt})

    agent = st.session_state.get("cooking_agent")
    servings = st.session_state.get("cooking_servings", 2)

    if agent:
        try:
            response = agent.chat(prompt, servings=servings)
        except Exception as exc:
            response = (
                f"I encountered an error: {exc}\n\n"
                "Please try rephrasing or check that your Google Gemini API key is configured."
            )
    else:
        response = "Cooking agent is not available. Please check your setup."

    st.session_state["cooking_chat"].append({"role": "assistant", "content": response})


def main() -> None:
    st.title("👩‍🍳 Cooking Assistant")
    st.caption(
        "Your AI-powered cooking companion. Ask for recipes, cooking instructions, "
        "ingredient amounts, and get detailed macro information for every meal."
    )

    _ensure_session()

    # Sidebar controls
    with st.sidebar:
        st.header("Settings")
        servings = st.number_input(
            "Target servings",
            min_value=1,
            max_value=8,
            value=st.session_state["cooking_servings"],
            step=1,
            help="All recipes and macros will be scaled to this number of servings.",
        )
        st.session_state["cooking_servings"] = int(servings)

        st.divider()
        st.subheader("Quick Actions")

        if st.button("🔍 Search Recipes", use_container_width=True):
            _process_message("Show me some healthy high-protein recipes")
            st.rerun()

        if st.button("🥗 Healthy Meals", use_container_width=True):
            _process_message("Give me healthy meal ideas under 500 calories")
            st.rerun()

        if st.button("💪 High Protein", use_container_width=True):
            _process_message("Show me high protein recipes with at least 30g protein per serving")
            st.rerun()

        st.divider()

        if st.button("🧹 Clear Chat", use_container_width=True):
            st.session_state["cooking_chat"] = []
            st.rerun()

    history = st.session_state["cooking_chat"]

    if not history:
        st.info("Welcome! Ask me anything about cooking, recipes, or ingredients.")
        st.markdown("### Try asking:")
        st.markdown("- *How do I make Grilled Chicken Bowl?*")
        st.markdown("- *Give me a high-protein recipe with salmon*")
        st.markdown("- *What are the ingredients and amounts for Greek Yogurt Parfait?*")
        st.markdown("- *Show me vegetarian recipes*")

    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask for a recipe, cooking instructions, or ingredient amounts..."):
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching recipes and preparing your answer..."):
                agent = st.session_state.get("cooking_agent")
                servings = st.session_state["cooking_servings"]

                if agent:
                    try:
                        response = agent.chat(prompt, servings=servings)
                        st.markdown(response)
                    except Exception as exc:
                        error_msg = (
                            f"I encountered an error: {exc}\n\n"
                            "Please try:\n"
                            "- Rephrasing your question\n"
                            "- Asking about a specific recipe name\n"
                            "- Checking if your API key is set correctly"
                        )
                        st.error(str(exc))
                        st.markdown(error_msg)
                        response = error_msg
                else:
                    response = "Cooking agent is not available. Please restart the app."
                    st.error(response)

        st.session_state["cooking_chat"].append({"role": "user", "content": prompt})
        st.session_state["cooking_chat"].append({"role": "assistant", "content": response})
        st.rerun()


if __name__ == "__main__":
    main()
