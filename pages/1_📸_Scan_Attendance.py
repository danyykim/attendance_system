import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time
import threading

# Threading lock for thread-safe access
lock = threading.Lock()
success_container = {"success": False}  # Shared container

# Set up the layout with buttons
st.subheader('Attendance System')

# Check In and Check Out buttons
col1, col2 = st.columns(2)
with col1:
    check_in = st.button('Check In')

with col2:
    check_out = st.button('Check Out')

# Initialize session state if not already done
if 'show_camera' not in st.session_state:
    st.session_state.show_camera = False

# Set session state on button click
if check_in or check_out:
    st.session_state.show_camera = True

if st.session_state.show_camera:
    # Set up the layout for the camera and status display
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

        return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

    ctx = webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback, rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.services.mozilla.com:3478"]}]
    })

    # Status Update Section
    st.subheader('Status')
    success_placeholder = st.empty()

    while ctx.state.playing:
        with lock:
            if success_container["success"]:
                names = ', '.join(success_container.get("names", []))  # Join names into a string
                success_placeholder.success(f"Data has been successfully saved! Names: {names}")
                time.sleep(5)
                success_placeholder.empty()
                success_container["success"] = False  # Reset after showing message
        time.sleep(1)
