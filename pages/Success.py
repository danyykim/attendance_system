import streamlit as st
import time

# Check if the session state indicates that data was saved
if st.session_state.get('data_saved', False):
    st.set_page_config(page_title='Success', layout='centered')
    st.title("Success")
    st.success("Data saved successfully!")

    # Keep the message on screen for a few seconds
    time.sleep(2)  # Adjust the time as needed

    # Optionally reset the session state variable
    st.session_state['data_saved'] = False  # Reset for future saves

    # Redirect back to the main page after a delay
    st.info("Redirecting back to the main page...")
    time.sleep(5)  # Time before redirect
    st.rerun()  # This will rerun the app and take the user back to the previous page
else:
    st.warning("No data saved. Please try again.")
