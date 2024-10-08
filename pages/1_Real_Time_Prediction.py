import streamlit as st 
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time

# Initialize session state to store the log-saving status
if "log_saved" not in st.session_state:
    st.session_state["log_saved"] = False

# Subheader
st.subheader('Real-Time Attendance System')

# Retrieve the data from Redis Database
with st.spinner('Retrieving Data from Redis DB...'):    
    redis_face_db = face_rec.retrive_data(name='academy:register')

st.success("Data successfully retrieved from Redis")

# Time
waitTime = 10  # time in sec
setTime = time.time()
realtimepred = face_rec.RealTimePred()  # real time prediction class

# Real Time Prediction
# streamlit webrtc
# callback function
def video_frame_callback(frame):
    global setTime

    img = frame.to_ndarray(format="bgr24")  # 3 dimension numpy array
    # Perform face prediction
    pred_img = realtimepred.face_prediction(img, redis_face_db, 'facial_features', ['Name', 'Role'], thresh=0.5)

    timenow = time.time()
    difftime = timenow - setTime
    if difftime >= waitTime:
        realtimepred.saveLogs_redis()
        setTime = time.time()  # reset time
        st.session_state["log_saved"] = True  # Indicate logs saved

    return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

# Start the video stream
webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback,
                rtc_configuration={
                    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                })

# Show success message once logs are saved
if st.session_state["log_saved"]:
    st.success("Logs successfully saved to Redis!")

st.subheader("Prediction Results")
