import streamlit as st
# style.py
# style.py
def apply_background_style():
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(to bottom, #FF6A00, #FFB700); /* Adjust colors */
            color: white;
            height: 100vh;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

