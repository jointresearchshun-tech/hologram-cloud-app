import streamlit as st
from services.github_storage import GithubStorage

def file_operations_ui():
    st.subheader("📂 File Operations")

    mode = st.radio("Select file source:", ["Local DATA folder", "GitHub DATA folder"])

    if mode == "Local DATA folder":
        uploaded = st.file_uploader("Upload a file", type=["txt", "csv", "json", "png", "jpg"])
        if uploaded:
            st.success(f"File uploaded: {uploaded.name}")
            content = uploaded.read()
            st.code(content[:500], language="text")

    elif mode == "GitHub DATA folder":
        token = st.secrets["github"]["token"]
        repo_name = st.secrets["github"]["repo"]
        storage = GithubStorage(token, repo_name)

        files = storage.list_files("DATA")
        selected = st.selectbox("Select a file in GitHub/DATA:", files)

        if selected:
            content = storage.download_file(selected).decode("utf-8", errors="ignore")
            st.text_area("File content", value=content, height=300, key="github_file_editor")

            if st.button("💾 Save changes"):
                storage.upload_file(selected, content.encode("utf-8"))
                st.success("File updated on GitHub ✅")
