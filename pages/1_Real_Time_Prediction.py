import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time

# Check if the user is authenticated before showing the page
if not st.session_state.get("authentication_status", False):
    st.warning("You must log in first.")
    st.stop()

st.subheader('Real-Time Attendance System')

# Retrieve data from Redis database
with st.spinner('Retrieving Data from Redis DB ...'):
    redis_face_db = face_rec.retrive_data(name='academy:register')

st.success("Data successfully retrieved from Redis")

# Define the time interval for saving logs
waitTime = 30  # time in seconds
setTime = time.time()
realtimepred = face_rec.RealTimePred()  # Real-time prediction class

# List to store recognized attendees to avoid repeating messages
recognized_attendees = set()

# Initialize session state for attendance success message
if "attendance_message" not in st.session_state:
    st.session_state["attendance_message"] = ""

# Define the callback function for video streaming
def video_frame_callback(frame):
    global setTime
    
    img = frame.to_ndarray(format="bgr24")  # Convert frame to 3D NumPy array

    # Perform real-time face prediction
    pred_img = realtimepred.face_prediction(img, redis_face_db,
                                            'facial_features', ['Name', 'Role'], thresh=0.5)

    timenow = time.time()
    difftime = timenow - setTime

    # After a specific wait time, save logs to Redis and show success message
    if difftime >= waitTime:
        attendees = realtimepred.saveLogs_redis()  # Save logs and get attendee names
        
        # Check if attendees were successfully logged
        if attendees:
            for attendee in attendees:
                if attendee not in recognized_attendees:  # Show success message for new attendees
                    st.session_state["attendance_message"] = f"Attendance recorded for: {attendee}"
                    recognized_attendees.add(attendee)  # Add to the list of recognized attendees

        setTime = time.time()  # Reset time for the next cycle
        print('Save Data to Redis database')

    # Return the processed image
    return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

# Display the success message in the Streamlit UI
if st.session_state["attendance_message"]:
    st.success(st.session_state["attendance_message"])

# WebRTC streamer for real-time video
webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback,
                rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    })

# Optional debugging information to display time and attendees
st.write(f"Time since last log: {time.time() - setTime:.2f} seconds")
st.write(f"Recognized attendees so far: {list(recognized_attendees)}")
