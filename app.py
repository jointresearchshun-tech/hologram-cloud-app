import sys, os
sys.path.append(os.path.dirname(__file__))

import streamlit as st
from config.logging_config import setup_logging
from ui.github_ui import github_connect_ui
from practical_colab_solution.integrated_colab_ui import integrated_colab_ui

logger = setup_logging()

def main():
    st.set_page_config(page_title="Cloud Hologram Processing System", layout="wide")
    st.title("🌐 Cloud Hologram Processing System")

    # ✅ 自動で GitHub 接続を試みる
    with st.spinner("Connecting to GitHub..."):
        github_connect_ui(auto_connect=True)  # ← オプションを付けて自動化

    # Colab UI
    integrated_colab_ui()

if __name__ == "__main__":
    main()
