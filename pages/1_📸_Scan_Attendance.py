import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time
import threading
import base64

if not st.session_state.get("authentication_status", False):
    st.warning("You must log in first.")
    st.stop()
    
lock = threading.Lock()
success_container = {"success": False}  # Shared container

# Set up the layout with buttons
st.subheader('Attendance System')

# Initialize session state if not already done
if 'show_camera' not in st.session_state:
    st.session_state.show_camera = False
if 'check_in' not in st.session_state:
    st.session_state.check_in = False
if 'check_out' not in st.session_state:
    st.session_state.check_out = False
if 'audio_played' not in st.session_state:  # Track if audio is played to avoid repeating
    st.session_state.audio_played = False

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
        st.session_state.audio_played = False
        st.rerun()
    
    if st.session_state.check_in:
        st.subheader('Check In')
    elif st.session_state.check_out:
        st.subheader('Check Out')
    # Retrieve data from Redis
    with st.spinner('Retrieving Data from Redis DB ...'):
        redis_face_db = face_rec.retrive_data(name='academy:register')
    

    waitTime = 5
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
            logged_names, unknown_count, already_checked_in, already_checked_out = realtimepred.saveLogs_redis(action)
            setTime = time.time()  # Reset time
            
            # Thread-safe access
            with lock:
                success_container["success"] = True
                success_container["names"] = logged_names
                success_container["unknown_count"]  = unknown_count
                success_container["already_checked_in"] = already_checked_in
                success_container["already_checked_out"] = already_checked_out  # Add this line

        return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

    ctx = webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback, rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.services.mozilla.com:3478"]}]
    })

    # Status Update Section
    st.subheader('Status')
    success_placeholder = st.empty()
    
    success_audio_path = 'success-sound.mp3'  # Replace with correct path if needed
    error_audio_path = 'error_sound.mp3'  # Replace with correct path if needed

# Function to play audio in the background without displaying the audio bar
    def play_audio(audio_file):
        with open(audio_file, 'rb') as f:
            audio_data = f.read()  # Read the audio file as bytes

        # Encode the audio data to base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        # Create the HTML string to play the audio without showing the bar
        audio_base64_src = f"data:audio/mp3;base64,{audio_base64}"
        
        # Embed the audio in the HTML with autoplay and hidden display
        st.markdown(
            f"""
            <audio autoplay="true" style="display:none;">
            <source src="{audio_base64_src}" type="audio/mp3">
            </audio>
            """,
            unsafe_allow_html=True
        )


    while ctx.state.playing:
        with lock:
            if success_container["success"]:
                names = ', '.join(success_container.get("names", []))  # Join recognized names into a string
                unknown_count = success_container.get("unknown_count", 0)  # Get unknown person count
                already_checked_in = ', '.join(success_container.get("already_checked_in", []))  # Already marked names
                already_checked_out = ', '.join(success_container.get("already_checked_out", []))  # Already checked out names

                if already_checked_in:
                    info_message = f"Already marked: {already_checked_in}"
                    success_placeholder.info(info_message)  # Show "Already marked" message
                    play_audio(error_audio_path)
                
                # Display already checked out names
                if already_checked_out:
                    info_message = f"Already checked out: {already_checked_out}"
                    success_placeholder.info(info_message)  # Show "Already checked out" message
                    play_audio(error_audio_path)

                # Display success message for first check-out
                if names and action == "Check Out" and not already_checked_out:
                    success_message = f"Successfully checked out! Names: {names}"
                    success_placeholder.success(success_message)
                    play_audio(success_audio_path)

                # Display success message for check-in
                elif names and action == "Check In" and not already_checked_in:
                    success_message = f"Data has been successfully saved! Names: {names}"
                    success_placeholder.success(success_message)
                    play_audio(success_audio_path)

                if unknown_count > 0:
                    success_message += f" | Unknown Persons Detected: {unknown_count}"

                time.sleep(3)
                success_placeholder.empty()
                success_container["success"] = False  # Reset after showing message
        time.sleep(1)
