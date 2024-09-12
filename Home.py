import streamlit as st



st.set_page_config(page_title='Face Recognition System',layout='wide')

st.header('Attendance System using Face Recognition')

with st.spinner("Loading Models and Connecting to Redis db ..."):
    import face_rec
    
st.success('Model loaded sucesfully')
st.success('Redis db sucessfully connected')
