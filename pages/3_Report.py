import streamlit as st
from Home import face_rec
import pandas as pd

if not st.session_state.get("authentication_status", False):
    st.warning("You must log in first.")
    st.stop()

st.set_page_config(page_title='Reporting', layout='wide')
st.subheader('Reporting')

name = 'attendance:logs'

def load_logs(name, end=-1):
    logs_list = face_rec.r.lrange(name, start=0, end=end)
    return logs_list

tab1, tab2, tab3 = st.tabs(['Registered Data', 'Logs', 'Attendance Report'])

with tab1:
    if st.button('Refresh Data'):
        with st.spinner('Retrieving Data from Redis DB ...'):
            redis_face_db = face_rec.retrive_data(name='academy:register')

            if len(redis_face_db['Name']) == len(redis_face_db['Role']) == len(redis_face_db['IC']):
                redis_face_db.index += 1  # Shift index to start from 1
                st.dataframe(redis_face_db[['Name', 'Role', 'IC']])
            else:
                st.error("Data inconsistency: Column lengths do not match!")

with tab2:
    if st.button('Refresh Logs'):        
        logs_before = load_logs(name=name)
        st.write(logs_before)

        # Check if new logs have been added
        if logs_before:
            new_data_added = True  # Assume new data has been added if we get any logs
            # Print/log the new data or any relevant info if needed
        else:
            new_data_added = False

        # Store success message conditionally
        if new_data_added:
            st.session_state['success'] = True  # Set success flag

# Show success message if new data was added
if st.session_state.get('success', False):
    st.success("Success: New data has been entered into attendance logs.")
    st.session_state['success'] = False  # Reset flag

with tab3:
    st.subheader('Attendance Report')

    logs_list = load_logs(name=name)

    convert_byte_to_string = lambda x: x.decode("utf-8")
    logs_list_string = list(map(convert_byte_to_string, logs_list))
    
    split_string = lambda x: x.split('@')
    logs_nested_list = list(map(split_string, logs_list_string))
    
    logs_df = pd.DataFrame(logs_nested_list, columns=['Name', 'Role', 'Timestamp'])

    logs_df["Timestamp"] = pd.to_datetime(logs_df['Timestamp'])
    logs_df["Date"] = logs_df['Timestamp'].dt.date
    
    report_df = logs_df.groupby(by=['Date', 'Name', 'Role']).agg(
        In_time=pd.NamedAgg('Timestamp', 'min'),
        Out_time=pd.NamedAgg('Timestamp', 'max'),
    ).reset_index()
    
    report_df['In_time'] = pd.to_datetime(report_df['In_time'])
    report_df['Out_time'] = pd.to_datetime(report_df['Out_time'])
    report_df['Duration'] = report_df['Out_time'] - report_df['In_time']

    report_df.index += 1  # Shift index to start from 1
    st.dataframe(report_df)
