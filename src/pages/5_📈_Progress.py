"""Progress Dashboard with enhanced visualizations."""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from core.db import Database


def main() -> None:
    # Page header
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="margin-bottom: 0.5rem;">📈 Progress Dashboard</h1>
        <p style="color: #52796F; font-size: 1.1rem;">Track your nutrition journey and see how you're doing over time.</p>
    </div>
    """, unsafe_allow_html=True)
    
    db = Database()
    today = date.today()
    
    # Get weekly summary
    summary = db.weekly_summary(today)
    
    if not summary or all(v == 0 for v in summary.values()):
        st.markdown("""
        <div style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); padding: 3rem; border-radius: 20px; text-align: center;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">📊</div>
            <h3 style="color: #92400E; margin-bottom: 1rem;">No Data Yet</h3>
            <p style="color: #A16207; max-width: 400px; margin: 0 auto;">
                Start logging your meals on the Daily Log page to see your progress and trends here!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🔢 Go to Daily Log", use_container_width=True):
            st.switch_page("pages/1_🔢_Daily_Log.py")
        return
    
    # Date range info
    start_date = today - timedelta(days=6)
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #2D6A4F 0%, #40916C 100%); padding: 1.5rem 2rem; border-radius: 16px; color: white; margin-bottom: 2rem;">
        <h3 style="color: white !important; margin: 0 0 0.5rem 0;">📅 Weekly Overview</h3>
        <p style="opacity: 0.9; margin: 0;">{start_date.strftime("%B %d")} - {today.strftime("%B %d, %Y")}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Summary cards
    col1, col2, col3, col4 = st.columns(4)
    
    avg_calories = summary.get("calories", 0) / 7
    avg_protein = summary.get("protein_g", 0) / 7
    avg_carbs = summary.get("carb_g", 0) / 7
    avg_fat = summary.get("fat_g", 0) / 7
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); padding: 1.5rem; border-radius: 14px; text-align: center;">
            <p style="color: #92400E; font-size: 0.85rem; margin: 0;">🔥 Total Calories</p>
            <h2 style="color: #78350F; margin: 0.5rem 0 0.25rem 0; font-size: 1.8rem;">{summary.get('calories', 0):,.0f}</h2>
            <p style="color: #A16207; font-size: 0.8rem; margin: 0;">~{avg_calories:,.0f}/day avg</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%); padding: 1.5rem; border-radius: 14px; text-align: center;">
            <p style="color: #1E40AF; font-size: 0.85rem; margin: 0;">💪 Total Protein</p>
            <h2 style="color: #1E3A8A; margin: 0.5rem 0 0.25rem 0; font-size: 1.8rem;">{summary.get('protein_g', 0):,.0f}g</h2>
            <p style="color: #3B82F6; font-size: 0.8rem; margin: 0;">~{avg_protein:,.0f}g/day avg</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%); padding: 1.5rem; border-radius: 14px; text-align: center;">
            <p style="color: #065F46; font-size: 0.85rem; margin: 0;">🍞 Total Carbs</p>
            <h2 style="color: #064E3B; margin: 0.5rem 0 0.25rem 0; font-size: 1.8rem;">{summary.get('carb_g', 0):,.0f}g</h2>
            <p style="color: #10B981; font-size: 0.8rem; margin: 0;">~{avg_carbs:,.0f}g/day avg</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #FCE7F3 0%, #FBCFE8 100%); padding: 1.5rem; border-radius: 14px; text-align: center;">
            <p style="color: #9D174D; font-size: 0.85rem; margin: 0;">🥑 Total Fat</p>
            <h2 style="color: #831843; margin: 0.5rem 0 0.25rem 0; font-size: 1.8rem;">{summary.get('fat_g', 0):,.0f}g</h2>
            <p style="color: #EC4899; font-size: 0.8rem; margin: 0;">~{avg_fat:,.0f}g/day avg</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts
    st.markdown("""
    <div style="background: white; padding: 1.5rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); margin-bottom: 1.5rem;">
        <h4 style="color: #2D6A4F; margin-bottom: 1rem;">📊 Weekly Macro Distribution</h4>
    </div>
    """, unsafe_allow_html=True)
    
    # Create a nice bar chart
    chart_data = pd.DataFrame({
        "Macro": ["Calories (÷10)", "Protein (g)", "Carbs (g)", "Fat (g)"],
        "Value": [
            summary.get("calories", 0) / 10,  # Scale down for visualization
            summary.get("protein_g", 0),
            summary.get("carb_g", 0),
            summary.get("fat_g", 0)
        ]
    })
    
    st.bar_chart(chart_data.set_index("Macro"), use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Daily breakdown section
    st.markdown("""
    <div style="background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%); padding: 1.5rem; border-radius: 16px; margin-bottom: 1rem;">
        <h4 style="color: #065F46; margin-bottom: 0.5rem;">📅 Daily Breakdown (Last 7 Days)</h4>
        <p style="color: #047857; margin: 0; font-size: 0.9rem;">See how your nutrition varied each day</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get daily data
    daily_data = []
    for i in range(7):
        day = today - timedelta(days=6-i)
        day_totals = db.daily_totals(day)
        daily_data.append({
            "Date": day.strftime("%a %m/%d"),
            "Calories": day_totals.get("calories", 0),
            "Protein (g)": day_totals.get("protein_g", 0),
            "Carbs (g)": day_totals.get("carb_g", 0),
            "Fat (g)": day_totals.get("fat_g", 0)
        })
    
    daily_df = pd.DataFrame(daily_data)
    
    # Display as a styled table
    if daily_df["Calories"].sum() > 0:
        st.dataframe(
            daily_df.set_index("Date"),
            use_container_width=True,
            height=300
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Calorie trend chart
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.03);">
            <h4 style="color: #2D6A4F; margin-bottom: 1rem;">📈 Calorie Trend</h4>
        </div>
        """, unsafe_allow_html=True)
        
        calorie_trend = daily_df[["Date", "Calories"]].set_index("Date")
        st.line_chart(calorie_trend, use_container_width=True)
    else:
        st.info("📝 Log more meals to see your daily breakdown!")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tips section
    st.markdown("""
    <div style="background: linear-gradient(135deg, #2D6A4F 0%, #40916C 100%); padding: 2rem; border-radius: 16px; color: white;">
        <h4 style="color: white !important; margin-bottom: 1rem;">💡 Tips for Success</h4>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px;">
                <p style="margin: 0; font-size: 0.9rem;">🎯 <strong>Stay Consistent</strong><br>Log meals daily for accurate tracking</p>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px;">
                <p style="margin: 0; font-size: 0.9rem;">💪 <strong>Hit Protein Goals</strong><br>Aim for 1.6-2.2g per kg bodyweight</p>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px;">
                <p style="margin: 0; font-size: 0.9rem;">⚖️ <strong>Balance Macros</strong><br>Don't neglect any macronutrient</p>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px;">
                <p style="margin: 0; font-size: 0.9rem;">📊 <strong>Track Trends</strong><br>Weekly averages matter more than daily</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
