import streamlit as st
from pathlib import Path

def load_css(path: str = "theme.css"):
    """Load a CSS file into Streamlit page."""
    p = Path(path)
    if not p.exists():
        st.warning(f"CSS not found: {path}")
        return
    css = p.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

