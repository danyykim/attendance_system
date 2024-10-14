import pickle
from pathlib import Path
import streamlit as st
import streamlit_authenticator as stauth
import face_rec

st.set_page_config(page_title='Attendance System', layout='wide')

st.markdown(
    """
    <style>
    body {
        background-color: #BF4E9C;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# User authentication
names = ["Danieal"]
usernames = ["nyel"]

# Load hashed passwords
file_path = Path("hashed_pw.pkl")
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

authenticator = stauth.Authenticate(names, usernames, hashed_passwords, "home_dashboard", "abcdef", cookie_expiry_days=30)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status == False:
    st.error("Username/password is incorrect")
elif authentication_status == None:
    st.warning("Please enter your username and password")
else:
    authenticator.logout("Logout", "sidebar")
    st.header(f"Welcome {name}")
    st.header('Attendance System using Face Recognition')

    # Add navigation links to the sidebar
    with st.spinner("Loading Models and Connecting to Redis db ..."):
        st.success('Model loaded successfully')
        st.success('Redis db successfully connected')
        
