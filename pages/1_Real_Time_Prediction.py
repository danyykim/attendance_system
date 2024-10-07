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
realtimepred = face_rec.RealTimePred()  # real-time prediction class
success_message = None  # Initialize a variable to hold success message

# Streamlit webrtc
# Callback function
def video_frame_callback(frame):
    global setTime, success_message
    
    img = frame.to_ndarray(format="bgr24")  # 3D numpy array
    pred_img = realtimepred.face_prediction(img, redis_face_db, 'facial_features', ['Name', 'Role'], thresh=0.5)
    
    timenow = time.time()
    difftime = timenow - setTime
    
    # Only check for logging after the wait time
    if difftime >= waitTime:
        setTime = time.time()  # Reset time

        # Check if there are new logs to save
        if realtimepred.logs['name']:  
            if realtimepred.saveLogs_redis():  # Save logs
                success_message = "Success: Face successfully scanned and logged!"  # Set success message
        else:
            success_message = "No new logs to save."  # Warning message if no new logs

    return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback,
                rtc_configuration={
                    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                })

st.subheader("Prediction Results")

# Display the success message
if success_message:
    st.success(success_message)  # Show success message
