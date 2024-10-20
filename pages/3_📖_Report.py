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
       logs = load_logs(name=name)       
       st.write(logs)
       
       log_count = len(logs)
       st.write(f"Total logs: {log_count}")

with tab3:
    st.subheader('Attendance Report')

    logs_list = load_logs(name=name)

    convert_byte_to_string = lambda x: x.decode("utf-8")
    logs_list_string = list(map(convert_byte_to_string, logs_list))
    
    split_string = lambda x: x.split('@')
    logs_nested_list = list(map(split_string, logs_list_string))
    
    logs_df = pd.DataFrame(logs_nested_list, columns=['Name', 'Role', 'Timestamp', 'Action'])

    # Convert Timestamp to datetime
    logs_df["Timestamp"] = pd.to_datetime(logs_df['Timestamp'], format="%Y-%m-%d %H:%M:%S", errors='coerce')
    logs_df["Date"] = logs_df['Timestamp'].dt.date
    
    # Date selection filter
    selected_date = st.date_input('Select a date to view the attendance report', pd.to_datetime('today').date())

    # Filter logs based on the selected date
    filtered_logs_df = logs_df[logs_df['Date'] == selected_date]

    # Sort logs by Name and Timestamp to ensure correct order
    filtered_logs_df = filtered_logs_df.sort_values(by=['Name', 'Timestamp'])
    
    # Separate Check-In and Check-Out actions
    check_in_df = filtered_logs_df[filtered_logs_df['Action'] == 'Check In'].copy()
    check_out_df = filtered_logs_df[filtered_logs_df['Action'] == 'Check Out'].copy()
    
    # Merge Check-Ins with Check-Outs using merge_asof to ensure that each check-in pairs with the next check-out
    report_df = pd.merge_asof(
        check_in_df.sort_values('Timestamp'),
        check_out_df.sort_values('Timestamp'),
        on='Timestamp',
        by='Name',
        direction='forward',  # Ensure check-out happens after check-in
        suffixes=('_in', '_out')
    )
    
    # Set In_time and Out_time columns
    report_df['In_time'] = report_df['Timestamp_in']
    report_df['Out_time'] = report_df['Timestamp_out']
    
    # Handle cases where no check-out has happened yet
    def calculate_duration(row):
        if pd.isnull(row['Out_time']):
            return 'Pending'
        else:
            return str(row['Out_time'] - row['In_time'])

    report_df['Duration'] = report_df.apply(calculate_duration, axis=1)

    # Display the report in the UI
    report_df.index += 1  # Shift index to start from 1
    st.dataframe(report_df[['Name', 'Role', 'Date', 'In_time', 'Out_time', 'Duration']])

