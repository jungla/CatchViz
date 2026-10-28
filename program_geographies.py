import streamlit as st
import folium
import geopandas as gpd
import pandas as pd
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

# CSS snippet to remove the default blue square/outline when a map polygon is clicked
st.markdown(
    """
    <style>
    .leaflet-interactive:focus {
        outline: none !important;
    }
    svg:focus {
        outline: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Using the abstract meridian grid globe for a clean data-focused feel
st.markdown("# 🌐 WCS Tanzania Marine Program Areas")
st.caption("Live, synchronized spatial distribution of regional development projects")

# 1. Configuration 
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1XsjrpSbwfzijQiE09-mNfKnBVZ_pe89sr8GF6GTK07Q/export?format=csv&gid=1881832883"

SHAPEFILE_CMA_PATH = "shapefiles/WCS_Project_Areas.gpkg"
SHAPEFILE_MPA_PATH = "shapefiles/MPAs_TZ_ZNZ.gpkg"

# Updated colors to be highly distinguishable
INITIATIVE_COLORS = {
    "MPA authority support": "#1f77b4",     # Blue
    "Ecosystem restoration": "#ff7f0e",     # Orange
    "Infrastructure support": "#2ca02c",    # Green
    "Governance support": "#9467bd",        # Purple
    "Ecosystem assessment": "#8c564b",      # Brown
    "Fisheries management": "#e377c2",      # Pink
    "Livelihood support": "#d62728"         # Red
}

# 2. Programmatic Controls: Sidebar to clear cache or force data fetch
with st.sidebar:
    st.header("⚡ Sync Management")
    if st.button("🔄 Force Fetch Live Sheet Data"):
        st.cache_data.clear()
        st.success("Cache cleared! Fetching fresh rows...")
        st.rerun()

# 3. Reading the live Google Sheet dynamically
@st.cache_data(ttl=60)
def fetch_live_sheet(url):
    try:
        df = pd.read_csv(url)
        # Clean string columns and handle empty 'nan' cells
        df['CMA/CMG'] = df['CMA/CMG'].astype(str).str.strip()
        df['General Description'] = df['General Description'].fillna("").astype(str).str.strip()
        df['Specific Intervention'] = df['Specific Intervention'].fillna("").astype(str).str.strip()
        
        # Filter out completely empty rows
        df = df[(df['CMA/CMG'] != "nan") & (df['CMA/CMG'] != "")]

        def process_group(g):
            # 1. Get UNIQUE categories for the colored squares on the map
            unique_cats = [c for c in g['General Description'].unique() if c and c.lower() != 'nan']
            
            # 2. Build the detailed intervention text for the top panel
            panel_lines = []
            for cat in unique_cats:
                # Find all specific interventions belonging to this category
                interventions = [
                    i for i in g[g['General Description'] == cat]['Specific Intervention'].unique() 
                    if i and i.lower() != 'nan'
                ]
                if interventions:
                    # Format as: "Category: Intervention 1, Intervention 2"
                    panel_lines.append(f"<b>{cat}:</b> {', '.join(interventions)}")
                else:
                    panel_lines.append(f"<b>{cat}</b>")
                    
            return pd.Series({
                'Categories': unique_cats,
                'ActivitiesHTML': "<br>".join(panel_lines) # Multi-line string for the UI panel
            })
            
        return df.groupby('CMA/CMG').apply(process_group).reset_index()
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
        if 'name' in gdf.columns:
            gdf['name'] = gdf['name'].astype(str).str.strip()
        return gdf
    except Exception as e:
        st.error(f"Error loading local shapefile framing: {e}")
        return None

# Load all datasets
grouped_interventions = fetch_live_sheet(GOOGLE_SHEET_URL)
cma_spatial_gdf = load_base_shapefile(SHAPEFILE_CMA_PATH)
mpa_spatial_gdf = load_base_shapefile(SHAPEFILE_MPA_PATH)

if grouped_interventions is not None and cma_spatial_gdf is not None and mpa_spatial_gdf is not None:
    
    # 5. Live left-join merge
    merged_gdf = cma_spatial_gdf.merge(grouped_interventions, left_on='name', right_on='CMA/CMG', how='left')
    
    # Ensure missing data is handled smoothly after the merge
    merged_gdf['Categories'] = merged_gdf['Categories'].apply(lambda x: x if isinstance(x, list) else [])
    merged_gdf['ActivitiesHTML'] = merged_gdf['ActivitiesHTML'].fillna("")

    # 6. Center map canvas
    center_lat = merged_gdf.geometry.centroid.y.mean()
    center_lon = merged_gdf.geometry.centroid.x.mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="OpenStreetMap")

    # Draw MPA Background Layer FIRST
    folium.GeoJson(
        mpa_spatial_gdf,
        style_function=lambda x: {
            "fillColor": "#add8e6",
            "color": "#00008b",
            "weight": 1.5,
            "fillOpacity": 0.15,
            "dashArray": "4 4"
        },
        tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["MPA:"]) if 'name' in mpa_spatial_gdf.columns else None,
        name="Marine Protected Areas (MPA)"
    ).add_to(m)

    # Draw CFMA Base Boundaries with hover highlight
    folium.GeoJson(
        merged_gdf,
        style_function=lambda x: {
            "fillColor": "#f8f9fa",
            "color": "#495057",
            "weight": 2,
            "fillOpacity": 0.4
        },
        highlight_function=lambda x: {
            "fillColor": "#e9ecef",
            "color": "#000000",
            "weight": 3,
            "fillOpacity": 0.6
        },
        tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["CMA:"]),
        name="Community Managed Area (CMA)"
    ).add_to(m)

    folium.LayerControl().add_to(m)

    # 7. Render contextual indicator blocks at polygon thresholds
    for _, row in merged_gdf.iterrows():
        # Iterate over the UNIQUE list of categories we generated in step 3
        v_interventions = row["Categories"]
        if not v_interventions or len(v_interventions) == 0:
            continue
            
        minx, miny, maxx, maxy = row.geometry.bounds
        anchor_lat = maxy  
        anchor_lon = minx  
        
        badge_html = ""
        for item in v_interventions:
            color = INITIATIVE_COLORS.get(item, "#7f7f7f")
            # Collapsed HTML string to avoid markdown parsing errors
            badge_html += f'<div style="width: 14px; height: 14px; background-color: {color}; border: 1.5px solid #ffffff; border-radius: 3px; display: inline-block; margin-right: 3px; box-shadow: 0px 1px 3px rgba(0,0,0,0.3);" title="{item}"></div>'
            
        container_html = f'<div style="display: flex; white-space: nowrap; padding: 2px;">{badge_html}</div>'
        
        folium.Marker(
            location=[anchor_lat, anchor_lon],
            icon=folium.DivIcon(html=container_html, icon_size=(100, 20), icon_anchor=(0, 0))
        ).add_to(m)

    # 8. Render App Interface
    
    # Read the map state from session state FIRST to prevent layout jumping
    map_state = st.session_state.get("wcs_map", {})
    
    # Determine what text and color to display in the info box
    info_text = "👆 <b>Click on any CMA on the map</b> to view its specific active interventions here."
    bg_color = "#e9ecef" # Default gray-ish background
    
    if map_state and map_state.get("last_active_drawing"):
        clicked_props = map_state["last_active_drawing"]["properties"]
        area_name = clicked_props.get("name", "Selected Area")
        
        # Look for our pre-formatted HTML string containing the Specific Interventions
        if "ActivitiesHTML" in clicked_props:
            activities = clicked_props["ActivitiesHTML"]
            if activities:
                info_text = f"<b>📍 {area_name} Interventions:</b><br>{activities}"
                bg_color = "#d4edda" # Success green
            else:
                info_text = f"<b>📍 {area_name}:</b> No active interventions registered at this time."
                bg_color = "#fff3cd" # Warning yellow
        else:
            info_text = f"<b>📍 {area_name}</b> (Marine Protected Area layer selected)"
            bg_color = "#cce5ff" # Info blue
            
    # Render the fixed-height dynamic info container BEFORE the map so nothing shifts
    st.markdown(
        f"""
        <div style="min-height: 55px; padding: 15px; border-radius: 8px; background-color: {bg_color}; margin-bottom: 15px; border: 1px solid #ced4da; display: flex; flex-direction: column; justify-content: center;">
            <span style="font-size: 16px; color: #212529; margin: 0; line-height: 1.6;">{info_text}</span>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # Render the map 
    st_folium(m, width="100%", height=650, key="wcs_map") 
    
    # --- NEW RESPONSIVE LEGEND (FIXED HTML FORMATTING) ---
    st.markdown("### 🎨 Legend Key")
    
    # Build a responsive flexbox layout for the legend, formatted cleanly on single lines
    legend_html = '<div style="display: flex; flex-wrap: wrap; gap: 24px; padding: 10px 0;">'
    for name, color in INITIATIVE_COLORS.items():
        legend_html += (
            f'<div style="display: flex; align-items: center; gap: 10px;">'
            f'<div style="width: 24px; height: 24px; background-color: {color}; border-radius: 4px; border: 1px solid #999; box-shadow: 1px 1px 3px rgba(0,0,0,0.2);"></div>'
            f'<span style="font-size: 16px; font-weight: 500; color: #212529;">{name}</span>'
            f'</div>'
        )
    legend_html += '</div>'
    
    st.markdown(legend_html, unsafe_allow_html=True)
            
else:
    st.info("Configuration check: Awaiting data from both web source connection and filesystem path frameworks.")