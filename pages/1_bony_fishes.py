from datetime import date
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from src.data_loader import load_catch_data
from src.components.headers import render_page_header
from src.components.maps import render_site_map

# --- Data Loading ---
df = load_catch_data()

# --- Sidebar Filters ---
st.sidebar.header("Filters ⚙️")

if df.empty:
    st.warning("No data loaded. Please check your data source and files.")
    st.header("Filtered Data Records")
    st.dataframe(pd.DataFrame(), width="stretch")
    st.stop()

# Date filter
min_date = date(2022, 1, 1)
max_date = df["today"].max()

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

# Site filter
all_sites = sorted(df["landing_site"].dropna().unique())
selected_sites = st.sidebar.multiselect(
    "Select Site(s):",
    options=all_sites,
    default=all_sites,
    key="site_filter"
)

# Catch group filter
all_groups = sorted(df["group_catch"].dropna().unique())
selected_groups = st.sidebar.multiselect(
    "Select Group(s):",
    options=all_groups,
    default=["reef_fish", "tuna_like", "small_pelagic"],
    key="group_filter"
)

# --- Apply Filters ---
filtered_df = df[
    (df["today"] >= start_date) &
    (df["today"] <= end_date) &
    (df["landing_site"].isin(selected_sites)) &
    (df["group_catch"].isin(selected_groups))
].copy()

# --- Header ---
render_page_header(
    subtitle="Landings of Bony Fishes",
    start_date=start_date,
    end_date=end_date,
    selected_items=selected_sites,
    item_label="sites"
)

# --- Metrics / KPIs ---
if not filtered_df.empty:
    total_catch = filtered_df["weight_catch"].sum()
    num_records_filtered = len(filtered_df)
    avg_catch_per_record = filtered_df["weight_catch"].mean()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Catch (kg)", value=f"{total_catch:,.2f}")
    with col2:
        st.metric(label="Number of Records", value=f"{num_records_filtered:,}")
    with col3:
        st.metric(label="Average Catch per Record (kg)", value=f"{avg_catch_per_record:,.2f}")
    st.markdown("---")

    # --- Landing Records Map ---
    st.header("Landing Records")
    coords_lat = filtered_df.groupby("landing_site")["_gps_latitude"].median()
    coords_lon = filtered_df.groupby("landing_site")["_gps_longitude"].median()
    coords_cnt = filtered_df.groupby("landing_site")["_gps_latitude"].count()

    coords = pd.DataFrame({
        "lat": coords_lat,
        "lon": coords_lon,
        "count": coords_cnt * 3
    }).dropna().reset_index()

    render_site_map(coords, lat_col="lat", lon_col="lon", label_col="landing_site", radius_col="count")

    # --- Sampling Effort ---
    con0 = st.container(border=True)
    con0.subheader("Sampling Effort")
    effort_time = filtered_df.groupby(["today", "landing_site"])["_uuid"].count().reset_index()
    fig_effort = alt.Chart(effort_time).mark_bar().encode(
        x=alt.X("today", title="Date"),
        y=alt.Y("_uuid", title="Number of Records", stack="zero"),
        color="landing_site"
    )
    con0.altair_chart(fig_effort, width="stretch")

    # Side-by-side charts
    col_viz1, col_viz2 = st.columns(2)

    with col_viz1:
        # Landings by Boat Type
        con1 = col_viz1.container(border=True)
        con1.subheader("Landings by type of boat")
        boat_type = filtered_df.groupby("boat_type").count().sort_values(by="_uuid").reset_index()
        fig_boat = alt.Chart(boat_type).mark_bar().encode(
            x=alt.X("boat_type", title="Type of Fishing Vessel", sort=None),
            y=alt.Y("_uuid", title="Number of Records")
        )
        con1.altair_chart(fig_boat, width="stretch")

        # Landings by Species Group
        con2 = col_viz1.container(border=True)
        con2.subheader("Landings by Species Group")
        site_catch_df = filtered_df.groupby(["group_catch", "landing_site"])["_uuid"].count().reset_index().sort_values(by="_uuid", ascending=False)
        fig_group = alt.Chart(site_catch_df).mark_bar().encode(
            x=alt.X("landing_site", title="Landing Site"),
            y=alt.Y("_uuid", title="Number of landings"),
            color="group_catch"
        )
        con2.altair_chart(fig_group, width="stretch")

    with col_viz2:
        # Landings by Gear Type
        con3 = col_viz2.container(border=True)
        con3.subheader("Landings by Gear Type")
        s = pd.Series(filtered_df["gear_type"].dropna()).astype(str)
        exploded_words = s.str.split(expand=False).explode()
        gear_type = pd.DataFrame(exploded_words.value_counts()).reset_index()
        fig_gear = alt.Chart(gear_type).mark_bar().encode(
            x=alt.X("gear_type", title="Type of Gear", sort=None),
            y=alt.Y("count", title="Number of Records")
        )
        con3.altair_chart(fig_gear, width="stretch")

        # Effort by Vessel
        con4 = col_viz2.container(border=True)
        con4.subheader("Effort by Type of Vessel")
        mean_ppl_day = filtered_df.groupby(["today", "landing_site", "boat_type"])["people"].mean()
        effort = (
            filtered_df.groupby(["today", "landing_site", "boat_type"])["people"].sum() +
            mean_ppl_day * filtered_df.groupby(["today", "landing_site", "boat_type"])["boats_landed"].median()
        )
        effort_df = pd.DataFrame(effort.reset_index())
        effort_df["effort"] = pd.DataFrame(effort).values
        effort_df = effort_df[["landing_site", "boat_type", "effort"]].groupby(["landing_site", "boat_type"]).sum().reset_index()

        fig_effort_vessel = alt.Chart(effort_df).mark_bar().encode(
            x=alt.X("landing_site", title="Landing Site"),
            y=alt.Y("effort", title="Number of landings"),
            color="boat_type"
        )
        con4.altair_chart(fig_effort_vessel, width="stretch")

    # --- Catch and Yield Analysis ---
    st.header("Catch and Yield Analysis")
    st.subheader("Catch Per Unit Effort")

    filtered_df["CPUE"] = filtered_df["weight_catch"] / filtered_df["people"] / filtered_df["fishing_duration"]
    cpue_df = filtered_df.replace([np.inf, -np.inf], np.nan)
    cpue_summary = cpue_df.groupby(["today", "landing_site"])["CPUE"].mean().reset_index().dropna()

    fig_cpue = alt.Chart(cpue_summary).mark_circle().encode(
        x=alt.X("today", title="Date"),
        y=alt.Y("CPUE", title="CPUE [kg/fisher/day]"),
        color="landing_site"
    )
    fig_cpue = fig_cpue + fig_cpue.transform_regression("today", "CPUE", method="linear", groupby=["landing_site"]).mark_line(size=4)
    st.altair_chart(fig_cpue, width="stretch")

else:
    st.markdown("---")
    st.warning("No data available for the selected filters. Showing a preview of all loaded data.")
    st.header("Original Data Preview (Top 10 rows)")
    st.dataframe(df.head(10), width="stretch")

st.sidebar.markdown("---")
st.sidebar.info("Data collected with Kobotoolbox at landing sites in Tanzania and updated periodically. Raw data can be found at https://zenodo.org/records/15229813")
