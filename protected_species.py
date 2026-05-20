import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Config ---
st.set_page_config(
    page_title="MarineSentinel Inventory Hub",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS for Card UI ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    .species-card {
        background-color: white;
        padding: 0px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
        transition: all 0.3s;
        overflow: hidden;
    }
    .species-card:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        transform: translateY(-4px);
    }
    .card-img { width: 100%; height: 150px; object-fit: cover; }
    .card-content { padding: 15px; }
    .badge {
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: bold;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 8px;
    }
    .badge-no_trading { background-color: #fee2e2; color: #ef4444; }
    .badge-no_landing { background-color: red; color: yellow; }
    .taxa-group {
        color: #3b82f6;
        font-size: 10px;
        font-weight: bold;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .species-name { font-size: 14px; font-weight: bold; color: #1e293b; margin: 0; }
    .scientific-name { font-size: 11px; color: #94a3b8; font-style: italic; }
    </style>
""", unsafe_allow_html=True)

# --- Data Loading ---
CSV_URL = 'https://docs.google.com/spreadsheets/d/1N8ts_6x-zI2QYiQt7HwX3cyvZaWtUTaU2IlxqRY5qzY/export?format=csv&gid=1557232272'

@st.cache_data
def load_data():
    return pd.read_csv(CSV_URL)

df = load_data()

# --- Sidebar Filters ---
with st.sidebar:
    
    search_term = st.text_input("Search catalog...", placeholder="Name, family, genus...")
    groups = ['ALL GROUPS'] + sorted([str(g) for g in df['Group'].unique() if pd.notna(g)])
    selected_group = st.selectbox("Taxa Group", options=groups)
    statuses = ['ALL STATUSES'] + sorted([str(s).upper() for s in df['Provision'].unique() if pd.notna(s)])
    selected_status = st.selectbox("Provision Status", options=statuses)
    
    st.divider()
    view_mode = st.radio("View Mode", options=["Grid", "List"], horizontal=True)

# --- Filter Logic ---
filtered_df = df.copy()
if search_term:
    search_term = search_term.lower()
    mask = (filtered_df['Common name'].str.lower().fillna('').str.contains(search_term) |
            filtered_df['Family'].str.lower().fillna('').str.contains(search_term) |
            (filtered_df['Genus'].str.lower().fillna('') + ' ' + filtered_df['Species'].str.lower().fillna('')).str.contains(search_term))
    filtered_df = filtered_df[mask]

if selected_group != 'ALL GROUPS':
    filtered_df = filtered_df[filtered_df['Group'] == selected_group]
if selected_status != 'ALL STATUSES':
    filtered_df = filtered_df[filtered_df['Provision'].str.upper() == selected_status]

# --- Dashboard Layout ---
st.title("Zanzibar Protected Species List")

# Metric Cards
m1, m2, m3, m4 = st.columns(4)
m1.metric("TOTAL CATALOG", len(df))
m2.metric("NO LANDING", len(df[df['Provision'].str.lower() == 'no landing']))
m3.metric("NO TRADING", len(df[df['Provision'].str.lower() == 'no trading']))
m4.metric("TAXA GROUPS", df['Group'].nunique())

# Chart
st.markdown("### Distribution by Taxonomy Group")
group_counts = df.groupby('Group').size().reset_index(name='count')
fig = px.bar(group_counts, x='count', y='Group', orientation='h', 
             color_discrete_sequence=['#3b82f6'], template='plotly_white', height=350)
fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), xaxis_title=None, yaxis_title=None, 
                  yaxis={'categoryorder':'total ascending'})
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
                status = str(row['Provision']).lower()
                badge_class = "badge-no_trading" if status == 'no trading' else "badge-no_landing"
                img = row['Image'] if pd.notna(row['Image']) else "https://via.placeholder.com/400x300?text=No+Image"
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
    st.dataframe(filtered_df[['Common name', 'Genus', 'Species', 'Group', 'Family', 'Provision']], 
                 use_container_width=True, hide_index=True)
