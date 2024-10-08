import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time

# Subheader for the Real-Time Attendance System
st.subheader('Real-Time Attendance System')

# CSS to hide the button
hide_button_css = """
    <style>
    #autoButton {
        display: none;
    }
    </style>
"""
st.markdown(hide_button_css, unsafe_allow_html=True)

# JavaScript to auto-click the button after 10 seconds
auto_click_js = """
    <script>
    function simulateClick() {
        document.getElementById("autoButton").click();
    }
    setTimeout(simulateClick, 10000);  // 10 seconds
    </script>
"""
st.markdown(auto_click_js, unsafe_allow_html=True)

# Hidden button to save logs (will be clicked automatically)
if st.button("Save Logs", key="autoButton"):
    st.success("Logs saved automatically after 10 seconds!")

# Retrieving Data from Redis Database
with st.spinner('Retrieving Data from Redis DB...'):
    redis_face_db = face_rec.retrive_data(name='academy:register')

st.success("Data successfully retrieved from Redis")

# Time-related setup
waitTime = 10  # time in sec
setTime = time.time()
realtimepred = face_rec.RealTimePred()  # real-time prediction class

# Video callback function for real-time prediction
def video_frame_callback(frame):
    global setTime

    img = frame.to_ndarray(format="bgr24")  # 3D numpy array
    pred_img = realtimepred.face_prediction(img, redis_face_db, 'facial_features', ['Name', 'Role'], thresh=0.5)

    timenow = time.time()
    difftime = timenow - setTime
    if difftime >= waitTime:
        realtimepred.saveLogs_redis()
        setTime = time.time()  # reset time
        print('Save Data to Redis database')

    return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

# Streamlit WebRTC streamer for real-time video
webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback,
                rtc_configuration={
                    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                })

st.subheader("Prediction Results")
