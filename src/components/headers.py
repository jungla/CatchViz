import streamlit as st
from datetime import date
from typing import Sequence, Optional
from src.components.styles import load_css

def render_page_header(
    subtitle: str,
    title: str = "Data Visualization Platform",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    selected_items: Optional[Sequence[str]] = None,
    item_label: str = "sites"
):
    """Render standardized WCS page header with subtitle and filter status."""
    load_css("global.css")

    col1, mid, col2 = st.columns([20, 1, 5])
    with col1:
        st.markdown(
            f"""
            <h1 class="h1-custom">{title}</h1>
            <h2 class="h2-custom">{subtitle}</h2>
            """,
            unsafe_allow_html=True
        )

    if start_date and end_date:
        items_str = ", ".join(selected_items) if selected_items else "None"
        st.markdown(
            f"Visualizing data from **{start_date.strftime('%Y-%m-%d')}** to **{end_date.strftime('%Y-%m-%d')}** "
            f"for {item_label}: **{items_str}**."
        )
        st.markdown("---")
