import streamlit as st
# style.py
# style.py


def add_custom_css():
    st.markdown(
        """
        <style>
        /* Set the background for the main app */
        .stApp {
            background: rgb(45,189,253);
            background: linear-gradient(0deg, rgba(45,189,253,1) 0%, rgba(228,0,166,1) 100%);
            color: white; /* Adjust text color */
        }
        .stAlert {
            background-color: rgba(255, 255, 255, 0.85) !important;
            border-radius: 10px !important;
        }
        .stSuccess {
            background-color: rgba(220, 255, 220, 0.85) !important;
            color: green !important;
        }
        .stInfo {
            background-color: rgba(220, 240, 255, 0.85) !important;
            color: blue !important;
        }
        </style>
        """, unsafe_allow_html=True
    )

# Call this function at the top of your page to apply the styles
add_custom_css()

      

