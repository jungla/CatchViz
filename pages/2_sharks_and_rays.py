import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from src.data_loader import load_shark_data, load_iucn_reference
from src.components.headers import render_page_header
from src.components.maps import render_site_map

# --- Data Loading ---
df = load_shark_data()
df_IUCN = load_iucn_reference()

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

# Market filter
all_markets = sorted(df["market"].dropna().unique())
selected_markets = st.sidebar.multiselect(
    "Select Market(s):",
    options=all_markets,
    default=all_markets,
    key="market_filter"
)

# Landing site filter
all_sites = sorted(df["landing_site"].dropna().unique())
selected_sites = st.sidebar.multiselect(
    "Select Landing Site(s):",
    options=all_sites,
    default=all_sites,
    key="site_filter"
)

# Group filter
all_groups = ["Ray", "Shark"]
selected_groups = st.sidebar.multiselect(
    "Select Group(s):",
    options=all_groups,
    default=["Ray", "Shark"],
    key="selected_groups"
)

# --- Apply Filters ---
filtered_df = df[
    (df["date"] >= start_date) &
    (df["date"] <= end_date) &
    (df["landing_site"].isin(selected_sites) | df["market"].isin(selected_markets)) &
    (df["type"].isin(selected_groups))
].copy()

# --- Header ---
render_page_header(
    subtitle="Landings of Sharks and Rays",
    start_date=start_date,
    end_date=end_date,
    selected_items=selected_sites,
    item_label="sites"
)

# --- Metrics / KPIs ---
if not filtered_df.empty:
    total_records = len(filtered_df["Scientific_name"])
    total_species = len(filtered_df["Scientific_name"].dropna().unique())
    total_weight = filtered_df["weight"].sum()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Number of Records", value=f"{total_records:,}")
    with col2:
        st.metric(label="Number of Species Landed", value=total_species)
    with col3:
        st.metric(label="Total Catch (kg)", value=f"{total_weight:,.2f}")
    st.markdown("---")

    # --- Landing Records Map ---
    st.header("Landing Records")
    coords_lat = filtered_df.groupby("landing_site")["_gps_latitude"].median()
    coords_lon = filtered_df.groupby("landing_site")["_gps_longitude"].median()
    coords_cnt = filtered_df.groupby("landing_site")["_gps_latitude"].count()

    coords = pd.DataFrame({
        "lat": coords_lat,
        "lon": coords_lon,
        "count": coords_cnt * 10
    }).dropna().reset_index()

    render_site_map(coords, lat_col="lat", lon_col="lon", label_col="landing_site", radius_col="count")

    # --- Sampling Effort ---
    con0 = st.container(border=True)
    con0.subheader("Sampling Effort")
    effort_time = filtered_df.set_index("today_raw").groupby("landing_site")["_uuid"].resample("ME").count().reset_index()
    effort_time = effort_time.rename(columns={"today_raw": "today"})

    fig_effort = alt.Chart(effort_time).mark_bar().encode(
        x=alt.X("yearmonth(today):O", title="Date"),
        y=alt.Y("_uuid", title="Number of Records", stack="zero"),
        color="landing_site"
    )
    con0.altair_chart(fig_effort, width="stretch")

    # --- Life History Traits and IUCN Categories ---
    st.header("Life History Traits and IUCN Categories")
    st.dataframe(df_IUCN, width="stretch")

    col_viz1, col_viz2 = st.columns(2)

    # Color definitions
    IUCN_status = ["CR", "EN", "VU", "NT", "LC", "DD", "NE"]
    IUCN_hex_colors = ["#D40000", "#FF7C00", "#FFD800", "#00A859", "#0085C8", "#CCCCCC", "#CCCCCC"]
    color_scale = alt.Scale(domain=IUCN_status, range=IUCN_hex_colors)

    with col_viz1:
        # Top Landings by Species
        con1 = col_viz1.container(border=True)
        con1.subheader("Top Landings by Species")
        landings_species = (
            filtered_df.groupby(["Red_List_Status", "IUCN_color", "Scientific_name"])
            .count()
            .sort_values("_uuid")["_uuid"]
            .reset_index()
        )
        if not landings_species.empty:
            p50 = np.percentile(landings_species["_uuid"], 50)
            landings_species = landings_species[landings_species["_uuid"] > p50].sort_values("_uuid")

        fig_species = alt.Chart(landings_species).mark_bar().encode(
            x=alt.X("Scientific_name", title="Scientific Name", sort=None),
            y=alt.Y("_uuid", title="Number of Records"),
            color=alt.Color("Red_List_Status:N", scale=color_scale, legend=alt.Legend(title="IUCN Red List Status"))
        ).configure_axis(labelLimit=1000)
        con1.altair_chart(fig_species, width="stretch")

        # Maturity Ratio
        con2 = col_viz1.container(border=True)
        con2.subheader("Maturity Ratio")
        con2.markdown("Distribution of the ratios of the number of adults and juveniles landed for each species.")

        filtered_df["maturity"] = np.nan
        # Male ray
        mask_m_ray = (filtered_df["sex"] == "Male") & (filtered_df["Shark_or_Ray"] == "Ray")
        filtered_df.loc[mask_m_ray, "maturity"] = (
            filtered_df.loc[mask_m_ray, "disc_width"].astype(float) /
            filtered_df.loc[mask_m_ray, "Male_size_at_maturity_cm_DW_TL"].astype(float)
        )
        # Female ray
        mask_f_ray = (filtered_df["sex"] == "Female") & (filtered_df["Shark_or_Ray"] == "Ray")
        filtered_df.loc[mask_f_ray, "maturity"] = (
            filtered_df.loc[mask_f_ray, "disc_width"].astype(float) /
            filtered_df.loc[mask_f_ray, "Female_size_at_maturity_cm_DW_TL"].astype(float)
        )
        # Male shark
        mask_m_shark = (filtered_df["sex"] == "Male") & (filtered_df["Shark_or_Ray"] == "Shark")
        filtered_df.loc[mask_m_shark, "maturity"] = (
            filtered_df.loc[mask_m_shark, "total_length"].astype(float) /
            filtered_df.loc[mask_m_shark, "Male_size_at_maturity_cm_DW_TL"].astype(float)
        )
        # Female shark
        mask_f_shark = (filtered_df["sex"] == "Female") & (filtered_df["Shark_or_Ray"] == "Shark")
        filtered_df.loc[mask_f_shark, "maturity"] = (
            filtered_df.loc[mask_f_shark, "total_length"].astype(float) /
            filtered_df.loc[mask_f_shark, "Female_size_at_maturity_cm_DW_TL"].astype(float)
        )

        rule_line = alt.Chart(filtered_df).mark_rule(color="black", size=2).encode(x=alt.X(datum=1))
        fig_maturity = alt.Chart(filtered_df).mark_bar().encode(
            x=alt.X("maturity:Q", title="Maturity Ratio", bin=alt.Bin(extent=[0, 3], step=0.2)),
            y=alt.Y("count():Q", title="Individuals")
        )
        con2.altair_chart(fig_maturity + rule_line, width="stretch")

        # Fishing Gear
        con5 = col_viz1.container(border=True)
        con5.subheader("Fishing Gear")
        con5.markdown("Count of the fishing gear used. In some cases, multiple gears were used during the same fishing trip.")

        gears = [
            "gear_type/basket_traps", "gear_type/hook_line", "gear_type/spear_gun",
            "gear_type/beach_seines", "gear_type/ring_nets", "gear_type/gill_nets_3",
            "gear_type/gill_nets_6", "gear_type/longline", "gear_type/reef_seine_set_net",
            "gear_type/drift_net"
        ]
        gear_records = []
        for gear in gears:
            if gear in filtered_df.columns:
                cnt = (filtered_df[gear] == 1).sum()
                gear_records.append([gear.replace("gear_type/", ""), cnt])

        gear_df = pd.DataFrame(gear_records, columns=["gear_type", "count"]).sort_values(by="count")[-7:]
        base_pie = alt.Chart(gear_df).encode(
            alt.Theta("count:Q").stack(True),
            alt.Color("gear_type:N").legend(None)
        )
        fig_pie = base_pie.mark_arc(outerRadius=120)
        text_pie = base_pie.mark_text(radius=140, size=12, fill="black").encode(text="gear_type:N")
        con5.altair_chart(fig_pie + text_pie, width="stretch")

    with col_viz2:
        # IUCN Status of Landings
        con3 = col_viz2.container(border=True)
        con3.subheader("IUCN Status of Landings")
        iucn_status_df = (
            filtered_df.groupby("Red_List_Status")["_uuid"]
            .count()
            .reset_index()
            .sort_values(by="_uuid", ascending=False)
        )
        iucn_status_df = iucn_status_df[~iucn_status_df["Red_List_Status"].isin([0, "0", np.nan])]

        fig_iucn_bar = alt.Chart(iucn_status_df).mark_bar().encode(
            x=alt.X("Red_List_Status", title="Red List Status", sort=None),
            y=alt.Y("_uuid", title="Number of landings"),
            color=alt.Color("Red_List_Status:N", scale=color_scale, legend=alt.Legend(title="IUCN Red List Status"))
        ).configure_axis(labelLimit=1000)
        con3.altair_chart(fig_iucn_bar, width="stretch")

        # Sex Ratio
        con4 = col_viz2.container(border=True)
        con4.subheader("Sex Ratio")
        con4.markdown("Distribution of the ratios of the number of females and males landed for each species.")

        females = filtered_df[filtered_df["sex"] == "Female"].groupby("Scientific_name")["_uuid"].count()
        males = filtered_df[filtered_df["sex"] == "Male"].groupby("Scientific_name")["_uuid"].count()
        sex_ratio_df = (females / males).reset_index()

        fig_sex_ratio = alt.Chart(sex_ratio_df).mark_bar().encode(
            x=alt.X("_uuid:Q", title="Sex Ratio (female/male)", bin=alt.Bin(extent=[0, 3], step=0.2)),
            y=alt.Y("count():Q", title="Individuals")
        )
        rule_line2 = alt.Chart(filtered_df).mark_rule(color="black", size=2).encode(x=alt.X(datum=1))
        con4.altair_chart(fig_sex_ratio + rule_line2, width="stretch")

        # Targeted
        con6 = col_viz2.container(border=True)
        con6.subheader("Targeted")
        con6.markdown("Count of whether elasmobranchs were targeted during the fishing trip.")

        targeted_df = filtered_df.groupby("targeted").count().reset_index()
        base_targeted = alt.Chart(targeted_df).encode(
            alt.Theta("_uuid:Q").stack(True),
            alt.Color("targeted:N").legend(None)
        )
        fig_tgt_pie = base_targeted.mark_arc(outerRadius=120)
        tgt_text = base_targeted.mark_text(radius=140, size=12, fill="black").encode(text="targeted:N")
        con6.altair_chart(fig_tgt_pie + tgt_text, width="stretch")

else:
    st.markdown("---")
    st.warning("No data available for the selected filters. Showing a preview of all loaded data.")
    st.header("Original Data Preview (Top 10 rows)")
    st.dataframe(df.head(10), width="stretch")
