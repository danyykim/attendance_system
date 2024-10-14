import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time
import threading
import redis

hostname = 'redis-10380.c240.us-east-1-3.ec2.redns.redis-cloud.com'
portnumber = '10380'
password = '6z4TqpJEaYTnp6dy9renIRjJV3Enlj9i'

r = redis.StrictRedis(host=hostname,
                      port=portnumber,
                      password=password)
# Threading lock for thread-safe access
lock = threading.Lock()
success_container = {"success": False, "action": None}  # Shared container

# Set up the layout with buttons
st.subheader('Attendance System')

# Initialize session state if not already done
if 'show_camera' not in st.session_state:
    st.session_state.show_camera = False
if 'check_in' not in st.session_state:
    st.session_state.check_in = False
if 'check_out' not in st.session_state:
    st.session_state.check_out = False

# Check In and Check Out buttons
if not st.session_state.check_in and not st.session_state.check_out:
    col1, col2 = st.columns(2)
    with col1:
        if st.button('Check In'):
            st.session_state.check_in = True
            st.session_state.show_camera = True
            st.session_state.check_out = False
    with col2:
        if st.button('Check Out'):
            st.session_state.check_out = True
            st.session_state.show_camera = True
            st.session_state.check_in = False

if st.session_state.show_camera:
    
    # Set up the layout for the camera and status display
    
    if st.button('Back'):
        st.session_state.show_camera = False
        st.session_state.check_in = False
        st.session_state.check_out = False
        st.rerun()
    
    if st.session_state.check_in:
        st.subheader('Check In')
    elif st.session_state.check_out:
        st.subheader('Check Out')
        
    # Retrieve data from Redis
    with st.spinner('Retrieving Data from Redis DB ...'):
        redis_face_db = face_rec.retrive_data(name='academy:register')
    st.success("Data successfully retrieved from Redis")

    waitTime = 10
    setTime = time.time()
    realtimepred = face_rec.RealTimePred()

    if st.session_state.check_in:
        action = "Check In"
    elif st.session_state.check_out:
        action = "Check Out"
    else:
        action = None
        
    def video_frame_callback(frame):
        global setTime
        img = frame.to_ndarray(format="bgr24")
        pred_img = realtimepred.face_prediction(
            img, redis_face_db, 'facial_features', ['Name', 'Role'], thresh=0.5, action=action
        )
        
        timenow = time.time()
        difftime = timenow - setTime

        if difftime >= waitTime:
            logged_names, unknown_count = realtimepred.saveLogs_redis()
            setTime = time.time()  # Reset time
            
            for name in logged_names:
                check_in_status = r.hget('attendance:status', name)  # Retrieve their status from Redis

                if check_in_status == b'checked_in':
                    # If they have already been checked in, set the action to "Already Checked In"
                    r.hset('attendance:status', name, 'already_scanned')
            # Thread-safe access
            with lock:
                success_container["success"] = True
                success_container["names"] = logged_names
                success_container["unknown_count"]  = unknown_count
                
                for name in logged_names:
                    check_in_status = r.hget('attendance:status', name)
                    if check_in_status == b'already_scanned':
                        success_container["action"] = "Already Checked In"
                    else:
                        success_container["action"] = action  # Regular check-in or check-out
                        
        return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

    ctx = webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback, rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.services.mozilla.com:3478"]}]
    })

    # Status Update Section
    st.subheader('Status')
    success_placeholder = st.empty()

    while ctx.state.playing:
        with lock:
            if success_container["success"]:
                names = ', '.join(success_container.get("names", []))  # Join recognized names into a string
                unknown_count = success_container.get("unknown_count", 0)  # Get unknown person count
                action_status = success_container.get("action", "Unknown")  # Get action status
                
                if action_status == "Check In":
                    success_message = f"Checked In: {names}"
                elif action_status == "Already Checked In":
                    success_message = f"Already Checked In: {names}"
                elif action_status == "Check Out":
                    success_message = f"Checked Out: {names}"
                else:
                    success_message = f"Unknown action for {names}"

                if unknown_count > 0:
                    success_message += f" | Unknown Persons Detected: {unknown_count}"

                success_placeholder.success(success_message)
                time.sleep(5)
                success_placeholder.empty()
                success_container["success"] = False  # Reset after showing message
        time.sleep(1)
