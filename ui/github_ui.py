import streamlit as st
from services.github_storage import GithubStorage

def github_connect_ui(auto_connect: bool = False):
    st.subheader("🔗 GitHub Connection")

    if "github_client" not in st.session_state:
        st.session_state["github_client"] = None

    if auto_connect:
        try:
            token = st.secrets["github"]["token"]
            repo = st.secrets["github"]["repo"]
            st.session_state["github_client"] = GithubStorage(token, repo)
            st.success(f"✅ Connected to GitHub repository: {repo}")
            return
        except Exception as e:
            st.error(f"❌ Auto connect failed: {e}")

    # Manual input
    token = st.text_input("GitHub Token", type="password")
    repo = st.text_input("Repository (e.g. user/repo)")

    if st.button("Connect to GitHub"):
        if token and repo:
            try:
                st.session_state["github_client"] = GithubStorage(token, repo)
                st.success(f"✅ Connected to GitHub repository: {repo}")
            except Exception as e:
                st.error(f"❌ Connection failed: {e}")
        else:
            st.warning("⚠️ Please provide both token and repository.")
