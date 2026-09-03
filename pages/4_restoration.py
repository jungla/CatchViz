import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from src.data_loader import load_restoration_data, load_restoration_sites_reference
from src.components.headers import render_page_header

# --- Data Loading ---
df = load_restoration_data()
ref_coords = load_restoration_sites_reference()

# --- Sidebar Filters ---
st.sidebar.header("Filters ⚙️")

if df.empty:
    st.warning("No data loaded. Please check your data files.")
    st.header("Filtered Data Records")
    st.dataframe(pd.DataFrame(), width="stretch")
    st.stop()

min_date = df["date"].min()
max_date = df["date"].max()

date_range = st.sidebar.date_input(
    "Select Date Range:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="date_filter"
)

start_date = min_date
end_date = max_date
if len(date_range) == 2:
    start_date, end_date = date_range

all_sites = sorted(df["site_name"].dropna().unique())
selected_sites = st.sidebar.multiselect(
    "Select Site(s):",
    options=all_sites,
    default=all_sites,
    key="site_filter"
)

# --- Apply Filters ---
filtered_df = df[
    (df["date"] >= start_date) &
    (df["date"] <= end_date) &
    (df["site_name"].isin(selected_sites))
].copy()

# --- Header ---
render_page_header(
    subtitle="Coral Restoration Projects",
    start_date=start_date,
    end_date=end_date,
    selected_items=selected_sites,
    item_label="sites"
)

# --- Metrics / KPIs ---
if not filtered_df.empty:
    total_transplanted = sum(filtered_df.groupby("site_name")["total_fragments_transplanted_to_date"].max())
    total_nursery = sum(filtered_df.groupby("site_name")["total_fragments_in_nursery_to_date"].max())
    total_reefstar_area = sum(filtered_df.groupby("site_name")["total_reef_starts_deployed_to_date"].max()) * 1
    total_fencewire_area = sum(filtered_df.groupby("site_name")["total_fence_wires_deployed_to_date"].max()) * 30
    total_coralclips_area = sum(filtered_df.groupby("site_name")["total_fragments_on_clips_to_date"].max()) * 0.25
    total_area_restored = (total_reefstar_area + total_fencewire_area + total_coralclips_area) / 1e4

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Number of Corals Transplanted to Date", value=f"{int(total_transplanted):,}")
    with col2:
        st.metric(label="Number Corals in Nursery to Date", value=f"{int(total_nursery):,}")
    with col3:
        st.metric(label="Total Area Restored (ha)", value=f"{total_area_restored:,.2f}")
    st.markdown("---")

    # --- Map Visualization ---
    st.header("Coral Restoration Records")

    nursery_counts = filtered_df.groupby("site_name")["total_fragments_in_nursery_to_date"].max().reset_index()
    transplant_counts = filtered_df.groupby("site_name")["total_fragments_transplanted_to_date"].max().reset_index()

    map_df = pd.merge(ref_coords, nursery_counts, on="site_name", how="left")
    map_df = pd.merge(map_df, transplant_counts, on="site_name", how="left")
    site_type_df = filtered_df[["site_name", "site_type"]].drop_duplicates()
    map_df = pd.merge(site_type_df, map_df, on="site_name", how="inner").drop_duplicates()

    dots_nursery = pdk.Layer(
        "ScatterplotLayer",
        data=map_df[map_df["site_type"] == "nursery"].dropna(subset=["latitude", "longitude"]),
        get_position="[longitude, latitude]",
        get_radius="total_fragments_in_nursery_to_date",
        radius_scale=2,
        radius_min_pixels=2,
        radius_max_pixels=60,
        get_fill_color="[200, 30, 100, 160]",
        pickable=True,
    )

    dots_transplanting = pdk.Layer(
        "ScatterplotLayer",
        data=map_df[map_df["site_type"] == "transplanting"].dropna(subset=["latitude", "longitude"]),
        get_position="[longitude, latitude]",
        get_radius="total_fragments_transplanted_to_date",
        radius_scale=2,
        radius_min_pixels=2,
        radius_max_pixels=60,
        get_color="[200, 30, 60, 120]",
        pickable=True,
    )

    labels = pdk.Layer(
        "TextLayer",
        data=map_df.dropna(subset=["latitude", "longitude"]),
        get_position="[longitude, latitude]",
        get_text="site_name",
        get_size=10,
        size_units="'pixels'",
        get_color=[0, 0, 0, 255],
        get_alignment_baseline="'bottom'",
        get_text_anchor="'middle'",
    )

    clean_coords = map_df.dropna(subset=["latitude", "longitude"])
    if not clean_coords.empty:
        st.pydeck_chart(pdk.Deck(
            map_style="light",
            layers=[dots_nursery, dots_transplanting, labels],
            initial_view_state=pdk.ViewState(
                latitude=float(np.mean(clean_coords["latitude"])),
                longitude=float(np.mean(clean_coords["longitude"])),
                zoom=7,
                pitch=0,
            ),
        ))

    # Data summary
    st.subheader("Restoration Monitoring Records")
    st.dataframe(filtered_df, width="stretch")

else:
    st.markdown("---")
    st.warning("No data available for the selected filters.")
    st.header("Original Data Preview (Top 10 rows)")
    st.dataframe(df.head(10), width="stretch")
