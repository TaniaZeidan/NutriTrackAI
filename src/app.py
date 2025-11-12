"""Streamlit entry point for NutriTrackAI."""
from __future__ import annotations

import streamlit as st

from .core.rag import build_index
from .tools.meal_planner import generate_plan
from .core.schemas import MacroTargets


st.set_page_config(page_title="NutriTrackAI", page_icon="🥗", layout="wide")

st.sidebar.image("https://raw.githubusercontent.com/streamlit/brand/main/logomark/streamlit-mark-color.png", width=80)
st.sidebar.title("NutriTrackAI")

if st.sidebar.button("Rebuild Recipe Index"):
    with st.spinner("Building FAISS index..."):
        build_index(force=True)
        st.success("Index rebuilt.")

# ensure index exists on start
build_index()

if "weekly_plan" not in st.session_state:
    st.session_state["weekly_plan"] = generate_plan(
        MacroTargets(calories=2000, protein=130, carbs=220, fat=60), days=1
    )

st.sidebar.info("Use the pages menu to explore logging, planning, groceries, cooking, and progress.")

st.write("Select a page from the sidebar to get started.")
