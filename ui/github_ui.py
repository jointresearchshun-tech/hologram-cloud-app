import streamlit as st
from services.github_service import connect_github

def github_connect_ui(auto_connect=False):
    st.subheader("🔗 GitHub Connection")

    token = st.secrets["github"]["token"]
    repo = st.secrets["github"]["repo"]

    if auto_connect:
        success, msg = connect_github(token, repo)
        if success:
            st.success("✅ Connected to GitHub automatically!")
        else:
            st.error(f"❌ GitHub connection failed: {msg}")
        return

    # Manual connection with button
    if st.button("Connect to GitHub"):
        success, msg = connect_github(token, repo)
        if success:
            st.success("✅ Connected to GitHub!")
        else:
            st.error(f"❌ GitHub connection failed: {msg}")
