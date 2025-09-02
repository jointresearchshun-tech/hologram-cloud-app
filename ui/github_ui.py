def github_connect_ui(auto_connect=False):
    st.subheader("🔗 GitHub Connection")

    token = st.secrets["github"]["token"]
    repo = st.secrets["github"]["repo"]

    if auto_connect:
        from services.github_service import connect_github
        success, msg = connect_github(token, repo)
        if success:
            st.success("✅ Connected to GitHub automatically!")
        else:
            st.error(f"❌ GitHub connection failed: {msg}")
        return

    # 通常のボタン操作版
    if st.button("Connect to GitHub"):
        from services.github_service import connect_github
        success, msg = connect_github(token, repo)
        if success:
            st.success("✅ Connected to GitHub!")
        else:
            st.error(f"❌ GitHub connection failed: {msg}")
