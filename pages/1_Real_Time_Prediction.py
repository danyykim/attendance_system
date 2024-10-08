import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time

# Initialize the Real-Time Prediction class
st.subheader('Real-Time Attendance System')

with st.spinner('Retrieving Data from Redis DB ...'):
    redis_face_db = face_rec.retrive_data(name='academy:register')

st.success("Data successfully retrieved from Redis")

# Set the time for log-saving intervals
waitTime = 10  # Time interval in seconds
setTime = time.time()
realtimepred = face_rec.RealTimePred()

# Callback function for WebRTC
def video_frame_callback(frame):
    global setTime

    img = frame.to_ndarray(format="bgr24")
    pred_img = realtimepred.face_prediction(img, redis_face_db, 'facial_features', ['Name', 'Role'], thresh=0.5)

    # Check time difference to trigger log save
    timenow = time.time()
    difftime = timenow - setTime
    if difftime >= waitTime:
        save_success = realtimepred.saveLogs_redis()
        setTime = time.time()  # Reset time

        if save_success:
            st.session_state['data_saved'] = True  # Save to session state
            st.rerun()  # Rerun the page to trigger redirection

    return av.VideoFrame.from_ndarray(pred_img, format="bgr24")


webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback,
                rtc_configuration={
                    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                })

# Check session state and redirect if necessary
if st.session_state.get('data_saved', False):
    st.success("Data saved successfully!")
    time.sleep(2)  # Optional: Pause for a brief moment
    st.session_state['data_saved'] = False  # Reset state for next save
    st.experimental_set_query_params(page='success')  # Simulate redirection to Success.py
