import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time

# Initialize session state for log count and message if not already done
if 'previous_log_count' not in st.session_state:
    st.session_state.previous_log_count = 0
if 'success_message' not in st.session_state:
    st.session_state.success_message = "Waiting for recognition..."

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

    # Real-time video frame callback
    def video_frame_callback(frame):
        global setTime

        img = frame.to_ndarray(format="bgr24")  # Process video frame
        pred_img = realtimepred.face_prediction(
            img, redis_face_db, 'facial_features', ['Name', 'Role'], thresh=0.5
        )

        timenow = time.time()
        difftime = timenow - setTime

        # Check if 10 seconds have passed
        if difftime >= waitTime:
            realtimepred.saveLogs_redis()
            setTime = time.time()  # Reset time
            
            current_log_count = len(face_rec.r.lrange('attendance:logs', 0, -1))
            print(f"Current log count: {current_log_count}, Previous log count: {st.session_state.previous_log_count}")
            # Check if new logs are added
            if current_log_count > st.session_state.previous_log_count:
                st.session_state.success_message = "New logs added!"  # Update success message
            else:
                st.session_state.success_message = "No new logs."
            
            st.session_state.previous_log_count = current_log_count
            print('Save Data to Redis database')
        return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

    # Streamlit WebRTC streamer
    webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback, rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    })

# Column 2: Success Message
with col2:
    st.subheader('Status')
    st.info(st.session_state.success_message)
