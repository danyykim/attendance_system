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

# Time settings
waitTime = 10  # time in sec
setTime = time.time()
realtimepred = face_rec.RealTimePred()  # Real-time prediction class

# Flag to check if logs were saved
logs_saved = False

# Streamlit webrtc
# Callback function
def video_frame_callback(frame):
    global setTime, logs_saved
    
    img = frame.to_ndarray(format="bgr24")  # 3D numpy array
    pred_img = realtimepred.face_prediction(img, redis_face_db, 'facial_features', ['Name', 'Role'], thresh=0.5)
    
    timenow = time.time()
    difftime = timenow - setTime

    if difftime >= waitTime:
        realtimepred.saveLogs_redis()
        setTime = time.time()  # Reset time    
        logs_saved = True  # Set flag to True
        print('Save Data to Redis database')

    return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback,
                rtc_configuration={
                    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                })

st.subheader("Prediction Results")

# Display success message if logs were saved
if logs_saved:
    st.success("Success: Face successfully scanned and logged!")
