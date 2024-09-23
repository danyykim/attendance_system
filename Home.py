import pickle
from pathlib import Path

import streamlit as st
import streamlit_authenticator as stauth


st.set_page_config(page_title='Attendance System',layout='wide')

#user-authentication
names = ["Danieal"]
usernames = ["nyel"]

#load hash password
#file_path = Path(__file__).parent / "hashed_pw.pkl"
file_path = Path("/var/www/html/attendance_system/hashed_pw.pkl")

with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)
    
authenticator = stauth.Authenticate(names, usernames, hashed_passwords, "home_dashboard", "abcdef", cookie_expiry_days=30)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status == False:
  st.error("Username/password is incorrect")
  
if authentication_status == None:
  st.warning("Please enter your username and password")

if authentication_status:

    authenticator.logout("Logout", "sidebar")
    st._main.header(f"Welcome {name}")
    st.header('Attendance System using Face Recognition')

    with st.spinner("Loading Models and Connecting to Redis db ..."):
        from . import face_rec
            
        st.success('Model loaded sucesfully')
        st.success('Redis db sucessfully connected')
