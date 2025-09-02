import streamlit as st

def file_management_ui():
    st.subheader("📂 File Management")

    github_client = st.session_state.get("github_client")
    if not github_client:
        st.warning("⚠️ Please connect to GitHub first.")
        return

    # Upload
    st.markdown("### Upload File")
    uploaded_file = st.file_uploader("Choose a file to upload")
    if uploaded_file and st.button("Upload to GitHub"):
        try:
            github_client.upload_file(uploaded_file.name, uploaded_file.read())
            st.success(f"Uploaded {uploaded_file.name}")
        except Exception as e:
            st.error(f"Upload failed: {e}")

    st.divider()

    # List & Download & Delete
    st.markdown("### Repository Files (DATA folder only)")
    files = github_client.list_files("data")

    if files:
        for file_path in files:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(file_path)
            with col2:
                if st.button("Download", key=f"dl_{file_path}"):
                    try:
                        content = github_client.download_file(file_path)
                        st.download_button(
                            label="Save File",
                            data=content,
                            file_name=file_path,
                            mime="application/octet-stream",
                            key=f"save_{file_path}"
                        )
                    except Exception as e:
                        st.error(f"Download failed: {e}")
            with col3:
                if st.button("Delete", key=f"del_{file_path}"):
                    try:
                        github_client.delete_file(file_path)
                        st.success(f"Deleted {file_path}")
                        st.rerun()  # ✅ experimental_rerun の代わり
                    except Exception as e:
                        st.error(f"Delete failed: {e}")
    else:
        st.info("No files found in repository.")
