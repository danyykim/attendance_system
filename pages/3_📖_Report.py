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

    # Load check-ins and check-outs separately
    check_in_logs = load_logs('attendance:checkins')
    check_out_logs = load_logs('attendance:checkouts')

    # Convert logs to DataFrames
    convert_byte_to_string = lambda x: x.decode("utf-8")
    check_in_logs_string = list(map(convert_byte_to_string, check_in_logs))
    check_out_logs_string = list(map(convert_byte_to_string, check_out_logs))

    check_in_nested_list = [log.split('@') for log in check_in_logs_string]
    check_out_nested_list = [log.split('@') for log in check_out_logs_string]

    check_in_df = pd.DataFrame(check_in_nested_list, columns=['Name', 'Role', 'Timestamp', 'Action'])
    check_out_df = pd.DataFrame(check_out_nested_list, columns=['Name', 'Role', 'Timestamp', 'Action'])

    # Convert timestamps to datetime
    check_in_df["Timestamp"] = pd.to_datetime(check_in_df['Timestamp'], format="%Y-%m-%d %H:%M:%S", errors='coerce')
    check_out_df["Timestamp"] = pd.to_datetime(check_out_df['Timestamp'], format="%Y-%m-%d %H:%M:%S", errors='coerce')

    # Merge DataFrames on Name and Role
    report_df = pd.merge(check_in_df, check_out_df, on=['Name', 'Role'], how='left', suffixes=('_in', '_out'))

    # Rename columns for clarity
    report_df.rename(columns={'Timestamp_in': 'In_time', 'Timestamp_out': 'Out_time'}, inplace=True)

    def calculate_duration(row):
        if pd.isnull(row['Out_time']):
            return 'Pending'
        else:
            duration = row['Out_time'] - row['In_time']
            return str(duration)

    report_df['Duration'] = report_df.apply(calculate_duration, axis=1)

    report_df.index += 1  # Shift index to start from 1
    st.dataframe(report_df[['Name', 'Role', 'In_time', 'Out_time', 'Duration']])

