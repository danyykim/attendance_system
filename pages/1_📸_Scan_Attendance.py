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

# Initialize session state if not already done
if 'show_camera' not in st.session_state:
    st.session_state.show_camera = False
if 'check_in' not in st.session_state:
    st.session_state.check_in = False
if 'check_out' not in st.session_state:
    st.session_state.check_out = False

# Check In and Check Out buttons
if not st.session_state.check_in and not st.session_state.check_out:
    col1, col2 = st.columns(2)
    with col1:
        if st.button('Check In'):
            st.session_state.check_in = True
            st.session_state.show_camera = True
            st.session_state.check_out = False
    with col2:
        if st.button('Check Out'):
            st.session_state.check_out = True
            st.session_state.show_camera = True
            st.session_state.check_in = False

if st.session_state.show_camera:
    
    # Set up the layout for the camera and status display
    
    if st.button('Back'):
        st.session_state.show_camera = False
        st.session_state.check_in = False
        st.session_state.check_out = False
        st.rerun()

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
            logged_names, unknown_count = realtimepred.saveLogs_redis()
            setTime = time.time()  # Reset time
            
            # Thread-safe access
            with lock:
                success_container["success"] = True
                success_container["names"] = logged_names
                success_container["unknown_count"]  = unknown_count

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
                names = ', '.join(success_container.get("names", []))  # Join recognized names into a string
                unknown_count = success_container.get("unknown_count", 0)  # Get unknown person count
                success_message = f"Data has been successfully saved! Names: {names}"
                if unknown_count > 0:
                    success_message += f" | Unknown Persons Detected: {unknown_count}"

                success_placeholder.success(success_message)
                time.sleep(5)
                success_placeholder.empty()
                success_container["success"] = False  # Reset after showing message
        time.sleep(1)
