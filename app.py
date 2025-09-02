import streamlit as st
from config.logging_config import setup_logging
from state.session_manager import initialize_session_state
from ui.sidebar import sidebar
from ui.github_ui import setup_github_connection
from ui.colab_ui import manage_colab_servers
from ui.file_ui import file_management_ui
from ui.processing_ui import processing_ui
from ui.job_ui import job_monitoring_ui
from practical_colab_solution.integrated_colab_ui import integrated_colab_ui


def main():
    st.set_page_config(
        page_title="Distributed Colab Manager",
        layout="wide",
    )

    setup_logging()
    initialize_session_state()

    sidebar()

    st.title("🚀 Distributed Colab Manager")

    if setup_github_connection():
        integrated_colab_ui()
        manage_colab_servers()
        file_management_ui()
        processing_ui()
        job_monitoring_ui()


if __name__ == "__main__":
    main()
