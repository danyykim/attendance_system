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

    logs_df["Timestamp"] = pd.to_datetime(logs_df['Timestamp'], format="%Y-%m-%d %H:%M:%S", errors='coerce')
    logs_df["Date"] = logs_df['Timestamp'].dt.date
    
    # Date selection filter
    selected_date = st.date_input('Select a date to view the attendance report', pd.to_datetime('today').date())

    # Filter the logs based on the selected date
    filtered_logs_df = logs_df[logs_df['Date'] == selected_date]
    
    logs_df.sort_values(by=['Name', 'Timestamp'], inplace=True)
    
    check_in_df = filtered_logs_df[filtered_logs_df['Action'] == 'Check In'].copy()
    check_out_df = filtered_logs_df[filtered_logs_df['Action'] == 'Check Out'].copy()  
    
    if 'Role' not in check_in_df.columns:
        check_in_df['Role'] = 'Unknown'  # Default to 'Unknown' if missing
    if 'Role' not in check_out_df.columns:
        check_out_df['Role'] = 'Unknown'  # Default to 'Unknown' if missing
    
    report_df = pd.merge_asof(
        check_in_df.sort_values('Timestamp'),
        check_out_df.sort_values('Timestamp'),
        on='Timestamp',
        by='Name',  # Ensure that it matches by Name
        direction='forward',  # Only match check-out times that are after check-in times
        suffixes=('_in', '_out')
    )
    
    print(report_df.columns)

    # Manually verify and adjust the column references if necessary
    if 'Timestamp_in' not in report_df.columns:
        report_df['In_time'] = report_df['Timestamp']
    else:
        report_df['In_time'] = report_df['Timestamp_in']

    # Adjust for the out time as well
    if 'Timestamp_out' not in report_df.columns:
        report_df['Out_time'] = pd.NaT  # Set as NaT (Not a Time) if there is no corresponding out time
    else:
        report_df['Out_time'] = report_df['Timestamp_out']
  
    report_df['Date'] = report_df['In_time'].dt.date
  
    def calculate_duration(row):
        if pd.isnull(row['Out_time']):
            return 'Pending'
        else:
            duration = row['Out_time'] - row['In_time']
            return str(duration)

    report_df['Duration'] = report_df.apply(calculate_duration, axis=1)
    
    report_df.index += 1  # Shift index to start from 1
    
    if 'Role' not in report_df.columns:
        report_df['Role'] = 'Unknown'
    
    st.dataframe(report_df[['Name', 'Role', 'Date', 'In_time', 'Out_time', 'Duration']])
