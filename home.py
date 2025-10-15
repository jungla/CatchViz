import streamlit as st


st.markdown("""
<style>
[data-testid="stSidebarNavItems"] ul {
    font-size: 40px !important; /* Adjust font size as needed */
    color: #ff4b4b !important; /* Adjust font color as needed */
}
</style>
""", unsafe_allow_html=True)

bony_page= st.Page("bony_fishes.py", title="Bony Fishes", icon="🐠")
shark_page = st.Page("sharks_and_rays.py", title="Sharks and Rays", icon="🦈")

pg = st.navigation([bony_page, shark_page], position="sidebar", expanded=True)
st.set_page_config(page_title="Data manager", page_icon=":material/edit:")
pg.run()
