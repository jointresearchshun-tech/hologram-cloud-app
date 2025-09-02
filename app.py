import streamlit as st
from ui.github_ui import github_connect_ui
from ui.processing_ui import processing_ui


from practical_colab_solution.integrated_colab_ui import colab_connect_ui  
from ui.file_ui import file_management_ui


def main():
    st.title("🔗 GitHub & Google Colab Integration App")

    # GitHub connection
    github_connect_ui(auto_connect=True)

    # Colab connection (auto from secrets.toml)
    colab_connect_ui(auto_connect=True)

    # File management UI
    file_management_ui()

    processing_ui()


if __name__ == "__main__":
    main()
