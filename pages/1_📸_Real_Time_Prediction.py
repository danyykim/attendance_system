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

    # Set wait time and initialize prediction class
    waitTime = 10
    setTime = time.time()
    realtimepred = face_rec.RealTimePred()

    # Initialize previous log count
    previous_log_count = 0

    # Real-time video frame callback
    def video_frame_callback(frame):
        global setTime, previous_log_count

        img = frame.to_ndarray(format="bgr24")  # Process video frame
        pred_img = realtimepred.face_prediction(
            img, redis_face_db, 'facial_features', ['Name', 'Role'], thresh=0.5
        )

        timenow = time.time()
        difftime = timenow - setTime

        # Check if 10 seconds have passed
        if difftime >= waitTime:
            current_count = realtimepred.get_current_log_count()  # Get current log count
            
            if current_count > previous_log_count:  # Only save if new logs are detected
                realtimepred.saveLogs_redis()
                previous_log_count = current_count  # Update previous log count
                print('Save Data to Redis database')
            setTime = time.time()  # Reset time

        return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

    # Streamlit WebRTC streamer
    webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback, rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    })

# Column 2: Success Message
with col2:
    st.subheader('Status')

    if st.session_state.get("camera_running", False):  # Check if the camera is running
        current_count = realtimepred.get_current_log_count()  # Get current log count

        # Check if the current count has increased
        if current_count > previous_log_count:
            st.success("Data has been successfully saved!")
        else:
            st.info("Waiting for recognition...")
    else:
        st.info("Camera is not yet started.")
