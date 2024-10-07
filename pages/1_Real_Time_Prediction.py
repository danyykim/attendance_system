import streamlit as st
from Home import face_rec
import time

st.subheader('Real-Time Attendance System')

# Retrieve data from Redis Database
with st.spinner('Retrieving Data from Redis DB...'):
    redis_face_db = face_rec.retrive_data(name='academy:register')
    
st.success("Data successfully retrieved from Redis")

# Initialize a class instance for Real-Time Prediction
realtimepred = face_rec.RealTimePred()

# Set session state to store logs status
if 'logs_saved' not in st.session_state:
    st.session_state['logs_saved'] = False

# Set time for log checking
waitTime = 10  # seconds
setTime = time.time()

# Real Time Prediction
# streamlit webrtc
from streamlit_webrtc import webrtc_streamer
import av

def video_frame_callback(frame):
    global setTime

    img = frame.to_ndarray(format="bgr24")  # 3D numpy array
    # Apply prediction on the frame
    pred_img = realtimepred.face_prediction(img, redis_face_db, 'facial_features', ['Name', 'Role'], thresh=0.5)

    # Check for wait time and save logs
    timenow = time.time()
    difftime = timenow - setTime
    if difftime >= waitTime:
        realtimepred.saveLogs_redis()
        st.session_state['logs_saved'] = True
        setTime = time.time()  # reset time    

    return av.VideoFrame.from_ndarray(pred_img, format="bgr24")


webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback,
                rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    })

# Prediction Results Header
st.subheader("Prediction Results")

# Display success message if new logs are saved
if st.session_state['logs_saved']:
    st.success("Success: New face data has been successfully logged!")
else:
    st.warning("No new data found in logs.")
