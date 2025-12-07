"""Grocery List page with enhanced UI."""
from __future__ import annotations

import streamlit as st

from tools.grocery_list import build_list_from_plan, export_csv
from ui.components import plan_table

# Category icons and colors
CATEGORY_STYLES = {
    "Produce": {"icon": "🥬", "color": "#22C55E", "bg": "#DCFCE7"},
    "Protein": {"icon": "🥩", "color": "#EF4444", "bg": "#FEE2E2"},
    "Dairy": {"icon": "🥛", "color": "#3B82F6", "bg": "#DBEAFE"},
    "Pantry": {"icon": "🥫", "color": "#F59E0B", "bg": "#FEF3C7"},
    "Other": {"icon": "📦", "color": "#8B5CF6", "bg": "#EDE9FE"},
}


def main() -> None:
    # Page header
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="margin-bottom: 0.5rem;">🛒 Grocery List</h1>
        <p style="color: #52796F; font-size: 1.1rem;">Your shopping list generated from your meal plan, organized by category.</p>
    </div>
    """, unsafe_allow_html=True)
    
    plan = st.session_state.get("weekly_plan")
    
    if not plan:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); padding: 3rem; border-radius: 20px; text-align: center;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">📋</div>
            <h3 style="color: #92400E; margin-bottom: 1rem;">No Meal Plan Yet</h3>
            <p style="color: #A16207; max-width: 400px; margin: 0 auto;">
                Create a meal plan first on the "Plan My Week" page, then come back here to generate your grocery list!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("📅 Go to Plan My Week", use_container_width=True):
            st.switch_page("pages/2_📅_Plan_My_Week.py")
        return
    
    # Build the grocery list
    groceries = build_list_from_plan(plan)
    
    if not groceries:
        st.info("No groceries to display. Your meal plan may be empty.")
        return
    
    # Summary stats
    total_items = len(groceries)
    categories = set(item.category for item in groceries)
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #2D6A4F 0%, #40916C 100%); padding: 1.5rem 2rem; border-radius: 16px; color: white; margin-bottom: 2rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h3 style="color: white !important; margin: 0 0 0.5rem 0;">📊 Shopping Summary</h3>
                <p style="opacity: 0.9; margin: 0;">Ready to shop for your meal plan</p>
            </div>
            <div style="display: flex; gap: 2rem;">
                <div style="text-align: center;">
                    <h2 style="color: #95D5B2 !important; margin: 0;">{total_items}</h2>
                    <span style="opacity: 0.8; font-size: 0.85rem;">Items</span>
                </div>
                <div style="text-align: center;">
                    <h2 style="color: #95D5B2 !important; margin: 0;">{len(categories)}</h2>
                    <span style="opacity: 0.8; font-size: 0.85rem;">Categories</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Group items by category
    by_category = {}
    for item in groceries:
        if item.category not in by_category:
            by_category[item.category] = []
        by_category[item.category].append(item)
    
    # Display by category
    for category in sorted(by_category.keys()):
        items = by_category[category]
        style = CATEGORY_STYLES.get(category, CATEGORY_STYLES["Other"])
        
        st.markdown(f"""
        <div style="background: {style['bg']}; padding: 1.25rem; border-radius: 14px; margin-bottom: 1rem; border-left: 4px solid {style['color']};">
            <h4 style="color: {style['color']}; margin: 0 0 0.75rem 0;">{style['icon']} {category}</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Create columns for items
        cols = st.columns(3)
        for idx, item in enumerate(items):
            with cols[idx % 3]:
                st.markdown(f"""
                <div style="background: white; padding: 1rem; border-radius: 10px; margin-bottom: 0.5rem; box-shadow: 0 2px 5px rgba(0,0,0,0.03);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #374151; font-weight: 500;">{item.name}</span>
                        <span style="color: {style['color']}; font-weight: 600; font-size: 0.9rem;">{item.quantity:.1f} {item.unit}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Export section
    st.markdown("""
    <div style="background: white; padding: 2rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.05);">
        <h3 style="color: #2D6A4F; margin-bottom: 1rem;">📥 Export Your List</h3>
        <p style="color: #52796F; margin-bottom: 1rem;">Download your grocery list as a CSV file to take to the store or share with family.</p>
    </div>
    """, unsafe_allow_html=True)
    
    csv_data = export_csv(groceries)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.download_button(
            "📄 Download as CSV",
            data=csv_data,
            file_name="grocery_list.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Copy-friendly text version
        text_list = "\n".join([
            f"□ {item.name}: {item.quantity:.1f} {item.unit}"
            for item in groceries
        ])
        st.download_button(
            "📝 Download as Checklist",
            data=text_list,
            file_name="grocery_checklist.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tips section
    st.markdown("""
    <div style="background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%); padding: 1.5rem; border-radius: 14px;">
        <h4 style="color: #065F46; margin-bottom: 0.75rem;">💡 Shopping Tips</h4>
        <ul style="color: #047857; margin: 0; padding-left: 1.25rem;">
            <li>Check your pantry before shopping to avoid duplicates</li>
            <li>Buy fresh produce for the first few days of your plan</li>
            <li>Consider frozen options for longer-lasting ingredients</li>
            <li>Shop the perimeter of the store for healthier options</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
