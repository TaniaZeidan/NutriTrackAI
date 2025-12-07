"""Enhanced Cooking Assistant page with beautiful chat UI."""
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
    # Page header
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="margin-bottom: 0.5rem;">👩‍🍳 Cooking Assistant</h1>
        <p style="color: #52796F; font-size: 1.1rem;">Your AI-powered cooking companion for recipes, instructions, and nutrition info.</p>
    </div>
    """, unsafe_allow_html=True)
    
    _ensure_session()
    
    # Sidebar controls
    with st.sidebar:
        st.markdown("""
        <div style="padding: 0.5rem 0.5rem 0.5rem 0.5rem;">
            <p style="font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px; color: #94A3B8; margin: 0 0 0.5rem 0; font-weight: 600;">⚙️ Settings</p>
        </div>
        """, unsafe_allow_html=True)
        
        servings = st.number_input(
            "🍽️ Target Servings",
            min_value=1,
            max_value=8,
            value=st.session_state["cooking_servings"],
            step=1,
            help="All recipes and macros will be scaled to this number of servings.",
        )
        st.session_state["cooking_servings"] = int(servings)
        
        st.caption("📊 Macros calculated per serving")
        
        st.markdown("---")
        
        st.markdown("""
        <p style="font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px; color: #94A3B8; margin: 0 0 0.75rem 0; font-weight: 600;">⚡ Quick Actions</p>
        """, unsafe_allow_html=True)
        
        # Quick action buttons
        if st.button("🔍 Search Healthy Recipes", use_container_width=True):
            _process_message("Show me some healthy high-protein recipes")
            st.rerun()
        
        if st.button("🥗 Low Calorie Meals", use_container_width=True):
            _process_message("Give me healthy meal ideas under 500 calories")
            st.rerun()
        
        if st.button("💪 High Protein Options", use_container_width=True):
            _process_message("Show me high protein recipes with at least 30g protein per serving")
            st.rerun()
        
        if st.button("🥬 Vegetarian Ideas", use_container_width=True):
            _process_message("Show me vegetarian recipes")
            st.rerun()
        
        st.markdown("---")
        
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state["cooking_chat"] = []
            st.rerun()
    
    # Main chat area
    history = st.session_state["cooking_chat"]
    
    if not history:
        # Welcome state
        st.markdown("""
        <div style="background: linear-gradient(135deg, #2D6A4F 0%, #40916C 100%); padding: 2rem; border-radius: 20px; color: white; text-align: center; margin-bottom: 2rem;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">👨‍🍳</div>
            <h2 style="color: white !important; margin-bottom: 0.5rem;">Welcome to Your AI Chef!</h2>
            <p style="opacity: 0.9; max-width: 500px; margin: 0 auto;">
                Ask me anything about cooking, recipes, or ingredients. I'll help you with detailed instructions and nutrition information!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Suggestion cards
        st.markdown("""
        <h4 style="color: #2D6A4F; margin-bottom: 1rem;">💬 Try asking me...</h4>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="background: white; padding: 1.5rem; border-radius: 14px; margin-bottom: 1rem; box-shadow: 0 2px 10px rgba(0,0,0,0.03); border: 1px solid #E8F5E9;">
                <p style="color: #2D6A4F; font-weight: 600; margin-bottom: 0.5rem;">🍗 Recipe Instructions</p>
                <p style="color: #6B7280; font-size: 0.9rem; margin: 0;">"How do I make Grilled Chicken Bowl?"</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style="background: white; padding: 1.5rem; border-radius: 14px; margin-bottom: 1rem; box-shadow: 0 2px 10px rgba(0,0,0,0.03); border: 1px solid #E8F5E9;">
                <p style="color: #2D6A4F; font-weight: 600; margin-bottom: 0.5rem;">🥗 Diet-Specific</p>
                <p style="color: #6B7280; font-size: 0.9rem; margin: 0;">"Show me vegetarian high-protein recipes"</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: white; padding: 1.5rem; border-radius: 14px; margin-bottom: 1rem; box-shadow: 0 2px 10px rgba(0,0,0,0.03); border: 1px solid #E8F5E9;">
                <p style="color: #2D6A4F; font-weight: 600; margin-bottom: 0.5rem;">🐟 Ingredient-Based</p>
                <p style="color: #6B7280; font-size: 0.9rem; margin: 0;">"Give me a recipe with salmon"</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style="background: white; padding: 1.5rem; border-radius: 14px; margin-bottom: 1rem; box-shadow: 0 2px 10px rgba(0,0,0,0.03); border: 1px solid #E8F5E9;">
                <p style="color: #2D6A4F; font-weight: 600; margin-bottom: 0.5rem;">📊 Nutrition Info</p>
                <p style="color: #6B7280; font-size: 0.9rem; margin: 0;">"What are the macros for Greek Yogurt Parfait?"</p>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        # Display chat history with enhanced styling
        for message in history:
            if message["role"] == "user":
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-end; margin-bottom: 1rem;">
                    <div style="background: linear-gradient(135deg, #2D6A4F 0%, #40916C 100%); color: white; padding: 1rem 1.25rem; border-radius: 18px 18px 4px 18px; max-width: 80%; box-shadow: 0 2px 10px rgba(45,106,79,0.2);">
                        <p style="margin: 0;">{message["content"]}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-start; margin-bottom: 1rem;">
                    <div style="background: white; padding: 1rem 1.25rem; border-radius: 18px 18px 18px 4px; max-width: 85%; box-shadow: 0 2px 10px rgba(0,0,0,0.05); border: 1px solid #E8F5E9;">
                        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                            <span style="font-size: 1.25rem; margin-right: 0.5rem;">👩‍🍳</span>
                            <span style="color: #2D6A4F; font-weight: 600; font-size: 0.9rem;">NutriTrack Chef</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(message["content"])
                st.markdown("<br>", unsafe_allow_html=True)
    
    # Chat input
    st.markdown("<br>", unsafe_allow_html=True)
    
    if prompt := st.chat_input("Ask for a recipe, cooking instructions, or nutrition info..."):
        # Display user message immediately
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; margin-bottom: 1rem;">
            <div style="background: linear-gradient(135deg, #2D6A4F 0%, #40916C 100%); color: white; padding: 1rem 1.25rem; border-radius: 18px 18px 4px 18px; max-width: 80%;">
                <p style="margin: 0;">{prompt}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Process and get response
        with st.spinner("🔍 Searching recipes and preparing your answer..."):
            agent = st.session_state.get("cooking_agent")
            servings = st.session_state["cooking_servings"]
            
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
                response = "Cooking agent is not available. Please restart the app."
        
        # Display response
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-start; margin-bottom: 1rem;">
            <div style="background: white; padding: 1rem 1.25rem; border-radius: 18px 18px 18px 4px; max-width: 85%; box-shadow: 0 2px 10px rgba(0,0,0,0.05); border: 1px solid #E8F5E9;">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 1.25rem; margin-right: 0.5rem;">👩‍🍳</span>
                    <span style="color: #2D6A4F; font-weight: 600; font-size: 0.9rem;">NutriTrack Chef</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(response)
        
        # Save to history
        st.session_state["cooking_chat"].append({"role": "user", "content": prompt})
        st.session_state["cooking_chat"].append({"role": "assistant", "content": response})
        st.rerun()


if __name__ == "__main__":
    main()
