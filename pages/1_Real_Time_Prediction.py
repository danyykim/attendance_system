import streamlit as st 
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time

# st.set_page_config(page_title='Predictions')
st.subheader('Real-Time Attendance System')


# Retrive the data from Redis Database
with st.spinner('Retriving Data from Redis DB ...'):    
    redis_face_db = face_rec.retrive_data(name='academy:register')
    st.dataframe(redis_face_db)
    
st.success("Data sucessfully retrived from Redis")

# time 
waitTime = 30 # time in sec
setTime = time.time()
realtimepred = face_rec.RealTimePred() # real time prediction class

last_recognized_person = st.empty()  # This will store the last recognized person
previous_name = None  # Variable to store the previous recognized name
# Real Time Prediction
# streamlit webrtc
# callback function
def video_frame_callback(frame):
    global setTime, previous_name
    
    img = frame.to_ndarray(format="bgr24") # 3 dimension numpy array
    # operation that you can perform on the array
    pred_img = realtimepred.face_prediction(img,redis_face_db,
                                        'facial_features',['Name','Role'],thresh=0.5)
    
    timenow = time.time()
    difftime = timenow - setTime
    if difftime >= waitTime:
        realtimepred.saveLogs_redis()
        setTime = time.time() # reset time        
        print('Save Data to redis database')
    
    current_name = realtimepred.logs['name'][-1] if realtimepred.logs['name'] else None
    if current_name and current_name != previous_name and current_name != "Unknown":
        last_recognized_person.success(f"User {current_name} recognized successfully!")  # Display success message
        previous_name = current_name  # Update the previous recognized name

    return av.VideoFrame.from_ndarray(pred_img, format="bgr24")


webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback,
                rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    })