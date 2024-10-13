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
    
    
    st.write("Logs Nested List:", logs_nested_list)  # Debugging step

    # Handle cases where logs_nested_list has 3 or 4 elements
    logs_nested_list = [row for row in logs_nested_list if len(row) == 4]
    
    logs_df = pd.DataFrame(logs_nested_list, columns=['Name', 'Role', 'Timestamp', 'Action'])

    logs_df["Timestamp"] = pd.to_datetime(logs_df['Timestamp'], format="%Y-%m-%d %H:%M:%S", errors='coerce')
    logs_df["Date"] = logs_df['Timestamp'].dt.date
    
    check_in_df = logs_df[logs_df['Action'] == 'Check In'].copy()
    check_out_df = logs_df[logs_df['Action'] == 'Check Out'].copy()
    
    report_df = pd.merge(check_in_df, check_out_df, on=['Name', 'Role', 'Date'], suffixes=('_in', '_out'))
    
    report_df['In_time'] = report_df['Timestamp_in']
    report_df['Out_time'] = report_df['Timestamp_out']
    report_df['Duration'] = report_df['Out_time'] - report_df['In_time']

    report_df.index += 1  # Shift index to start from 1
    st.dataframe(report_df[['Name', 'Role', 'Date', 'In_time', 'Out_time', 'Duration']])
