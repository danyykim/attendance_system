import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time

st.subheader('Real-Time Attendance System')

# Retrieve the data from Redis Database
with st.spinner('Retrieving Data from Redis DB ...'):
    redis_face_db = face_rec.retrive_data(name='academy:register')

st.success("Data successfully retrieved from Redis")

# Time configuration
waitTime = 10  # Time in seconds
setTime = time.time()
realtimepred = face_rec.RealTimePred()  # Real-time prediction class

# Callback function for video frame processing
def video_frame_callback(frame):
    global setTime
    
    img = frame.to_ndarray(format="bgr24")  # 3D array BGR
    # Perform face prediction
    pred_img = realtimepred.face_prediction(img, redis_face_db, 
                                            'facial_features', ['Name', 'Role'], thresh=0.5)

    timenow = time.time()
    difftime = timenow - setTime
    if difftime >= waitTime:
        save_success = realtimepred.saveLogs_redis()  # Save logs to Redis
        setTime = time.time()  # Reset time
        
        if save_success:
            st.session_state['data_saved'] = True  # Set session state variable
            st.rerun()  # Rerun the app to update the page

    return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

# WebRTC stream
webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback,
                rtc_configuration={
                    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}
                ]
                })

st.subheader("Prediction Results")
