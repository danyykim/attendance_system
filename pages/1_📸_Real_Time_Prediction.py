import streamlit as st 
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time
import tkinter as tk

# st.set_page_config(page_title='Predictions')
st.subheader('Real-Time Attendance System')

# Retrieve the data from Redis Database
with st.spinner('Retrieving Data from Redis DB ...'):    
    redis_face_db = face_rec.retrive_data(name='academy:register')
    st.dataframe(redis_face_db)
    
st.success("Data successfully retrieved from Redis")

# time 
waitTime = 10 # time in sec
setTime = time.time()
realtimepred = face_rec.RealTimePred() # real time prediction class

def video_frame_callback(frame):
    global setTime

    img = frame.to_ndarray(format="bgr24")  # Convert frame to numpy array
    # Perform face prediction using face_rec.face_prediction
    result = realtimepred.face_prediction(img, redis_face_db,
                                          'facial_features', ['Name', 'Role'], thresh=0.5)

    # Assuming result is a dictionary or tuple with predicted attributes
    predicted_name = result.get('Name') if isinstance(result, dict) else result[0]  # Adjust as per actual output

    timenow = time.time()
    difftime = timenow - setTime
    if difftime >= waitTime:
        realtimepred.saveLogs_redis()  # Assuming saveLogs_redis is defined in face_rec
        setTime = time.time()  # Reset timer

        # Display a message window
        message = f"Tahniah {predicted_name} kerana hadir!"  # Example message
        window_width = 300
        window_height = 200
        close_after_ms = 5000  # 5000 milliseconds = 5 seconds

        create_message_window(message, window_width, window_height, close_after_ms)

    return av.VideoFrame.from_ndarray(img, format="bgr24")  # Return the original frame or processed frame



# Assuming create_message_window is defined somewhere else
def create_message_window(message, width, height, close_after):
    # Implement your message window creation logic here
    pass

def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width / 2) - (width / 2)
    y = (screen_height / 2) - (height / 2)
    window.geometry(f'{width}x{height}+{int(x)}+{int(y)}')

def close_after(window, milliseconds):
    window.after(milliseconds, window.destroy)

def create_message_window(message, width, height, close_after_ms):
    root = tk.Tk()
    root.title('Message Window')
    
    label = tk.Label(root, text=message)
    label.pack(pady=20)
    
    button = tk.Button(root, text='Close', width=25, command=lambda: close_after(root, 0))
    button.pack()
    
    center_window(root, width, height)
    close_after(root, close_after_ms)
    
    root.mainloop() #command used to execute popup message.

webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback,
                rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    })

