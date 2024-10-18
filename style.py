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
        /* Ensure that success, info, and warning messages are not transparent */
        .stAlert {
            background-color: rgba(255, 255, 255, 0.9);  /* Set background to white with slight transparency */
            border-radius: 10px;  /* Optional: Adds rounded corners */
            color: black;  /* Text color */
            padding: 10px; /* Adds some padding */
        }
        </style>
        """, unsafe_allow_html=True
    )

# Call this function at the top of your page to apply the styles
add_custom_css()

      

