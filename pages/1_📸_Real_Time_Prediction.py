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
             # Trigger success in column 2
            st.write('Save Data to redis database')
        return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

    # Streamlit WebRTC streamer
    webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback, rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    })

# Column 2: Success Message
with col2:
    st.subheader('Status')
    if st.session_state.get('success'):
        st.success("Data has been successfully saved!")
    else:
        st.info("Waiting for recognition...")
