import streamlit as st
import pandas as pd
from datetime import date
from typing import Tuple, List

def render_date_filter(
    df: pd.DataFrame,
    date_col: str = "today",
    key: str = "date_filter",
    min_limit: date = None
) -> Tuple[date, date]:
    """Standardized sidebar date range selector."""
    if df.empty or date_col not in df.columns:
        today = date.today()
        return today, today

    min_val = min_limit or df[date_col].min()
    max_val = df[date_col].max()

    date_range = st.sidebar.date_input(
        "Select Date Range:",
        value=(min_val, max_val),
        min_value=min_val,
        max_value=max_val,
        key=key
    )

    if len(date_range) == 2:
        return date_range[0], date_range[1]
    return min_val, max_val

def render_multiselect_filter(
    df: pd.DataFrame,
    col: str,
    label: str,
    default_selected: List = None,
    key: str = None
) -> List:
    """Standardized sidebar multiselect with all options by default."""
    if df.empty or col not in df.columns:
        return []
    options = sorted(df[col].dropna().unique())
    default = default_selected if default_selected is not None else options
    return st.sidebar.multiselect(
        label,
        options=options,
        default=default,
        key=key or f"{col}_filter"
    )
