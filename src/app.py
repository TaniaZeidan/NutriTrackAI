"""Streamlit entry point for NutriTrackAI."""
from __future__ import annotations

import streamlit as st

from core.embeddings import build_index
from core.rag import search_recipes
from tools.meal_planner import generate_plan
from core.schemas import MacroTargets


# Page configuration
st.set_page_config(
    page_title="NutriTrackAI",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for the entire app
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Main app styling */
    .stApp {
        background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%);
    }
    
    /* ========== SIDEBAR STYLING ========== */
    [data-testid="stSidebar"] {
        background: #FFFFFF !important;
        border-right: 1px solid #E2E8F0;
        box-shadow: 4px 0 20px rgba(0, 0, 0, 0.03);
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0 !important;
    }
    
    /* Sidebar text colors */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {
        color: #334155 !important;
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {
        color: #0F172A !important;
    }
    
    /* Sidebar navigation - page links */
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] {
        padding: 1rem 0;
    }
    
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
        color: #475569 !important;
        padding: 0.75rem 1rem !important;
        margin: 0.25rem 0.75rem !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        display: block !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
        background: #F0FDF4 !important;
        color: #166534 !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-selected="true"] {
        background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3) !important;
    }
    
    /* Sidebar buttons */
    [data-testid="stSidebar"] .stButton button {
        background: #F8FAFC !important;
        color: #475569 !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px;
        padding: 0.6rem 1rem;
        font-weight: 500;
        transition: all 0.2s ease;
        width: 100%;
    }
    
    [data-testid="stSidebar"] .stButton button:hover {
        background: #F0FDF4 !important;
        border-color: #22C55E !important;
        color: #166534 !important;
    }
    
    /* Sidebar divider */
    [data-testid="stSidebar"] hr {
        border: none;
        height: 1px;
        background: #E2E8F0;
        margin: 1rem 1rem;
    }
    
    /* Sidebar inputs */
    [data-testid="stSidebar"] .stTextInput input,
    [data-testid="stSidebar"] .stNumberInput input {
        background: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        color: #334155 !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
    }
    
    /* ========== MAIN CONTENT STYLING ========== */
    
    /* Headers */
    h1 {
        font-family: 'Inter', sans-serif !important;
        color: #0F172A !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }
    
    h2, h3 {
        font-family: 'Inter', sans-serif !important;
        color: #1E293B !important;
        font-weight: 600 !important;
    }
    
    /* Body text */
    p, span, label, .stMarkdown {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Main content buttons */
    .stButton > button {
        background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%);
        color: white !important;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(34, 197, 94, 0.25);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(34, 197, 94, 0.35);
    }
    
    /* Primary button variant */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #F97316 0%, #EA580C 100%);
        box-shadow: 0 4px 12px rgba(249, 115, 22, 0.25);
    }
    
    /* Form inputs */
    .stTextInput input, .stNumberInput input {
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        padding: 0.75rem 1rem !important;
        font-family: 'Inter', sans-serif !important;
        background: white !important;
        transition: all 0.2s ease;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #22C55E !important;
        box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.15) !important;
    }
    
    /* Select boxes */
    [data-testid="stSelectbox"] > div > div {
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        background: white !important;
    }
    
    /* Metrics */
    [data-testid="stMetric"] {
        background: white;
        padding: 1.25rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        border: 1px solid #E2E8F0;
    }
    
    [data-testid="stMetric"] label {
        color: #64748B !important;
        font-weight: 500 !important;
    }
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #0F172A !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 10px !important;
        border: none !important;
    }
    
    /* Success messages */
    [data-testid="stAlert"] {
        background: #F0FDF4 !important;
        border: 1px solid #BBF7D0 !important;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: white !important;
        border-radius: 10px !important;
        border: 1px solid #E2E8F0 !important;
        font-weight: 600 !important;
        color: #1E293B !important;
    }
    
    /* Dividers */
    hr {
        border: none;
        height: 1px;
        background: #E2E8F0;
        margin: 1.5rem 0;
    }
    
    /* Chat messages */
    [data-testid="stChatMessage"] {
        background: white !important;
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
        padding: 1rem !important;
        margin: 0.5rem 0 !important;
    }
    
    /* Chat input */
    [data-testid="stChatInput"] textarea {
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        background: white !important;
    }
    
    /* Dataframes */
    .stDataFrame {
        border-radius: 10px !important;
        overflow: hidden;
        border: 1px solid #E2E8F0;
    }
    
    /* Download button */
    .stDownloadButton button {
        background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: #F8FAFC;
        padding: 0.5rem;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: #22C55E !important;
        color: white !important;
    }
    
    /* Form styling */
    [data-testid="stForm"] {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: #F1F5F9;
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #CBD5E1;
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #94A3B8;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar content
with st.sidebar:
    # Clean logo header
    st.markdown("""
    <div style="padding: 1.5rem 1rem 1rem 1rem; text-align: center; border-bottom: 1px solid #E2E8F0; margin-bottom: 1rem;">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 56px; height: 56px; background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%); border-radius: 14px; margin-bottom: 0.75rem; box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);">
            <span style="font-size: 1.75rem;">🥗</span>
        </div>
        <h2 style="font-size: 1.4rem; margin: 0; font-weight: 700; color: #0F172A;">NutriTrack<span style="color: #22C55E;">AI</span></h2>
        <p style="font-size: 0.8rem; margin: 0.25rem 0 0 0; color: #64748B;">Smart Nutrition Tracking</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tools section
    st.markdown("""
    <div style="padding: 0 0.5rem;">
        <p style="font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px; color: #94A3B8; margin: 1rem 0 0.5rem 0.5rem; font-weight: 600;">Tools</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔄 Rebuild Index", use_container_width=True, help="Rebuild the recipe search index"):
        with st.spinner("Rebuilding..."):
        build_index(force=True)
            st.success("✅ Done!")
    
    # Info card at bottom
    st.markdown("""
    <div style="position: fixed; bottom: 1rem; left: 1rem; right: 1rem; max-width: 230px;">
        <div style="background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%); padding: 1rem; border-radius: 12px; border: 1px solid #BBF7D0;">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                <span style="font-size: 1rem;">💡</span>
                <span style="font-size: 0.8rem; font-weight: 600; color: #166534;">Quick Tip</span>
            </div>
            <p style="font-size: 0.75rem; color: #15803D; margin: 0; line-height: 1.4;">
                Select a page above to start tracking your nutrition journey!
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Ensure index exists on start
build_index()

if "weekly_plan" not in st.session_state:
    st.session_state["weekly_plan"] = generate_plan(
        MacroTargets(calories=2000, protein=130, carbs=220, fat=60), days=1
    )

# Main content - Welcome page
st.markdown("""
<div style="text-align: center; padding: 3rem 0 2rem 0;">
    <div style="display: inline-flex; align-items: center; justify-content: center; width: 80px; height: 80px; background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%); border-radius: 20px; margin-bottom: 1.5rem; box-shadow: 0 8px 24px rgba(34, 197, 94, 0.25);">
        <span style="font-size: 2.5rem;">🥗</span>
    </div>
    <h1 style="font-size: 2.75rem; margin-bottom: 0.75rem; color: #0F172A;">Welcome to NutriTrack<span style="color: #22C55E;">AI</span></h1>
    <p style="font-size: 1.15rem; color: #64748B; max-width: 550px; margin: 0 auto; line-height: 1.6;">
        Your intelligent companion for tracking nutrition, planning meals, and achieving your health goals.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Feature cards
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="background: white; padding: 2rem; border-radius: 16px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #E2E8F0; height: 220px;">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 56px; height: 56px; background: #FEF3C7; border-radius: 14px; margin-bottom: 1rem;">
            <span style="font-size: 1.5rem;">📊</span>
        </div>
        <h3 style="color: #0F172A; margin-bottom: 0.5rem; font-size: 1.1rem;">Track Macros</h3>
        <p style="color: #64748B; font-size: 0.9rem; line-height: 1.5;">Log meals and automatically calculate your daily calories and macros.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="background: white; padding: 2rem; border-radius: 16px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #E2E8F0; height: 220px;">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 56px; height: 56px; background: #DBEAFE; border-radius: 14px; margin-bottom: 1rem;">
            <span style="font-size: 1.5rem;">🎯</span>
        </div>
        <h3 style="color: #0F172A; margin-bottom: 0.5rem; font-size: 1.1rem;">Personalized Plans</h3>
        <p style="color: #64748B; font-size: 0.9rem; line-height: 1.5;">Get AI meal plans tailored to your body metrics and goals.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="background: white; padding: 2rem; border-radius: 16px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #E2E8F0; height: 220px;">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 56px; height: 56px; background: #F0FDF4; border-radius: 14px; margin-bottom: 1rem;">
            <span style="font-size: 1.5rem;">👨‍🍳</span>
        </div>
        <h3 style="color: #0F172A; margin-bottom: 0.5rem; font-size: 1.1rem;">Smart Recipes</h3>
        <p style="color: #64748B; font-size: 0.9rem; line-height: 1.5;">Chat with AI to discover healthy recipes with nutrition info.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# CTA section
st.markdown("""
<div style="background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%); padding: 2.5rem; border-radius: 20px; text-align: center; box-shadow: 0 8px 24px rgba(34, 197, 94, 0.2);">
    <h2 style="color: white !important; margin-bottom: 0.75rem; font-size: 1.5rem;">🚀 Ready to Start?</h2>
    <p style="color: rgba(255,255,255,0.9); max-width: 450px; margin: 0 auto; font-size: 1rem;">
        Select a page from the sidebar to begin tracking your nutrition!
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Tips row
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div style="background: white; padding: 1.25rem; border-radius: 12px; border: 1px solid #E2E8F0; display: flex; align-items: flex-start; gap: 1rem;">
        <div style="min-width: 40px; height: 40px; background: #FEF3C7; border-radius: 10px; display: flex; align-items: center; justify-content: center;">
            <span style="font-size: 1.1rem;">💡</span>
        </div>
        <div>
            <h4 style="color: #0F172A; margin: 0 0 0.25rem 0; font-size: 0.95rem;">Pro Tip</h4>
            <p style="color: #64748B; font-size: 0.85rem; margin: 0; line-height: 1.4;">Log meals daily to see accurate progress trends!</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="background: white; padding: 1.25rem; border-radius: 12px; border: 1px solid #E2E8F0; display: flex; align-items: flex-start; gap: 1rem;">
        <div style="min-width: 40px; height: 40px; background: #DBEAFE; border-radius: 10px; display: flex; align-items: center; justify-content: center;">
            <span style="font-size: 1.1rem;">🔑</span>
        </div>
        <div>
            <h4 style="color: #0F172A; margin: 0 0 0.25rem 0; font-size: 0.95rem;">API Key</h4>
            <p style="color: #64748B; font-size: 0.85rem; margin: 0; line-height: 1.4;">Add your Google API key to .env for AI features.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
