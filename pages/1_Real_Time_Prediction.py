import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time

# Check if the user is authenticated
if not st.session_state.get("authentication_status", False):
    st.warning("You must log in first.")
    st.stop()

# Set up the page UI
st.subheader('Real-Time Attendance System')

# Placeholder for attendance message
attendance_placeholder = st.empty()  # Create a placeholder for dynamic updates

# Retrieve data from Redis Database
with st.spinner('Retrieving Data from Redis DB ...'):
    redis_face_db = face_rec.retrive_data(name='academy:register')

st.success("Data successfully retrieved from Redis")

# Time settings
waitTime = 30  # Time in seconds
setTime = time.time()
realtimepred = face_rec.RealTimePred()  # Real-time prediction class

# Set to track already recognized attendees
recognized_attendees = set()

# Real-Time Prediction
def video_frame_callback(frame):
    global setTime
    img = frame.to_ndarray(format="bgr24")  # Convert to 3D NumPy array
    pred_img = realtimepred.face_prediction(img, redis_face_db, 'facial_features', ['Name', 'Role'], thresh=0.5)

    timenow = time.time()
    difftime = timenow - setTime

    if difftime >= waitTime:
        # Save logs to Redis and get logged attendees
        attendees = realtimepred.saveLogs_redis()

        # Check if attendees were recognized
        if attendees:
            for attendee in attendees:
                if attendee not in recognized_attendees:
                    # Update the placeholder with success message
                    attendance_placeholder.success(f"Attendance recorded for: {attendee}")
                    recognized_attendees.add(attendee)  # Add to the recognized set
                    print(f"Attendance recorded for: {attendee}")
        setTime = time.time()  # Reset time

    return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

# Add WebRTC streamer component to the layout
webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback,
                rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    })

