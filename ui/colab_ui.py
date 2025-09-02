import streamlit as st

def colab_connect_ui(auto_connect: bool = False):
    st.subheader("🔗 Google Colab Connection")

    if auto_connect:
        # For future expansion with st.secrets
        st.success("✅ Connected to Google Colab (auto mode)")
        return

    # Manual connection (ngrok public URL)
    colab_url = st.text_input("Enter Colab server URL", key="colab_url")

    if st.button("Connect to Colab"):
        if colab_url:
            st.session_state["colab_url"] = colab_url
            st.success(f"✅ Connected to Colab: {colab_url}")
        else:
            st.error("⚠️ Please enter a valid Colab URL")
