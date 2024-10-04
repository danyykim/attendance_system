import streamlit as st
from Home import face_rec
import numpy as np
from streamlit_webrtc import webrtc_streamer
import av

if not st.session_state.get("authentication_status", False):
    st.warning("You must log in first.")
    st.stop()

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
embedding = None  # Initialize embedding variable outside the function

def video_callback_func(frame):
    global embedding
    img = frame.to_ndarray(format='bgr24')  # 3D array BGR
    reg_img, embedding = registration_form.get_embedding(img)
    
    # Save data to local computer if embedding is available
    if embedding is not None:
        with open('face_embedding.txt', mode='ab') as f:
            np.savetxt(f, embedding)

    return av.VideoFrame.from_ndarray(reg_img, format='bgr24')

# Use webrtc_streamer to scan the face
webrtc_streamer(key='registration', video_frame_callback=video_callback_func, rtc_configuration={
    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
})

# Step-3: Save the data in Redis database upon form submission
if st.button('Submit'):
    # Ensure all required fields are filled, including face embedding
    if person_name and role and ic_number and len(ic_number) == 12 and ic_number.isdigit():
        if embedding is not None:
            # Try saving data in Redis
            return_val = registration_form.save_data_in_redis_db(person_name, role, ic_number)
            
            if return_val:
                st.success(f"{person_name} registered successfully")
            elif return_val == 'name_false':
                st.error('Please enter a valid name: Name cannot be empty or just spaces.')
            elif return_val == 'file_false':
                st.error('face_embedding.txt not found. Please refresh the page and try again.')
        else:
            st.error("Face scan is required. Please ensure the face is scanned properly before submitting.")
    else:
        st.error("Please fill all required fields correctly.")
