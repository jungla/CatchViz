import streamlit as st
import folium
import geopandas as gpd
import pandas as pd
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

# Using the abstract meridian grid globe for a clean data-focused feel
st.markdown("# 🌐 Village Intervention Matrix")
st.caption("Live, synchronized spatial distribution of regional development projects")

# 1. Configuration - Replace this with your actual "Publish to Web" CSV URL from Google Sheets
# File -> Share -> Publish to web -> Select Sheet -> Comma-separated values (.csv)
GOOGLE_SHEET_URL = "https://google.com"
SHAPEFILE_PATH = "data/village_boundaries.shp"

INITIATIVE_COLORS = {
    "Clean Water Wells": "#1f77b4",     # Blue
    "Solar Microgrid": "#ff7f0e",       # Orange
    "Mobile Health Clinic": "#2ca02c",  # Green
    "Education Center": "#d62728"       # Red
}

# 2. Programmatic Controls: Sidebar to clear cache or force data fetch
with st.sidebar:
    st.header("⚡ Sync Management")
    if st.button("🔄 Force Fetch Live Sheet Data"):
        st.cache_data.clear()
        st.success("Cache cleared! Fetching fresh rows...")
        st.rerun()

# 3. Reading the live Google Sheet dynamically
@st.cache_data(ttl=60)  # Fetches fresh data every 60 seconds automatically
def fetch_live_sheet(url):
    try:
        df = pd.read_csv(url)
        # Ensure clean text keys for mismatch prevention during merge
        df['village'] = df['village'].astype(str).str.strip()
        df['intervention'] = df['intervention'].astype(str).str.strip()
        
        # Compress repeating village rows into list arrays
        return df.groupby('village')['intervention'].apply(list).reset_index()
    except Exception as e:
        st.error(f"Error connecting to Google Sheet: {e}")
        return None

# 4. Loading the static Shapefile framework
@st.cache_data
def load_base_shapefile(path):
    try:
        gdf = gpd.read_file(path)
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)
        gdf['name'] = gdf['name'].astype(str).str.strip()
        return gdf
    except Exception as e:
        st.error(f"Error loading local shapefile framing: {e}")
        return None

# Load both datasets
grouped_interventions = fetch_live_sheet(GOOGLE_SHEET_URL)
base_spatial_gdf = load_base_shapefile(SHAPEFILE_PATH)

if grouped_interventions is not None and base_spatial_gdf is not None:
    # 5. Live left-join merge matching Shapefile Names to live Google Sheet Village entries
    merged_gdf = base_spatial_gdf.merge(grouped_interventions, left_on='name', right_on='village', how='left')
    merged_gdf['intervention'] = merged_gdf['intervention'].apply(lambda x: x if isinstance(x, list) else [])

    # 6. Center map canvas over actual data boundaries
    center_lat = merged_gdf.geometry.centroid.y.mean()
    center_lon = merged_gdf.geometry.centroid.x.mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="OpenStreetMap")

    # Draw base boundaries
    folium.GeoJson(
        merged_gdf,
        style_function=lambda x: {
            "fillColor": "#f8f9fa",
            "color": "#495057",
            "weight": 2,
            "fillOpacity": 0.3
        },
        tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["Village:"])
    ).add_to(m)

    # 7. Render contextual indicator blocks at polygon thresholds
    for _, row in merged_gdf.iterrows():
        v_interventions = row["intervention"]
        if not v_interventions:
            continue
            
        minx, miny, maxx, maxy = row.geometry.bounds
        anchor_lat = maxy  
        anchor_lon = minx  
        
        badge_html = ""
        for item in v_interventions:
            color = INITIATIVE_COLORS.get(item, "#7f7f7f")
            badge_html += f"""
            <div style="
                width: 14px; 
                height: 14px; 
                background-color: {color}; 
                border: 1.5px solid #ffffff; 
                border-radius: 3px; 
                display: inline-block; 
                margin-right: 3px; 
                box-shadow: 0px 1px 3px rgba(0,0,0,0.3);
            " title="{item}"></div>
            """
            
        container_html = f'<div style="display: flex; white-space: nowrap; padding: 2px;">{badge_html}</div>'
        
        folium.Marker(
            location=[anchor_lat, anchor_lon],
            icon=folium.DivIcon(html=container_html, icon_size=(100, 20), icon_anchor=(0, 0))
        ).add_to(m)

    # 8. Render App Interface
    col1, col2 = st.columns([3, 1])
    with col1:
        st_folium(m, width="100%", height=600)
    with col2:
        st.markdown("### 🎨 Legend Key")
        for name, color in INITIATIVE_COLORS.items():
            st.markdown(f"<span style='color:{color}; font-size:18px;'>■</span> {name}", unsafe_allow_html=True)
else:
    st.info("Configuration check: Awaiting data from both web source connection and filesystem path frameworks.")
