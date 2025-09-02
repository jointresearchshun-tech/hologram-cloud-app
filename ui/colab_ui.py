import streamlit as st

def manage_colab_servers():
    st.subheader("⚙️ Colab Server Management (manual)")

    if "colab_servers" not in st.session_state:
        st.session_state["colab_servers"] = []

    new_name = st.text_input("Server Name")
    new_url = st.text_input("Server URL (e.g. https://xxxx.ngrok.io)")

    if st.button("Add Server"):
        if new_name and new_url:
            st.session_state["colab_servers"].append({"name": new_name, "url": new_url})
            st.success(f"Added server: {new_name}")
        else:
            st.warning("Please provide both name and URL.")

    if st.session_state["colab_servers"]:
        st.write("Registered Servers:")
        for server in st.session_state["colab_servers"]:
            st.write(f"- {server['name']}: {server['url']}")
