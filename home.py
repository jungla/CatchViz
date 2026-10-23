import streamlit as st

st.set_page_config(
    page_title="WCS Tanzania Data Visualization Platform",
    page_icon="🎣",
    layout="wide" # Use wide layout for more space for charts
)

st.markdown("""
<style>
[data-testid="stSidebarNavItems"] ul {
    font-size: 40px !important; /* Adjust font size as needed */
    color: #ff4b4b !important; /* Adjust font color as needed */
}
</style>
""", unsafe_allow_html=True)

st.logo("img/WCS-logo_only.png", icon_image="img/WCS-logo_only.png", size="large")
#st.sidebar.markdown("WCS Tanzania")

bony_page= st.Page("bony_fishes.py", title="Bony Fishes", icon="🐠")
shark_page = st.Page("sharks_and_rays.py", title="Sharks and Rays Landings", icon="🦈")
id_shark_page = st.Page("elasmobranch_id/inference/identify_sharks_and_rays.py", title="Identify Shark and Ray Species", icon="🔍")
protected_species_page = st.Page("protected_species.py", title="Protected Species List", icon="🐋")
restoration_page = st.Page("restoration.py", title="Coral Reef Restoration", icon="🪸")
program_geographies_page = st.Page("program_geographies.py", title="Program Geographies", icon="🌍")


pg = st.navigation({
    "Program Management": [program_geographies_page],
    "Field Activities": [restoration_page, bony_page, shark_page ],
    "Tools": [protected_species_page, id_shark_page]
}, position="sidebar", expanded=True)
pg.run()
