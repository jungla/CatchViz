import streamlit as st
from config.settings import CSS_DIR

def load_css(filename: str = "global.css"):
    """Inject CSS stylesheet into Streamlit page."""
    css_file = CSS_DIR / filename
    if css_file.is_file():
        with open(css_file, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
