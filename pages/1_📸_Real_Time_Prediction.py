import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time

# Set up the layout with two columns
col1, col2 = st.columns(2)

# Column 1: Real-Time Attendance System
with col1:
    st.subheader('Real-Time Attendance System')

    # Retrieve data from Redis
    with st.spinner('Retrieving Data from Redis DB ...'):
        redis_face_db = face_rec.retrive_data(name='academy:register')
    st.success("Data successfully retrieved from Redis")

    # Initialize prediction class
    realtimepred = face_rec.RealTimePred()

    # Real-time video frame callback
    def video_frame_callback(frame):
        img = frame.to_ndarray(format="bgr24")  # Process video frame
        pred_img = realtimepred.face_prediction(
            img, redis_face_db, 'facial_features', ['Name', 'Role'], thresh=0.5
        )
        return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

    # Streamlit WebRTC streamer
    webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback, rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    })

# Check logs and set success message
if realtimepred.logs['name']:  # Check if there are any logs
    realtimepred.saveLogs_redis()  # Save to Redis
    st.session_state.success = True  # Update success flag
else:
    st.session_state.success = False  # Reset success flag

# Column 2: Success Message
with col2:
    st.subheader('Status')
    if st.session_state.get('success'):
        st.success("Data has been successfully saved!")
    else:
        st.info("Waiting for recognition...")
