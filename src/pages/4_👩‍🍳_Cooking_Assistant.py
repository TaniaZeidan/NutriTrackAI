"""Enhanced Cooking Assistant page with proper agent integration."""
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
        except Exception as e:
            st.error(f"Failed to initialize cooking agent: {e}")
            st.session_state["cooking_agent"] = None


def _process_message(prompt: str) -> None:
    """Process a message and get agent response."""
    # Add user message
    st.session_state["cooking_chat"].append({
        "role": "user",
        "content": prompt
    })
    
    # Get agent response
    agent = st.session_state.get("cooking_agent")
    servings = st.session_state.get("cooking_servings", 2)
    
    if agent:
        try:
            response = agent.chat(prompt, servings=servings)
        except Exception as e:
            response = (
                f"I encountered an error: {str(e)}\n\n"
                "Please try:\n"
                "- Rephrasing your question\n"
                "- Asking about a specific recipe name\n"
                "- Checking if your API key is set correctly"
            )
    else:
        response = "Cooking agent is not available. Please check your setup."
    
    # Add assistant response
    st.session_state["cooking_chat"].append({
        "role": "assistant",
        "content": response
    })


def main() -> None:
    st.title("🍳 Cooking Assistant")
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
        
        # Quick action buttons - NOW WITH PROPER PROCESSING
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
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state["cooking_chat"] = []
            st.rerun()
    
    # Display chat history
    history = st.session_state["cooking_chat"]
    
    if not history:
        st.info("👋 Welcome! Ask me anything about cooking, recipes, or ingredients.")
        
        st.markdown("### Try asking:")
        st.markdown("- *How do I make Grilled Chicken Bowl?*")
        st.markdown("- *Give me a high-protein recipe with salmon*")
        st.markdown("- *What are the ingredients and amounts for Greek Yogurt Parfait?*")
        st.markdown("- *Show me vegetarian recipes*")
    
    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask for a recipe, cooking instructions, or ingredient amounts..."):
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process and get response
        with st.chat_message("assistant"):
            with st.spinner("🔍 Searching recipes and preparing your answer..."):
                agent = st.session_state.get("cooking_agent")
                servings = st.session_state["cooking_servings"]
                
                if agent:
                    try:
                        response = agent.chat(prompt, servings=servings)
                        st.markdown(response)
                    except Exception as e:
                        error_msg = (
                            f"I encountered an error: {str(e)}\n\n"
                            "Please try:\n"
                            "- Rephrasing your question\n"
                            "- Asking about a specific recipe name\n"
                            "- Checking if your API key is set correctly"
                        )
                        st.error(str(e))
                        st.markdown(error_msg)
                        response = error_msg
                else:
                    response = "Cooking agent is not available. Please restart the app."
                    st.error(response)
        
        # Save to history
        st.session_state["cooking_chat"].append({"role": "user", "content": prompt})
        st.session_state["cooking_chat"].append({"role": "assistant", "content": response})
        st.rerun()


if __name__ == "__main__":
    main()