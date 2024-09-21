import streamlit as st
from Home import face_rec
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer
import av


# st.set_page_config(page_title='Registration Form')
st.subheader('Registration Form')

## init registration form
registration_form = face_rec.RegistrationForm()

if 'person_name' not in st.session_state:
    st.session_state.person_name = ''
if 'role' not in st.session_state:
    st.session_state.role = 'Student'
if 'ic_number' not in st.session_state:
    st.session_state.ic_number = ''

# Step-1: Collect person name and role
# form
person_name = st.text_input(label='Name', placeholder='First & Last Name', value=st.session_state.person_name)
role = st.selectbox(label='Select your Role', options=('Student', 'Teacher'), index=0 if st.session_state.role == 'Student' else 1)
ic_number = st.text_input(label='IC Number', placeholder='Enter your 12-digit IC Number', value=st.session_state.ic_number)

# Validate IC number
if len(str(ic_number)) != 12:
    st.error("IC Number must be exactly 12 digits.")


# step-2: Collect facial embedding of that person
def video_callback_func(frame):
    img = frame.to_ndarray(format='bgr24') # 3d array bgr
    reg_img, embedding = registration_form.get_embedding(img)
    # two step process
    # 1st step save data into local computer txt
    if embedding is not None:
        with open('face_embedding.txt',mode='ab') as f:
            np.savetxt(f,embedding)
    
    return av.VideoFrame.from_ndarray(reg_img,format='bgr24')

webrtc_streamer(key='registration',video_frame_callback=video_callback_func,
rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    })


# step-3: save the data in redis database
        
if st.button('Submit'):
    if person_name and role and ic_number and len(ic_number) == 12 and ic_number.isdigit():
        return_val = registration_form.save_data_in_redis_db(person_name, role, ic_number)
        if return_val == True:
            st.success(f"{person_name} registered successfully")
           #reset
            st.session_state.person_name = ''
            st.session_state.role = 'Student'
            st.session_state.ic_number = ''
            st.experimental_rerun()
        elif return_val == 'name_false':
            st.error('Please enter the name: Name cannot be empty or spaces')
        elif return_val == 'file_false':
            st.error('face_embedding.txt is not found. Please refresh the page and execute again.')
    else:
        st.error("Please fill all required fields correctly.")