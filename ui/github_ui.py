import streamlit as st
from services.github_storage import GithubStorage

def github_connect_ui(auto_connect=False):
    st.subheader("🔗 GitHub Connection")

    if auto_connect:
        try:
            token = st.secrets["github"]["token"]
            repo = st.secrets["github"]["repo"]
            st.session_state["github_client"] = GithubStorage(token, repo)
            st.success(f"Connected to {repo}")
        except Exception as e:
            st.error(f"GitHub connection failed: {e}")
    else:
        token = st.text_input("GitHub Token", type="password")
        repo = st.text_input("Repository (e.g. user/repo)")
        if st.button("Connect"):
            try:
                st.session_state["github_client"] = GithubStorage(token, repo)
                st.success(f"Connected to {repo}")
            except Exception as e:
                st.error(f"Connection failed: {e}")
