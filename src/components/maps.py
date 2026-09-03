import pydeck as pdk
import numpy as np
import pandas as pd
import streamlit as st
from typing import Optional

def render_site_map(
    coords_df: pd.DataFrame,
    lat_col: str = "lat",
    lon_col: str = "lon",
    label_col: str = "landing_site",
    radius_col: str = "count",
    dot_color: str = "[200, 30, 0, 160]",
    label_color: list = [1, 1, 1],
    default_zoom: int = 7
):
    """Render a standard PyDeck scatter + text label map."""
    clean_coords = coords_df.dropna(subset=[lat_col, lon_col])
    if clean_coords.empty:
        st.info("No geographic coordinates available to display map.")
        return

    layers = [
        pdk.Layer(
            "ScatterplotLayer",
            clean_coords,
            get_position=f"[{lon_col}, {lat_col}]",
            get_radius=radius_col,
            get_color=dot_color,
            pickable=True,
        ),
        pdk.Layer(
            "TextLayer",
            clean_coords,
            get_position=f"[{lon_col}, {lat_col}]",
            get_text=label_col,
            get_size=12,
            get_color=label_color,
            get_alignment_baseline="'bottom'",
        )
    ]

    mean_lat = float(np.mean(clean_coords[lat_col]))
    mean_lon = float(np.mean(clean_coords[lon_col]))

    st.pydeck_chart(
        pdk.Deck(
            map_style="light",
            layers=layers,
            initial_view_state=pdk.ViewState(
                latitude=mean_lat,
                longitude=mean_lon,
                zoom=default_zoom,
                pitch=0,
            ),
        )
    )
