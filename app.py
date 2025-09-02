import streamlit as st
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
page_title="☁️ Cloud Hologram Processing System",
page_icon="🔬",
layout="wide",
initial_sidebar_state="expanded",
)


st.title("☁️ Fully Cloud-Based Hologram Processing")
st.markdown("**Zero local compute – everything runs in the cloud**")


# Sidebar & system status
sidebar()


# GitHub connection (auto via secrets + manual fallback)
github_connected = setup_github_connection()


# Colab server setup
# 1) Manual management UI (keep)
manage_colab_servers()
# 2) Auto connect UI (secrets-based)
integrated_colab_ui()


st.divider()


if github_connected:
# File management (upload/list/download via GitHub)
file_management_ui()


st.divider()


# Processing (submit jobs to current Colab server)
processing_ui()


# Job monitoring (poll status, cancel, archive)
job_monitoring_ui()




if __name__ == "__main__":
initialize_session_state()
main()
