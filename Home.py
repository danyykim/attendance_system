import streamlit as st
import streamlit_authenticator as stauth


st.set_page_config(page_title='Attendance System',layout='wide')

st.header('Attendance System using Face Recognition')

with st.spinner("Loading Models and Connecting to Redis db ..."):
    import face_rec
        
    st.success('Model loaded sucesfully')
    st.success('Redis db sucessfully connected')
