# utils.py (Create this file to store the utility functions)
import streamlit as st

def set_page_background():
    page_bg_color = """
        <style>
        body {
            background: rgb(40,169,218);
            background: linear-gradient(0deg, rgba(40,169,218,1) 0%, rgba(246,13,218,1) 100%);
        }
        .stApp {
            background: rgb(40,169,218);
            background: linear-gradient(0deg, rgba(40,169,218,1) 0%, rgba(246,13,218,1) 100%);
        }
        </style>
    """
    st.markdown(page_bg_color, unsafe_allow_html=True)
