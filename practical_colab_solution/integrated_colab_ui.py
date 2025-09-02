import streamlit as st


def colab_connect_ui(auto_connect: bool = False):
    """
    Google Colab auto-connect UI.
    Reads server info from st.secrets["colab"] and 
    stores connection in session_state.
    """
    st.subheader("🔗 Google Colab Connection")

    # Already connected?
    if "colab_url" in st.session_state:
        st.success(f"✅ Connected to Colab: {st.session_state['colab_url']}")
        return

    if auto_connect:
        try:
            colab_conf = st.secrets["colab"]

            # Take first server in secrets
            server_name = colab_conf.get("server_1_name", "Colab Server")
            server_url = colab_conf.get("server_1_url", "")

            if not server_url:
                st.error("❌ No Colab server URL found in secrets.toml")
                return

            # Save connection into session_state
            st.session_state["colab_url"] = server_url
            st.success(f"✅ Auto-connected to {server_name}: {server_url}")

        except Exception as e:
            st.error(f"❌ Failed to auto-connect to Colab: {e}")
    else:
        st.info("ℹ️ Auto-connect disabled. Enable with `auto_connect=True`.")
