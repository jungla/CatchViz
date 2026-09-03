import streamlit as st
import pandas as pd
import plotly.express as px
from src.data_loader import load_protected_species_data
from src.components.styles import load_css

# --- Load Styles & Data ---
load_css("global.css")
load_css("species_card.css")

df = load_protected_species_data()

# --- Sidebar Filters ---
with st.sidebar:
    st.header("Filters ⚙️")
    search_term = st.text_input("Search catalog...", placeholder="Name, family, genus...")
    groups = ["ALL GROUPS"] + sorted([str(g) for g in df["Group"].unique() if pd.notna(g)])
    selected_group = st.selectbox("Taxa Group", options=groups)
    statuses = ["ALL STATUSES"] + sorted([str(s).upper() for s in df["Provision"].unique() if pd.notna(s)])
    selected_status = st.selectbox("Provision Status", options=statuses)

    st.divider()
    view_mode = st.radio("View Mode", options=["Grid", "List"], horizontal=True)

# --- Filter Logic ---
filtered_df = df.copy()
if search_term:
    search_term = search_term.lower()
    mask = (
        filtered_df["Common name"].str.lower().fillna("").str.contains(search_term) |
        filtered_df["Family"].str.lower().fillna("").str.contains(search_term) |
        (filtered_df["Genus"].str.lower().fillna("") + " " + filtered_df["Species"].str.lower().fillna("")).str.contains(search_term)
    )
    filtered_df = filtered_df[mask]

if selected_group != "ALL GROUPS":
    filtered_df = filtered_df[filtered_df["Group"] == selected_group]
if selected_status != "ALL STATUSES":
    filtered_df = filtered_df[filtered_df["Provision"].str.upper() == selected_status]

# --- Dashboard Layout ---
st.markdown("""
<h1 class="h1-custom">Marine Protected Species</h1>
<h2 class="h2-custom">Zanzibar Protected Species Catalog</h2>
""", unsafe_allow_html=True)
st.divider()

# Metric Cards
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("TOTAL CATALOG", len(df))
m2.metric("ALWAYS RELEASE", len(df[df["Provision"].str.lower() == "always release"]))
m3.metric("ONLY CONSUMPTION", len(df[df["Provision"].str.lower() == "only consumption"]))
m4.metric("RESEARCH ONLY", len(df[df["Provision"].str.lower() == "research only"]))
m5.metric("TAXA GROUPS", df["Group"].nunique())

# Guidance Cards
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("ALWAYS RELEASE")
    st.info("Species that are illegal to land. If caught, dead or alive, they must be released and reported to the fishery official.")
with col2:
    st.subheader("ONLY CONSUMPTION")
    st.info("Ecologically threatened species that cannot be targeted. If caught alive, release. If caught dead, can be landed for consumption, not commercial trade.")
with col3:
    st.subheader("RESEARCH ONLY")
    st.info("Species important for science and highly threatened. If caught dead or injured, hand over to a government official or recognized researcher.")

# Distribution Chart
st.markdown("### Distribution by Taxonomy Group")
group_counts = df.groupby("Group").size().reset_index(name="count")
fig = px.bar(
    group_counts, x="count", y="Group", orientation="h",
    color_discrete_sequence=["#3b82f6"], template="plotly_white", height=350
)
fig.update_layout(
    margin=dict(l=20, r=20, t=20, b=20), xaxis_title=None, yaxis_title=None,
    yaxis={"categoryorder": "total ascending"}
)
st.plotly_chart(fig, use_container_width=True)

# Catalog
st.markdown(f"### Inventory Catalog ({len(filtered_df)} records)")
if filtered_df.empty:
    st.warning("No results found.")
elif view_mode == "Grid":
    grid_cols = 4
    for i in range(0, len(filtered_df), grid_cols):
        cols = st.columns(grid_cols)
        for j, (idx, row) in enumerate(filtered_df.iloc[i:i+grid_cols].iterrows()):
            with cols[j]:
                status = str(row["Provision"]).lower()
                if status == "only consumption":
                    badge_class = "badge-consumption"
                elif status == "always release":
                    badge_class = "badge-release"
                else:
                    badge_class = "badge-research"
                img = row["Image"] if pd.notna(row["Image"]) else "https://via.placeholder.com/400x300?text=No+Image"
                st.markdown(f"""
                <div class="species-card">
                    <img src="{img}" class="card-img">
                    <div class="card-content">
                        <span class="badge {badge_class}">{row['Provision']}</span>
                        <div class="taxa-group">{row['Group']}</div>
                        <p class="species-name">{row['Common name']}</p>
                        <p class="scientific-name">{row['Family']} {row['Genus']} {row['Species']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
else:
    st.dataframe(
        filtered_df[["Common name", "Genus", "Species", "Group", "Family", "Provision"]],
        use_container_width=True, hide_index=True
    )
