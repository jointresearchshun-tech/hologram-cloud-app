import os
import streamlit as st
from github_storage import GithubStorage

# GitHub storage client
github = GithubStorage(
    token=st.secrets["github"]["token"],
    repo=st.secrets["github"]["repo"]
)

# Local DATA folder
DATA_DIR = "DATA"
os.makedirs(DATA_DIR, exist_ok=True)

def file_operations_ui():
    st.subheader("📂 File Operations")

    source = st.radio("Select file source:", ["GitHub DATA folder", "Local DATA folder"])

    # ===============================
    # GitHub DATA folder operations
    # ===============================
    if source == "GitHub DATA folder":
        files = [f for f in github.list_files() if f.startswith("DATA/")]

        if files:
            selected = st.selectbox("Select a GitHub file:", files)
            if selected:
                # Load file content
                content = github.download_file(selected).decode("utf-8", errors="ignore")
                new_content = st.text_area("Edit GitHub file:", content, height=200)

                commit_message = st.text_input("Commit message:", value=f"Update {selected} via Streamlit")

                if st.button("Save changes to GitHub"):
                    github.upload_file(
                        filepath=selected,
                        content=new_content.encode("utf-8"),
                        commit_message=commit_message
                    )
                    st.success(f"✅ Changes saved to GitHub: {selected}")
        else:
            st.info("No files found in GitHub DATA/ folder.")

    # ===============================
    # Local DATA folder operations
    # ===============================
    elif source == "Local DATA folder":
        files = os.listdir(DATA_DIR)

        if files:
            selected = st.selectbox("Select a local file:", files)
            file_path = os.path.join(DATA_DIR, selected)

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            new_content = st.text_area("Edit local file:", content, height=200)

            if st.button("Save changes locally"):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                st.success(f"✅ Local file updated: {file_path}")
        else:
            st.info("No files in local DATA/ yet.")

        st.subheader("Create a New Local File")
        filename = st.text_input("Filename (e.g., test.txt):")
        content = st.text_area("Content for new file:")

        if st.button("Save new local file"):
            if filename:
                file_path = os.path.join(DATA_DIR, filename)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                st.success(f"File saved: {file_path}")
            else:
                st.error("Please enter a filename.")
