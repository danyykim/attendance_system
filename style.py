import streamlit as st
# style.py
def apply_background_style():
    st.markdown(
        """
        <style>
        .reportview-container {
            background: linear-gradient(to bottom, #FF6A00, #FFB700); /* Adjust colors */
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
