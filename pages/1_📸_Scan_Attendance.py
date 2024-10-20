import streamlit as st
from Home import face_rec
import time
import threading
import base64

if not st.session_state.get("authentication_status", False):
    st.warning("You must log in first.")
    st.stop()
    
lock = threading.Lock()
success_container = {"success": False}

# Set up the layout with buttons
st.subheader('Attendance System')

# Initialize session state if not already done
if 'show_camera' not in st.session_state:
    st.session_state.show_camera = False
if 'check_in' not in st.session_state:
    st.session_state.check_in = False
if 'check_out' not in st.session_state:
    st.session_state.check_out = False
if 'audio_played' not in st.session_state:
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

    # Camera Input
    image = st.camera_input("Capture Image")

    if image is not None:
        # Process the captured image
        img = face_rec.load_image(image)  # Implement your own image loading function
        action = "Check In" if st.session_state.check_in else "Check Out"
        # Run your facial recognition logic here
        # Example:
        pred_img = face_rec.face_prediction(img, redis_face_db, 'facial_features', ['Name', 'Role'], thresh=0.5, action=action)
        
        # Here, you can log the attendance or do further processing
        logged_names, unknown_count, already_checked_in, already_checked_out = face_rec.saveLogs_redis(action)

        # Update the success container
        with lock:
            success_container["success"] = True
            success_container["names"] = logged_names
            success_container["unknown_count"] = unknown_count
            success_container["already_checked_in"] = already_checked_in
            success_container["already_checked_out"] = already_checked_out

    # Status Update Section
    st.subheader('Status')
    success_placeholder = st.empty()

    # Audio playback logic
    def play_audio(audio_file):
        with open(audio_file, 'rb') as f:
            audio_data = f.read()
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        audio_base64_src = f"data:audio/mp3;base64,{audio_base64}"
        st.markdown(
            f"""
            <audio autoplay="true" style="display:none;">
            <source src="{audio_base64_src}" type="audio/mp3">
            </audio>
            """,
            unsafe_allow_html=True
        )

    if success_container["success"]:
        names = ', '.join(success_container.get("names", []))
        unknown_count = success_container.get("unknown_count", 0)
        already_checked_in = ', '.join(success_container.get("already_checked_in", []))
        already_checked_out = ', '.join(success_container.get("already_checked_out", []))

        if already_checked_in:
            info_message = f"Already marked: {already_checked_in}"
            success_placeholder.info(info_message)
            play_audio('error_sound.mp3')

        if already_checked_out:
            info_message = f"Already checked out: {already_checked_out}"
            success_placeholder.info(info_message)
            play_audio('error_sound.mp3')

        if names and action == "Check Out" and not already_checked_out:
            success_message = f"Successfully checked out! Names: {names}"
            success_placeholder.success(success_message)
            play_audio('success-sound.mp3')

        elif names and action == "Check In" and not already_checked_in:
            success_message = f"Data has been successfully saved! Names: {names}"
            success_placeholder.success(success_message)
            play_audio('success-sound.mp3')

        if unknown_count > 0:
            success_message += f" | Unknown Persons Detected: {unknown_count}"

        time.sleep(3)
        success_placeholder.empty()
        success_container["success"] = False  # Reset after showing message
