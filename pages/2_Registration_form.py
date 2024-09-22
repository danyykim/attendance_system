import streamlit as st
from Home import face_rec
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer
import av

# st.set_page_config(page_title='Registration Form')
st.subheader('Registration Form')

# Initialize registration form
registration_form = face_rec.RegistrationForm()

# Variable to store the face embedding
face_embedding = None

# Step-1: Collect person name, role, and IC number
with st.form(key='myform', clear_on_submit=True):
    person_name = st.text_input(label='Name', placeholder='First & Last Name')
    role = st.selectbox(label='Select your Role', options=('Student', 'Teacher'))
    ic_number = st.text_input(label='IC Number', placeholder='Enter your 12-digit IC Number')

    # Validate IC number only if the form is submitted
    submit_button = st.form_submit_button(label='Submit')

# Step-2: Collect facial embedding of that person using WebRTC
def video_callback_func(frame):
    global face_embedding
    img = frame.to_ndarray(format='bgr24')  # 3D array in BGR format
    reg_img, embedding = registration_form.get_embedding(img)

    # If a valid face embedding is found, store it
    if embedding is not None:
        face_embedding = embedding

    return av.VideoFrame.from_ndarray(reg_img, format='bgr24')

webrtc_streamer(key='registration', video_frame_callback=video_callback_func,
                rtc_configuration={
                    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                })

# Step-3: Save the data in Redis database only if all validations pass
if submit_button:
    # Check if name, role, and IC number are valid
    if person_name and role and len(ic_number) == 12 and ic_number.isdigit():
        # Ensure face embedding is captured before allowing registration
        if face_embedding is not None:
            # Save embedding data to a file (optional)
            with open('face_embedding.txt', mode='ab') as f:
                np.savetxt(f, face_embedding)

            # Save the data in Redis
            return_val = registration_form.save_data_in_redis_db(person_name, role, ic_number)
            if return_val == True:
                st.success(f"{person_name} registered successfully")
            elif return_val == 'name_false':
                st.error('Please enter a valid name: Name cannot be empty or spaces.')
            elif return_val == 'file_false':
                st.error('face_embedding.txt is not found. Please refresh the page and try again.')
        else:
            st.error("Face embedding not captured. Please ensure your face is scanned before submitting.")
    else:
        st.error("Please ensure all fields are filled correctly. IC Number must be exactly 12 digits.")
