import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time

# Ensure the user is logged in
if not st.session_state.get("authentication_status", False):
    st.warning("You must log in first.")
    st.stop()

# Set up the page UI
st.subheader('Real-Time Attendance System')

# Placeholder for success/failure messages
attendance_placeholder = st.empty()  # Dynamic updates here

# Retrieve data from Redis Database
with st.spinner('Retrieving Data from Redis DB ...'):
    try:
        redis_face_db = face_rec.retrive_data(name='academy:register')
        st.success("Data successfully retrieved from Redis")
    except Exception as e:
        st.error(f"Error retrieving data: {e}")
        st.stop()  # Stop if data retrieval fails

# Time settings
waitTime = 30  # Time in seconds
setTime = time.time()
realtimepred = face_rec.RealTimePred()  # Real-time prediction class

# Set to track already recognized attendees
recognized_attendees = set()

# Real-Time Prediction Callback
def video_frame_callback(frame):
    global setTime
    img = frame.to_ndarray(format="bgr24")  # Convert to 3D NumPy array

    # Run face prediction on the frame
    pred_img = realtimepred.face_prediction(img, redis_face_db, 'facial_features', ['Name', 'Role'], thresh=0.5)

    timenow = time.time()
    difftime = timenow - setTime

    if difftime >= waitTime:
        # Save logs to Redis and get logged attendees
        try:
            attendees = realtimepred.saveLogs_redis()

            # Debug: Check if attendees list is not empty
            print(f"Attendees detected: {attendees}")  # Output to terminal for debugging

            # Display success message in Streamlit if attendance was recorded
            if attendees:
                for attendee in attendees:
                    if attendee not in recognized_attendees:
                        # Update placeholder with success message
                        attendance_placeholder.success(f"Attendance recorded for: {attendee}")
                        print(f"Attendance recorded for: {attendee}")  # Print for terminal logging
                        recognized_attendees.add(attendee)  # Mark as recognized
            else:
                attendance_placeholder.warning("No new attendees detected.")
        except Exception as e:
            attendance_placeholder.error(f"Error saving attendance: {e}")
        finally:
            setTime = time.time()  # Reset time regardless of outcome

    return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

# Add WebRTC streamer component to the layout
webrtc_streamer(
    key="realtimePrediction", 
    video_frame_callback=video_frame_callback,
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    }
)
