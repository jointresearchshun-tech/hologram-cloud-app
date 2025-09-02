import streamlit as st
from services.github_storage import GithubStorage

def main():
    st.set_page_config(page_title="GitHub File Manager", layout="wide")
    st.title("📂 GitHub File Manager")

    # Load GitHub credentials from secrets
    try:
        token = st.secrets["github"]["token"]
        repo = st.secrets["github"]["repo"]
    except Exception as e:
        st.error("❌ Missing GitHub credentials in secrets.toml")
        st.stop()

    storage = GithubStorage(token, repo)

    # --- Upload file ---
    st.subheader("⬆️ Upload File")
    uploaded_file = st.file_uploader("Choose a file", type=None)
    if uploaded_file is not None:
        content = uploaded_file.read()
        file_path = f"uploads/{uploaded_file.name}"
        try:
            storage.upload_file(file_path, content)
            st.success(f"✅ Uploaded `{file_path}` to GitHub")
        except Exception as e:
            st.error(f"❌ Upload failed: {str(e)}")

    # --- List files ---
    st.subheader("📋 Files in Repository")
    files = storage.list_files("uploads")
    if not files:
        st.info("No files found in `uploads/` folder.")
    else:
        st.write("### Available Files:")
        for f in files:
            st.write(f"- {f}")

        # --- Download file ---
        file_to_download = st.selectbox("Select a file to download", files)
        if st.button("⬇️ Download selected file"):
            try:
                data = storage.download_file(file_to_download)
                st.download_button("Download File", data, file_to_download)
            except Exception as e:
                st.error(f"❌ Download failed: {str(e)}")

        # --- Delete file ---
        file_to_delete = st.selectbox("Select a file to delete", files)
        if st.button("🗑️ Delete selected file"):
            try:
                storage.delete_file(file_to_delete)
                st.success(f"✅ Deleted `{file_to_delete}` from GitHub")
            except Exception as e:
                st.error(f"❌ Delete failed: {str(e)}")


if __name__ == "__main__":
    main()
