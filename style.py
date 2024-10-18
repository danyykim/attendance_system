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

        /* Ensure st.success, st.info, st.warning retain their backgrounds */
        .stAlert {
            background-color: rgba(255, 255, 255, 0.9); /* Slightly opaque white background */
            border-radius: 10px; /* Rounded corners for better aesthetics */
        }

        /* Specific styles for success message */
        .stAlert[data-baseweb="alert-success"] {
            background-color: #D4EDDA !important;
            color: #155724 !important;
        }

        /* Specific styles for info message */
        .stAlert[data-baseweb="alert-info"] {
            background-color: #CCE5FF !important;
            color: #004085 !important;
        }

        /* Specific styles for warning message */
        .stAlert[data-baseweb="alert-warning"] {
            background-color: #FFF3CD !important;
            color: #856404 !important;
        }

        /* Specific styles for error message */
        .stAlert[data-baseweb="alert-error"] {
            background-color: #F8D7DA !important;
            color: #721C24 !important;
        }
        </style>
        """, unsafe_allow_html=True
    )

# Call this function at the top of your page to apply the styles
add_custom_css()

      

