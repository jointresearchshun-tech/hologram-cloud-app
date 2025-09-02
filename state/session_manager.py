import streamlit as st

def initialize_session_state():
    defaults = {
        "github_client": None,
        "colab_servers": [],
        "jobs": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
