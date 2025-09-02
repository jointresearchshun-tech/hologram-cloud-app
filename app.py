import streamlit as st
from ui.github_ui import github_connect_ui
from ui.colab_ui import colab_connect_ui
from ui.file_operations_ui import file_operations_ui


def main():
    st.title("🌐 Hologram Cloud App")

    # 1. GitHub connection
    github_connect_ui(auto_connect=True)

    # 2. Google Colab connection
    colab_connect_ui(auto_connect=True)

    # 3. File operations
    file_operations_ui()


if __name__ == "__main__":
    main()
