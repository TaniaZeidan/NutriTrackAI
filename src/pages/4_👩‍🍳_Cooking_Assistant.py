"""Enhanced Cooking Assistant page wired to the NutriTrackAI multi-agent graph."""
from __future__ import annotations

import streamlit as st

from agent.cooking_agent import CookingAgent


@st.cache_resource
def _create_agent():
    """Create a fresh CookingAgent (cached until Streamlit restarts)."""
    return CookingAgent()


def _ensure_session() -> None:
    """Initialize session state variables."""
    if "cooking_chat" not in st.session_state:
        st.session_state["cooking_chat"] = []
    if "cooking_servings" not in st.session_state:
        st.session_state["cooking_servings"] = 2
    try:
        st.session_state["cooking_agent"] = _create_agent()
    except Exception as exc:
        st.error(f"Failed to initialize the cooking agent: {exc}")
        st.session_state["cooking_agent"] = None


def _render_state_panel(state: dict) -> None:
    """Render the multi-agent state debug panel below a response."""
    if not state:
        return
    agent_name = state.get("current_agent", "unknown")
    confidence = state.get("confidence")
    query_type = state.get("query_type")
    tool_calls = state.get("tool_calls_count", 0)
    needs_review = state.get("needs_review", False)
    msg_count = state.get("message_count", 0)

    agent_labels = {
        "cooking": "Cooking Agent",
        "nutrition": "Nutrition Agent",
        "general": "Cooking Agent (fallback)",
    }
    agent_display = agent_labels.get(agent_name, agent_name or "N/A")

    conf_pct = f"{confidence:.0%}" if confidence is not None else "N/A"

    cols = st.columns(4)
    with cols[0]:
        st.metric("Routed To", agent_display)
    with cols[1]:
        st.metric("Confidence", conf_pct)
    with cols[2]:
        st.metric("Tool Calls", tool_calls)
    with cols[3]:
        st.metric("Messages", msg_count)

    if needs_review:
        st.warning("Low-confidence classification -- response may need review.")


def _process_message(prompt: str) -> None:
    """Process a sidebar-button message and store result."""
    st.session_state["cooking_chat"].append({"role": "user", "content": prompt})

    agent = st.session_state.get("cooking_agent")
    servings = st.session_state.get("cooking_servings", 2)
    state = {}

    if agent:
        try:
            result = agent.chat_with_state(prompt, servings=servings)
            response = result["response"]
            state = result.get("state", {})
        except Exception as exc:
            response = (
                f"I encountered an error: {exc}\n\n"
                "Please try rephrasing or check that your Google Gemini API key is configured."
            )
    else:
        response = "Cooking agent is not available. Please check your setup."

    st.session_state["cooking_chat"].append({
        "role": "assistant",
        "content": response,
        "state": state,
    })


def main() -> None:
    st.title("Cooking Assistant")
    st.caption(
        "Your AI-powered cooking companion. Ask for recipes, cooking instructions, "
        "ingredient amounts, and get detailed macro information for every meal."
    )

    _ensure_session()

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

        show_state = st.toggle("Show agent state", value=True,
                               help="Display routing and state info for each response.")

        st.divider()
        st.subheader("Quick Actions")

        if st.button("Search Recipes", use_container_width=True):
            _process_message("Show me some healthy high-protein recipes")
            st.rerun()

        if st.button("Healthy Meals", use_container_width=True):
            _process_message("Give me healthy meal ideas under 500 calories")
            st.rerun()

        if st.button("High Protein", use_container_width=True):
            _process_message("Show me high protein recipes with at least 30g protein per serving")
            st.rerun()

        st.divider()

        if st.button("Clear Chat", use_container_width=True):
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
            if message["role"] == "assistant" and show_state:
                state = message.get("state")
                if state:
                    with st.expander("Agent State", expanded=False):
                        _render_state_panel(state)

    if prompt := st.chat_input("Ask for a recipe, cooking instructions, or ingredient amounts..."):
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching recipes and preparing your answer..."):
                agent = st.session_state.get("cooking_agent")
                servings_val = st.session_state["cooking_servings"]
                state = {}

                if agent:
                    try:
                        result = agent.chat_with_state(prompt, servings=servings_val)
                        response = result["response"]
                        state = result.get("state", {})
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

                if show_state and state:
                    with st.expander("Agent State", expanded=True):
                        _render_state_panel(state)

        st.session_state["cooking_chat"].append({"role": "user", "content": prompt})
        st.session_state["cooking_chat"].append({
            "role": "assistant",
            "content": response,
            "state": state,
        })
        st.rerun()


if __name__ == "__main__":
    main()
