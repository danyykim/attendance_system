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
    
    # Convert frame to NumPy array (for image processing)
    img = frame.to_ndarray(format="bgr24")
    
    # Perform face prediction (returns processed image and recognized name)
    try:
        pred_img, recognized_name = realtimepred.face_prediction(
            img, redis_face_db, 'facial_features', ['Name', 'Role'], thresh=0.5)
    except Exception as e:
        st.error(f"Error during face recognition: {e}")
        pred_img = img  # Fallback: If there's an error, return the original frame
        recognized_name = None

    # Get the current time and check if it's time to save the logs
    timenow = time.time()
    difftime = timenow - setTime
    
    if difftime >= waitTime:
        realtimepred.saveLogs_redis()  # Save logs to Redis
        setTime = time.time()  # Reset time
        print('Logs saved to Redis database')

    # Return the video frame with the predicted result (or original frame in case of error)
    return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

# Start WebRTC video stream with callback
webrtc_ctx = webrtc_streamer(
    key="realtimePrediction", 
    video_frame_callback=video_frame_callback,
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    }
)

# Notification section (placed **below** the camera feed)
if webrtc_ctx.state.playing:
    st.markdown("---")
    st.subheader("Attendance Notification")

    # Display student details and handle attendance marking below the camera
    if last_recognized_student is not None:
        student_data = redis_face_db[redis_face_db['Name'] == last_recognized_student]
        if not student_data.empty:
            role = student_data.iloc[0]['Role']
            ic_number = student_data.iloc[0]['IC']
            st.success(f"Attendance marked for {last_recognized_student}!")
            st.write(f"Student Name: {last_recognized_student}")
            st.write(f"Role: {role}")
            st.write(f"IC Number: {ic_number}")
        else:
            st.error("Student details not found in the database.")
    else:
        st.info("No face recognized. Waiting for scan...")
