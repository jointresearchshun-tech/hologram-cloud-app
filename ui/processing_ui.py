import streamlit as st
from services.model_service import load_model_from_pth, decompress_file

def processing_ui():
    st.subheader("🛠 File Processing")

    github_client = st.session_state.get("github_client")
    if not github_client:
        st.warning("⚠️ Please connect to GitHub first.")
        return

    # List files in DATA/
    files = github_client.list_files("DATA")
    model_files = [f for f in files if f.endswith(".pth")]
    compressed_files = [f for f in files if f.endswith(".pt")]

    if not model_files or not compressed_files:
        st.info("Upload .pth model and .pt compressed data into DATA/ first.")
        return

    model_file = st.selectbox("Select Model (.pth)", model_files)
    compressed_file = st.selectbox("Select Compressed File (.pt)", compressed_files)

    if st.button("Run Decompression"):
        try:
            # Load model
            model_bytes = github_client.download_file(model_file)
            model = load_model_from_pth(model_bytes)

            # Download compressed
            compressed_bytes = github_client.download_file(compressed_file)

            # Decompress
            output_name = compressed_file.replace(".pt", "_decompressed.pt")
            output_path = f"DATA/{output_name}"
            saved_path = decompress_file(model, compressed_bytes, output_path, github_client)

            st.success(f"✅ Decompressed and saved as {saved_path}")

        except Exception as e:
            st.error(f"Decompression failed: {e}")
