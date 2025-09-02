import streamlit as st
import os
from github_storage import GithubStorage

# Initialize GitHub storage (read secrets from .streamlit/secrets.toml)
github = GithubStorage(
    token=st.secrets["github"]["token"],
    repo_name=st.secrets["github"]["repo"]
)

DATA_DIR = "DATA"
os.makedirs(DATA_DIR, exist_ok=True)

def main():
    st.title("📂 File Manager")

    # Mode selection
    mode = st.radio("Choose operation:", ["Local DATA folder", "Create new file", "GitHub files"])

    # === Local DATA folder ===
    if mode == "Local DATA folder":
        st.subheader("DATA/ Folder Files")

        files = os.listdir(DATA_DIR)
        if files:
            selected = st.selectbox("Select a file:", files)
            file_path = os.path.join(DATA_DIR, selected)

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            st.text_area("File Content:", content, height=200)

        else:
            st.info("No files in DATA/ yet.")

    # === Create new file ===
    elif mode == "Create new file":
        st.subheader("Create a New File in DATA/")

        filename = st.text_input("Filename (e.g., test.txt):")
        content = st.text_area("Content:")

        if st.button("Save"):
            if filename:
                file_path = os.path.join(DATA_DIR, filename)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                st.success(f"File saved: {file_path}")
            else:
                st.error("Please enter a filename.")

    # === GitHub files ===
    elif mode == "GitHub files":
        st.subheader("GitHub Files")

        files = github.list_files()
        if files:
            selected = st.selectbox("Select a GitHub file:", files)

            if st.button("Download from GitHub"):
                content = github.download_file(selected).decode("utf-8", errors="ignore")
                st.text_area("File Content:", content, height=200)

                # Optionally save to local DATA folder
                save_local = st.checkbox("Also save to DATA/")
                if save_local:
                    local_path = os.path.join(DATA_DIR, os.path.basename(selected))
                    with open(local_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    st.success(f"Saved to {local_path}")
        else:
            st.info("No files found in GitHub repository.")

if __name__ == "__main__":
    main()
