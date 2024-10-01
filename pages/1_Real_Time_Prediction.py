import streamlit as st 
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time

# Check if the user is authenticated
if not st.session_state.get("authentication_status", False):
    st.warning("You must log in first.")
    st.stop()

st.subheader('Real-Time Attendance System')

# Retrieve the data from Redis Database
with st.spinner('Retrieving Data from Redis DB ...'):    
    redis_face_db = face_rec.retrive_data(name='academy:register')
    st.dataframe(redis_face_db)
    
st.success("Data successfully retrieved from Redis")

# Time management
waitTime = 30  # time in seconds
setTime = time.time()
realtimepred = face_rec.RealTimePred()  # Real-time prediction class

# Store the last recognized student to avoid redundant logging
last_recognized_student = None

# Real-time prediction and attendance marking
def video_frame_callback(frame):
    global setTime, last_recognized_student
    
    img = frame.to_ndarray(format="bgr24")  # Convert frame to NumPy array
    
    # Perform face prediction (returns processed image and recognized name)
    pred_img, recognized_name = realtimepred.face_prediction(
        img, redis_face_db, 'facial_features', ['Name', 'Role'], thresh=0.5)

    # Get the current time and check if it's time to save the logs
    timenow = time.time()
    difftime = timenow - setTime
    
    if difftime >= waitTime:
        realtimepred.saveLogs_redis()  # Save logs to Redis
        setTime = time.time()  # Reset time
        print('Logs saved to Redis database')

    # Display student details and handle attendance
    if recognized_name and recognized_name != "Unknown":
        if last_recognized_student is None or last_recognized_student != recognized_name:
            # New student recognized, display their details and mark attendance
            last_recognized_student = recognized_name
            marked_students = set()
            marked_students.add(recognized_name)

            # Get additional student details from Redis
            student_data = redis_face_db[redis_face_db['Name'] == recognized_name]
            if not student_data.empty:
                role = student_data.iloc[0]['Role']
                ic_number = student_data.iloc[0]['IC']
                st.success(f"Attendance marked for {recognized_name}!")
                st.write(f"Student Name: {recognized_name}")
                st.write(f"Role: {role}")
                st.write(f"IC Number: {ic_number}")
            else:
                st.error("Student details not found in the database.")

        else:
            # Same student recognized again, show 'already marked' message
            st.warning(f"{recognized_name} has already been marked for attendance.")
    
    return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

# Start WebRTC video stream with callback
webrtc_streamer(
    key="realtimePrediction", 
    video_frame_callback=video_frame_callback,
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    }
)
