import streamlit as st 
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time
import threading
import cv2

# st.set_page_config(page_title='Predictions')
st.subheader('Real-Time Attendance System')

# Retrive the data from Redis Database
with st.spinner('Retrieving Data from Redis DB ...'):    
    redis_face_db = face_rec.retrive_data(name='academy:register')
    st.dataframe(redis_face_db)
    
st.success("Data successfully retrieved from Redis")

# Time setup and real-time prediction instance
waitTime = 30  # time in seconds
setTime = time.time()
realtimepred = face_rec.RealTimePred()  # Real-time prediction class

# Keep track of the last recognized name for showing success popups
last_recognized_person = st.empty()
previous_name = None

# Queue for logging to Redis asynchronously
log_queue = []

# Real-Time Prediction - Streamlit WebRTC
# Callback function for frame processing
def video_frame_callback(frame):
    global setTime, previous_name

    # Get the frame as a numpy array
    img = frame.to_ndarray(format="bgr24")
    
    # Resize frame for faster processing (optional)
    resized_img = cv2.resize(img, (320, 240))  # Resize for faster processing
    
    # Perform face prediction on the resized image
    pred_img = realtimepred.face_prediction(resized_img, redis_face_db, 'facial_features', ['Name', 'Role'], thresh=0.5)
    
    # Log saving mechanism
    timenow = time.time()
    difftime = timenow - setTime
    if difftime >= waitTime:
        # Push logs to Redis asynchronously to avoid blocking the frame processing
        log_queue.append(realtimepred.logs.copy())
        realtimepred.reset_dict()  # Reset logs
        setTime = time.time()

    # Face recognition notification
    current_name = realtimepred.logs['name'][-1] if realtimepred.logs['name'] else None
    if current_name and current_name != previous_name and current_name != "Unknown":
        last_recognized_person.success(f"User {current_name} recognized successfully!")
        previous_name = current_name

    # Return the predicted image for display
    return av.VideoFrame.from_ndarray(pred_img, format="bgr24")


# Function to save logs to Redis asynchronously
def save_logs_to_redis():
    while True:
        if log_queue:
            logs = log_queue.pop(0)
            for log in logs['name']:
                print(f"Saving log: {log}")  # Placeholder for Redis saving logic
            realtimepred.saveLogs_redis()  # Save logs to Redis

# Run the logging thread to handle Redis saving outside of the video callback
log_thread = threading.Thread(target=save_logs_to_redis, daemon=True)
log_thread.start()

# Start the Streamlit WebRTC video streamer
webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback,
                rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    })
