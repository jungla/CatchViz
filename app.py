import streamlit as st
from config.settings import IMG_DIR
from src.components.styles import load_css

st.set_page_config(
    page_title="WCS Tanzania Data Visualization Platform",
    page_icon="🎣",
    layout="wide"
)

# Load shared styles
load_css("global.css")

# App logo
logo_path = IMG_DIR / "WCS-logo_only.png"
if not logo_path.exists():
    logo_path = "img/WCS-logo_only.png"
else:
    logo_path = str(logo_path)

st.logo(logo_path, icon_image=logo_path, size="large")

# Pages configuration
bony_page = st.Page("pages/1_bony_fishes.py", title="Bony Fishes", icon="🐠")
shark_page = st.Page("pages/2_sharks_and_rays.py", title="Sharks and Rays", icon="🦈")
protected_species_page = st.Page("pages/3_protected_species.py", title="Protected Species List", icon="🐋")
restoration_page = st.Page("pages/4_restoration.py", title="Coral Reef Restoration", icon="🌊")

pg = st.navigation(
    [bony_page, shark_page, protected_species_page, restoration_page],
    position="sidebar",
    expanded=True
)
pg.run()
