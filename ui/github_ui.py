import streamlit as st

def github_connect_ui(auto_connect=False):
    st.subheader("🔗 GitHub Connection")

    token = st.secrets["github"]["token"]
    repo = st.secrets["github"]["repo"]  # ✅ toml の repo に対応

    if auto_connect:
        from services.github_service import connect_github
        success, msg = connect_github(token, repo)
        if success:
            st.success("✅ Connected to GitHub automatically!")
        else:
            st.error(f"❌ GitHub connection failed: {msg}")
        return

    # Manual connect button
    if st.button("Connect to GitHub"):
        from services.github_service import connect_github
        success, msg = connect_github(token, repo)
        if success:
            st.success("✅ Connected to GitHub!")
        else:
            st.error(f"❌ GitHub connection failed: {msg}")
