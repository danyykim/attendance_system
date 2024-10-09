import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time
import queue
import threading

# Threading lock for thread-safe access
lock = threading.Lock()
success_container = {"success": False}  # Shared container

# Set up the layout with two columns
col1, col2 = st.columns(2)

# Column 1: Real-Time Attendance System
with col1:
    st.subheader('Real-Time Attendance System')

    # Retrieve data from Redis
    with st.spinner('Retrieving Data from Redis DB ...'):
        redis_face_db = face_rec.retrive_data(name='academy:register')
    st.success("Data successfully retrieved from Redis")

    waitTime = 10
    setTime = time.time()
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
            realtimepred.saveLogs_redis()
            setTime = time.time()  # Reset time
            
            # Thread-safe access
            with lock:
                success_container["success"] = True

        return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

    ctx = webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback, rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    })

# Column 2: Status Update
with col2:
    st.subheader('Status')
    
    message_displayed = False
    
    while ctx.state.playing:
        with lock:
            if success_container["success"]:
                if not message_displayed:  # Check if info message is displayed
                    st.info("Waiting for recognition...")  # Display info message once
                    message_displayed = True  # Set flag after displaying info
                st.success("Data has been successfully saved!")  # Show success message
                success_container["success"] = False  # Reset after showing success
                time.sleep(10)  # Show the message for 10 seconds
            else:
                if message_displayed:
                    message_displayed = False  # Reset the flag for the next round
                time.sleep(1)  #
