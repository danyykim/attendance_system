import streamlit as st
from Home import face_rec
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer
import av

st.subheader('Registration Form')

# Initialize registration form
registration_form = face_rec.RegistrationForm()

# Step-1: Collect person name and role
person_name = st.text_input(label='Name', placeholder='First & Last Name')
role = st.selectbox(label='Select your Role', options=('Student', 'Teacher'))
ic_number = st.text_input(label='IC Number', placeholder='Enter your 12-digit IC Number')

# Validate IC number
if len(str(ic_number)) != 12:
    st.error("IC Number must be exactly 12 digits.")

# Step-2: Collect facial embedding of that person
def video_callback_func(frame):
    img = frame.to_ndarray(format='bgr24')  # 3D array BGR
    reg_img, embedding = registration_form.get_embedding(img)
    
    # Save data to local computer
    if embedding is not None:
        with open('face_embedding.txt', mode='ab') as f:
            np.savetxt(f, embedding)

    return av.VideoFrame.from_ndarray(reg_img, format='bgr24')

webrtc_streamer(key='registration', video_frame_callback=video_callback_func, rtc_configuration={
    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
})

# Step-3: Save the data in Redis database
if st.button('Submit'):
    if person_name and role and ic_number and len(ic_number) == 12 and ic_number.isdigit():
        return_val = registration_form.save_data_in_redis_db(person_name, role, ic_number)
        if return_val:
            st.success(f"{person_name} registered successfully")
            # Reset input fields
            person_name = ""
            role = ""
            ic_number = ""
        elif return_val == 'name_false':
            st.error('Please enter the name: Name cannot be empty or spaces')
        elif return_val == 'file_false':
            st.error('face_embedding.txt is not found. Please refresh the page and execute again.')
    else:
        st.error("Please fill all required fields correctly.")
