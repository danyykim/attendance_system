import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time
from datetime import datetime

# Check authentication status
if not st.session_state.get("authentication_status", False):
    st.warning("You must log in first.")
    st.stop()

st.subheader('Real-Time Attendance System')

# Retrieve the data from Redis Database
with st.spinner('Retrieving Data from Redis DB ...'):
    redis_face_db = face_rec.retrive_data(name='academy:register')
    st.dataframe(redis_face_db)

st.success("Data successfully retrieved from Redis")

# Initialize notification messages in session state
if 'notification' not in st.session_state:
    st.session_state.notification = ""

# Initialize last notification time for rate limiting
if 'last_notification_time' not in st.session_state:
    st.session_state.last_notification_time = 0

# Time setup
waitTime = 30  # time in sec
setTime = time.time()
realtimepred = face_rec.RealTimePred()  # real-time prediction class

# Real Time Prediction
def video_frame_callback(frame):
    global setTime

    img = frame.to_ndarray(format="bgr24")  # 3D numpy array
    # Perform face prediction
    pred_img, notification_message = realtimepred.face_prediction(
        img, redis_face_db, 'facial_features', ['Name', 'Role'], thresh=0.5
    )

    # Update session state with the notification message if it's new
    if notification_message and (time.time() - st.session_state.last_notification_time > 3):  # 3 seconds cooldown
        st.session_state.notification = notification_message
        st.session_state.last_notification_time = time.time()  # Update last notification time

    # Handle saving logs
    timenow = time.time()
    difftime = timenow - setTime
    if difftime >= waitTime:
        realtimepred.saveLogs_redis()
        setTime = time.time()  # reset time        

    return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

# Streamlit WebRTC for real-time video stream
webrtc_streamer(
    key="realtimePrediction",
    video_frame_callback=video_frame_callback,
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    }
)

# Display notification message if exists
if st.session_state.notification:
    st.success(st.session_state.notification)  # Display the notification message below the camera
