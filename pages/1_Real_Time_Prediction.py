import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time

# Subheader for the Real-Time Attendance System
st.subheader('Real-Time Attendance System')

# Retrieving Data from Redis Database
with st.spinner('Retrieving Data from Redis DB...'):
    redis_face_db = face_rec.retrive_data(name='academy:register')
st.success("Data successfully retrieved from Redis")

# Initialize time variables
waitTime = 10  # Interval in seconds to save logs and show success
setTime = time.time()
realtimepred = face_rec.RealTimePred()  # Real-time prediction class

# Variables to track success and errors
last_success_time = None

# Video callback function for real-time prediction
def video_frame_callback(frame):
    global setTime, last_success_time
    
    img = frame.to_ndarray(format="bgr24")  # 3D numpy array
    pred_img, person_detected = realtimepred.face_prediction(img, redis_face_db, 'facial_features', ['Name', 'Role'], thresh=0.5)
    
    # Track time for sending logs
    timenow = time.time()
    difftime = timenow - setTime
    
    # Every 10 seconds, save logs to Redis
    if difftime >= waitTime:
        realtimepred.saveLogs_redis()
        setTime = time.time()  # Reset timer
        
        # Show success message every 10 seconds
        last_success_time = time.time()
        st.success("Data successfully saved to logs!")
        print('Save Data to Redis database')

    # If an unknown person is detected, show error message
    if person_detected == 'unknown':
        st.error("Unknown person detected!")
    
    return av.VideoFrame.from_ndarray(pred_img, format="bgr24")


# Streamlit WebRTC streamer for real-time video
webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback,
                rtc_configuration={
                    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                })

# Automatically trigger every 10 seconds to simulate button click
def auto_trigger_logs():
    timenow = time.time()
    if last_success_time is not None and (timenow - last_success_time) >= waitTime:
        st.rerun()  # Rerun to trigger the logic

# Call the function to check every 10 seconds
auto_trigger_logs()

st.subheader("Prediction Results")
