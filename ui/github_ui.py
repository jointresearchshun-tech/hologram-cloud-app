import streamlit as st
from services.github_storage import GithubStorage

def setup_github_connection():
    st.subheader("🔗 GitHub Connection")

    token = st.text_input("GitHub Personal Access Token", type="password")
    repo_name = st.text_input("Repository (e.g. user/repo)")

    if st.button("Connect"):
        if token and repo_name:
            try:
                github_client = GithubStorage(token, repo_name)
                st.session_state["github_client"] = github_client
                st.success(f"Connected to {repo_name}")
                return True
            except Exception as e:
                st.error(f"Connection failed: {e}")
                return False
        else:
            st.warning("Please provide both token and repository name.")
            return False

    return "github_client" in st.session_state
