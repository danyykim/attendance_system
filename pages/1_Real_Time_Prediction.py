import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time

st.subheader('Real-Time Attendance System')

# Retrieve the data from Redis Database
with st.spinner('Retrieving Data from Redis DB...'):
    redis_face_db = face_rec.retrive_data(name='academy:register')

st.success("Data successfully retrieved from Redis")

# Variables to track success state
waitTime = 10 # time in sec
setTime = time.time()
realtimepred = face_rec.RealTimePred()

# Add session state for logs_saved flag
if 'logs_saved' not in st.session_state:
    st.session_state['logs_saved'] = False

# Real Time Prediction
def video_frame_callback(frame):
    global setTime

    img = frame.to_ndarray(format="bgr24")  # 3 dimension numpy array
    pred_img = realtimepred.face_prediction(img, redis_face_db,
                                            'facial_features', ['Name', 'Role'], thresh=0.5)

    timenow = time.time()
    difftime = timenow - setTime

    if difftime >= waitTime:
        realtimepred.saveLogs_redis()  # Save logs
        st.session_state['logs_saved'] = True  # Set flag to True after saving logs
        setTime = time.time()  # Reset time

    return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

# WebRTC streamer
webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback,
                rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})

# Display success message outside of callback
st.subheader("Prediction Results")
if st.session_state['logs_saved']:
    st.success("Success: Face successfully scanned and logged!")
    st.session_state['logs_saved'] = False  # Reset the flag for the next event
