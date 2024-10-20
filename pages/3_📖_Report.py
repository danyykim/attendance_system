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

    # Step 1: Fetch keys for real-time attendance report from Redis
    keys = face_rec.r.keys('attendance:report:*')

    # Step 2: Extract real-time report data from Redis
    report_data = []
    for key in keys:
        report_entry = face_rec.r.hgetall(key)
        if report_entry:
            report_data.append({
                'Name': report_entry[b'name'].decode('utf-8'),
                'Role': report_entry[b'role'].decode('utf-8'),
                'In_time': report_entry[b'in_time'].decode('utf-8'),
                'Out_time': report_entry[b'out_time'].decode('utf-8') if b'out_time' in report_entry else None
            })
    
    # Step 3: Create a DataFrame for the real-time report data
    report_df = pd.DataFrame(report_data)

    if not report_df.empty:
        # Convert timestamps to datetime for formatting
        report_df['In_time'] = pd.to_datetime(report_df['In_time'], format="%Y-%m-%d %H:%M:%S", errors='coerce')
        report_df['Out_time'] = pd.to_datetime(report_df['Out_time'], format="%Y-%m-%d %H:%M:%S", errors='coerce')
        report_df['Date'] = report_df['In_time'].dt.date
    
        # Step 4: Date selection filter
        selected_date = st.date_input('Select a date to view the attendance report', pd.to_datetime('today').date())
    
        # Step 5: Filter the logs based on the selected date
        filtered_report_df = report_df[report_df['Date'] == selected_date]
    
        # Step 6: Calculate duration for each entry
        def calculate_duration(row):
            if pd.isnull(row['Out_time']):
                return 'Pending'
            else:
                duration = row['Out_time'] - row['In_time']
                return str(duration)

        filtered_report_df['Duration'] = filtered_report_df.apply(calculate_duration, axis=1)
    
        # Display the filtered report
        filtered_report_df.index += 1  # Shift index to start from 1
        st.dataframe(filtered_report_df[['Name', 'Role', 'Date', 'In_time', 'Out_time', 'Duration']])
    else:
        st.info("No attendance data available.")
