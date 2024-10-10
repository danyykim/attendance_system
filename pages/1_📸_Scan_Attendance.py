import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time
import threading

# Threading lock for thread-safe access
lock = threading.Lock()
success_container = {"success": False}  # Shared container

# Set up the layout with two columns for buttons
st.subheader('Attendance System')

col1, col2 = st.columns(2)

# Check In button
with col1:
    if st.button('Check In'):
        # Logic for starting the camera and check-in
        st.session_state.check_in = True

# Check Out button
with col2:
    if st.button('Check Out'):
        # Logic for starting the camera and check-out
        st.session_state.check_out = True

# Initialize the camera only if either button is clicked
if 'check_in' in st.session_state or 'check_out' in st.session_state:
    waitTime = 10
    setTime = time.time()
    redis_face_db = face_rec.retrive_data(name='academy:register')
    realtimepred = face_rec.RealTimePred()

    def video_frame_callback(frame):
        global setTime
        img = frame.to_ndarray(format="bgr24")
        pred_img = realtimepred.face_prediction(
            img, redis_face_db, 'facial_features', ['Name', 'Role'], thresh=0.5
        )
        
        timenow = time.time()
        difftime = timenow - setTime

        if difftime >= waitTime:
            logged_names = realtimepred.saveLogs_redis()
            setTime = time.time()  # Reset time
            
            # Thread-safe access
            with lock:
                success_container["success"] = True
                success_container["names"] = logged_names

        return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

    ctx = webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback, rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.services.mozilla.com:3478"]}]
    })

# Status Update Section
st.subheader('Status')
success_placeholder = st.empty()

while 'check_in' in st.session_state or 'check_out' in st.session_state:
    with lock:
        if success_container["success"]:
            names = ', '.join(success_container.get("names", []))  # Join names into a string
            success_placeholder.success(f"Data has been successfully saved! Names: {names}")
            time.sleep(5)
            success_placeholder.empty()
            success_container["success"] = False  # Reset after showing message
    time.sleep(1)
