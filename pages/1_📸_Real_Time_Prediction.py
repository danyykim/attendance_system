import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time
import queue
import threading

# Threading lock for thread-safe access
lock = threading.Lock()
success_container = {"success": False, "names": [], "scanned_count": 0 }  # Shared container

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
            logged_names = realtimepred.saveLogs_redis()
            setTime = time.time()  # Reset time
            
            # Thread-safe access
            with lock:
                success_container["success"] = True
                success_container["names"] = logged_names
                success_container["scanned_count"] += len(logged_names)  # Increment the scanned count

        return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

    ctx = webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback, rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.services.mozilla.com:3478"]}]
    })

# Column 2: Status Update
with col2:
    st.subheader('Status')
    success_placeholder = st.empty()

    while ctx.state.playing:
        with lock:
            if success_container["success"]:
                names = ', '.join(success_container.get("names", []))  # Join names into a string
                count = success_container["scanned_count"]
                success_placeholder.success(f"Data has been successfully saved! Names: {names}")
                time.sleep(5)
                success_placeholder.empty()
                success_container["success"] = False  # Reset after showing message
        time.sleep(1)
