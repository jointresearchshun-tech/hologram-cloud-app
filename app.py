import streamlit as st
from config.logging_config import setup_logging

def main():
    setup_logging()
    st.write("Hello with logging_config import")

if __name__ == "__main__":
    main()
