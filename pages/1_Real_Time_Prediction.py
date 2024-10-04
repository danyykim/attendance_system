import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time

# Authentication check
if not st.session_state.get("authentication_status", False):
    st.warning("You must log in first.")
    st.stop()

# Subheader
st.subheader('Real-Time Attendance System')

# Placeholder for showing success messages
attendance_placeholder = st.empty()

# Retrieve the data from Redis Database
with st.spinner('Retrieving Data from Redis DB ...'):
    redis_face_db = face_rec.retrive_data(name='academy:register')

st.success("Data successfully retrieved from Redis")

# Time settings
waitTime = 30  # Time in seconds
setTime = time.time()
realtimepred = face_rec.RealTimePred()  # Real-time prediction class

# Keep track of already recognized attendees to avoid duplicate messages
recognized_attendees = set()

# Real-Time Prediction
def video_frame_callback(frame):
    global setTime
    img = frame.to_ndarray(format="bgr24")  # 3D NumPy array
    pred_img = realtimepred.face_prediction(img, redis_face_db,
                                            'facial_features', ['Name', 'Role'], thresh=0.5)

    # Time calculation for saving logs
    timenow = time.time()
    difftime = timenow - setTime

    if difftime >= waitTime:
        # Get attendees from the face recognition system
        attendees = realtimepred.logs.get('name', [])

        if attendees:
            for attendee in attendees:
                # Check if the attendee has been recognized before
                if attendee not in recognized_attendees:
                    # Show success message immediately after face is recognized
                    attendance_placeholder.success(f"Attendance recorded for: {attendee}")
                    print(f"Attendance recorded for: {attendee}")  # DEBUG
                    recognized_attendees.add(attendee)  # Add to recognized set

            # Save logs to Redis in a separate step (after showing the success message)
            recorded_attendees = realtimepred.saveLogs_redis()
            setTime = time.time()  # Reset time after logs are saved

    return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

# Start the camera stream
webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback,
                rtc_configuration={
                    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}
                ]})
