import streamlit as st
# style.py
# style.py
def apply_background_style():
    st.markdown(
        """
        <style>
        .stApp {  
            background: rgb(45,189,253);
            background: linear-gradient(0deg, rgba(45,189,253,1) 0%, rgba(228,0,166,1) 100%);
            color: white;
            height: 100vh;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

