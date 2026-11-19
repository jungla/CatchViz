"""
export_poster_page.py
=====================
Dedicated Streamlit page in CatchViz for generating and exporting A0 management
and scientific posters formatted with Typst.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime
from pathlib import Path

from poster_generator import (
    generate_poster,
    check_typst_available,
    clean_label
)

st.set_page_config(
    page_title="Export A0 Poster - CatchViz",
    page_icon="📜",
    layout="wide"
)

# Header
st.markdown("""
<style>
.h1-custom {
    font-family: 'Futura', serif;
    font-size: 32px !important;
    font-weight: bold;
}
.h2-custom {
    font-family: 'Futura', serif;
    font-size: 46px !important;
    color: #0284c7;
    font-weight: bold;
}
</style>
<h1 class="h1-custom">Tools</h1>
<h2 class="h2-custom">Management & Scientific Poster Generator</h2>
""", unsafe_allow_html=True)

st.markdown(
    "Generate presentation-ready, high-resolution **A0 posters (841 x 1189 mm)** from your filtered monitoring data."
)
st.markdown("---")

# Check Typst status
typst_ok, typst_info = check_typst_available()
col_status1, col_status2 = st.columns([3, 1])
with col_status1:
    if not typst_ok:
        st.warning(
            "⚠️ Typst engine not detected on system. You can still generate and download the complete Typst bundle "
            "(.typ markup + high-resolution figures) to compile on your machine (`brew install typst` or `pip install typst`)."
        )

# Choose Dataset
dataset_choice = st.radio(
    "Select Program Activity / Dataset:",
    options=[
        "Bony Fishes Landings (CATCH)",
        "Sharks and Rays Landings (SHARK)",
        "Coral Reef Restoration Projects (RESTORATION)"
    ],
    horizontal=True
)

if "Restoration" in dataset_choice:
    report_type = "restoration"
    csv_filename = "RESTORATION_kobo_data.csv"
elif "Shark" in dataset_choice:
    report_type = "sharks_rays"
    csv_filename = "SHARK_kobo_data.csv"
else:
    report_type = "bony_fishes"
    csv_filename = "CATCH_kobo_data.csv"

is_sharks = (report_type == "sharks_rays")
is_restoration = (report_type == "restoration")


@st.cache_data
def load_data(filename: str) -> pd.DataFrame:
    for candidate in [Path("kobo_data") / filename, Path(filename)]:
        if candidate.exists():
            return pd.read_csv(candidate, low_memory=False)
    return pd.DataFrame()


df_raw = load_data(csv_filename)

if df_raw.empty:
    st.error(f"Could not load data file `{csv_filename}` (checked `kobo_data/` and workspace root).")
    st.stop()

# Restoration-specific preprocessing (matching restoration.py)
if is_restoration:
    if 'Date' in df_raw.columns:
        df_raw['date'] = pd.to_datetime(df_raw['Date'], format='mixed', errors='coerce').dt.date
        df_raw['datetime'] = pd.to_datetime(df_raw['Date'], format='mixed', errors='coerce')
    if 'test' in df_raw.columns:
        df_raw = df_raw[df_raw['test'] != 'yes']

    coords_sites = pd.DataFrame(
        [
            ['moa', -4.77763, 39.19956],
            ['kigombe', -5.26431, 39.07310],
            ['msuka', -4.90274, 39.72391],
        ],
        columns=['project_site', 'latitude', 'longitude'],
    )
    if 'project_site' in df_raw.columns:
        df_raw = df_raw.drop(columns=[c for c in ['latitude', 'longitude'] if c in df_raw.columns])
        df_raw = pd.merge(df_raw, coords_sites, on='project_site', how='inner')

# Date handling
date_col = 'date' if 'date' in df_raw.columns else ('today' if 'today' in df_raw.columns else ('Date' if 'Date' in df_raw.columns else None))
if date_col and not is_restoration:
    df_raw[date_col] = pd.to_datetime(df_raw[date_col], errors='coerce').dt.date

# Filters
st.subheader("⚙️ Poster Filters & Scope")
if is_restoration:
    col_f1, col_f2 = st.columns(2)
else:
    col_f1, col_f2, col_f3 = st.columns(3)

# 1. Date filter
with col_f1:
    if date_col:
        valid_dates = df_raw[date_col].dropna()
        min_date = valid_dates.min() if not valid_dates.empty else date(2022, 1, 1)
        max_date = valid_dates.max() if not valid_dates.empty else date.today()

        date_range = st.date_input(
            "Reporting Date Range:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        if len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date, end_date = min_date, max_date
    else:
        start_date, end_date = "N/A", "N/A"

# 2. Location filter
with col_f2:
    if is_restoration:
        loc_col = 'project_site' if 'project_site' in df_raw.columns else 'site_name'
    else:
        loc_col = 'landing_site' if 'landing_site' in df_raw.columns else 'market'

    all_locs = sorted(df_raw[loc_col].dropna().unique().tolist()) if loc_col in df_raw.columns else []
    selected_locs = st.multiselect(
        f"Select {clean_label(loc_col)}(s):",
        options=all_locs,
        default=all_locs
    )

# 3. Group filter (for Bony Fishes & Sharks/Rays; Restoration uses all records for selected project_sites)
if not is_restoration:
    with col_f3:
        if is_sharks:
            group_col = 'type' if 'type' in df_raw.columns else None
            default_groups = ['Shark', 'Ray']
        else:
            group_col = 'group_catch' if 'group_catch' in df_raw.columns else None
            default_groups = ['reef_fish', 'tuna_like', 'small_pelagic']

        if group_col and group_col in df_raw.columns:
            all_groups = sorted(df_raw[group_col].dropna().unique().tolist())
            selected_groups = st.multiselect(
                "Target Groups:",
                options=all_groups,
                default=[g for g in default_groups if g in all_groups] or all_groups
            )
        else:
            selected_groups = []
else:
    group_col = None
    selected_groups = []

# Apply Filters
filtered_df = df_raw.copy()
if date_col and isinstance(start_date, (date, datetime)) and isinstance(end_date, (date, datetime)):
    filtered_df = filtered_df[(filtered_df[date_col] >= start_date) & (filtered_df[date_col] <= end_date)]

if selected_locs and loc_col in filtered_df.columns:
    filtered_df = filtered_df[filtered_df[loc_col].isin(selected_locs)]

if selected_groups and group_col and group_col in filtered_df.columns:
    filtered_df = filtered_df[filtered_df[group_col].isin(selected_groups)]

# Metrics Preview (matching restoration.py logic for restoration)
st.markdown("### 📊 Filtered Data Summary")
m1, m2, m3, m4 = st.columns(4)

if is_restoration:
    def _max_by_site(col_name: str) -> float:
        if filtered_df.empty or 'site_name' not in filtered_df.columns or col_name not in filtered_df.columns:
            return 0.0
        s = pd.to_numeric(filtered_df[col_name], errors='coerce')
        return float(np.nansum(s.groupby(filtered_df['site_name']).max()))

    total_transplanted_corals = _max_by_site('total_fragments_transplanted_to_date')
    total_reefstars = _max_by_site('total_reef_starts_deployed_to_date')
    total_nursery_tables = _max_by_site('total_tables_in_nursery_to_date')
    total_area_restored = (total_transplanted_corals / 2) / 1e4

    with m1:
        st.metric("Coral Fragments Transplanted", f"{int(total_transplanted_corals):,}")
    with m2:
        st.metric("Number of Reef Stars Installed", f"{int(total_reefstars):,}")
    with m3:
        st.metric("Number of Tables in Nurseries", f"{int(total_nursery_tables):,}")
    with m4:
        st.metric("Total Area Transplanted (ha)", f"{total_area_restored:,.2f}")
else:
    with m1:
        st.metric("Total Records", f"{len(filtered_df):,}")
    with m2:
        if is_sharks:
            wgt = filtered_df['weight'].sum() if 'weight' in filtered_df.columns else 0
            st.metric("Total Biomass (kg)", f"{wgt:,.1f}")
        else:
            wgt = filtered_df['weight_catch'].sum() if 'weight_catch' in filtered_df.columns else 0
            st.metric("Total Catch (kg)", f"{wgt:,.1f}")
    with m3:
        if is_sharks:
            sp_cnt = len(filtered_df['Scientific_name'].dropna().unique()) if 'Scientific_name' in filtered_df.columns else 0
            st.metric("Species Count", f"{sp_cnt}")
        else:
            avg_w = filtered_df['weight_catch'].mean() if 'weight_catch' in filtered_df.columns else 0
            st.metric("Avg Catch / Trip (kg)", f"{avg_w:,.2f}")
    with m4:
        n_loc = len(filtered_df[loc_col].dropna().unique()) if loc_col in filtered_df.columns else 0
        st.metric("Monitored Locations", f"{n_loc}")

st.markdown("---")

# Poster Action
st.subheader("🚀 Generate A0 Poster")
st.markdown(
    "Click below to generate all high-resolution publication charts, compile the Typst document, "
    "and download the complete A0 poster."
)

if st.button("🎨 Build & Export A0 Poster", type="primary", use_container_width=True):
    if filtered_df.empty:
        st.error("No records found matching the specified filters. Please broaden your filter selection.")
    else:
        with st.spinner("Generating 300 DPI figures & compiling Typst A0 poster..."):
            meta = {
                'start_date': start_date,
                'end_date': end_date,
                'selected_sites': selected_locs,
                'selected_groups': selected_groups
            }
            res = generate_poster(
                df=filtered_df,
                report_type=report_type,
                metadata=meta
            )

            if res['success'] and res['pdf_bytes']:
                st.success(res['message'])
                file_name = f"{report_type}_A0_poster_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                st.download_button(
                    label="📥 Download A0 Poster (PDF)",
                    data=res['pdf_bytes'],
                    file_name=file_name,
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
            else:
                st.warning(res['message'])
                st.info("You can download the full Typst source code and figures archive below:")
                zip_name = f"{report_type}_poster_bundle_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
                st.download_button(
                    label="📦 Download Complete Typst Bundle (.zip)",
                    data=res['zip_bytes'],
                    file_name=zip_name,
                    mime="application/zip",
                    use_container_width=True
                )