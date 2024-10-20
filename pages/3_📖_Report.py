import streamlit as st
from Home import face_rec
import pandas as pd
from styles import set_page_background

# Apply background color
set_page_background()
if not st.session_state.get("authentication_status", False):
    st.warning("You must log in first.")
    st.stop()

st.set_page_config(page_title='Reporting', layout='wide')
st.subheader('Reporting')

name = 'attendance:logs'

def load_logs(name, end=-1):
    logs_list = face_rec.r.lrange(name, start=0, end=end)
    return logs_list

# Tabs: Registered Data and Attendance Report (Removed Logs tab for simplicity)
tab1, tab2 = st.tabs(['Registered Data', 'Attendance Report'])

# Tab 1: Registered Data
with tab1:
    # Add date filter and role filter
    selected_role = st.selectbox('Filter by Role', ['All', 'Student', 'Teacher'])
    
    if st.button('Refresh Data'):
        with st.spinner('Retrieving Data from Redis DB ...'):
            redis_face_db = face_rec.retrive_data(name='academy:register')

            # Ensure consistency in the data length
            if len(redis_face_db['Name']) == len(redis_face_db['Role']) == len(redis_face_db['IC']):
                redis_face_db.index += 1  # Shift index to start from 1

                # Apply the selected filters
                filtered_data = redis_face_db.copy()

                # Apply role filter
                if selected_role != 'All':
                    filtered_data = filtered_data[filtered_data['Role'] == selected_role]

                # Display the filtered data
                st.dataframe(filtered_data[['Name', 'Role', 'IC']])
            else:
                st.error("Data inconsistency: Column lengths do not match!")

# Tab 2: Attendance Report (similar to the original)
with tab2:
    st.subheader('Attendance Report')

    logs_list = load_logs(name=name)

    convert_byte_to_string = lambda x: x.decode("utf-8")
    logs_list_string = list(map(convert_byte_to_string, logs_list))
    
    split_string = lambda x: x.split('@')
    logs_nested_list = list(map(split_string, logs_list_string))
    
    logs_df = pd.DataFrame(logs_nested_list, columns=['Name', 'Role', 'Timestamp', 'Action'])

    # Convert Timestamp to datetime
    logs_df["Timestamp"] = pd.to_datetime(logs_df['Timestamp'], format="%Y-%m-%d %H:%M:%S", errors='coerce')
    logs_df["Date"] = logs_df['Timestamp'].dt.date  # Ensure 'Date' is created from 'Timestamp'
    
    # Date selection filter
    selected_date = st.date_input('Select a date to view the attendance report', pd.to_datetime('today').date())

    # Filter logs based on the selected date
    filtered_logs_df = logs_df[logs_df['Date'] == selected_date]

    # Sort logs by Name and Timestamp to ensure correct order
    filtered_logs_df = filtered_logs_df.sort_values(by=['Name', 'Timestamp'])
    
    # Separate Check-In and Check-Out actions
    check_in_df = filtered_logs_df[filtered_logs_df['Action'] == 'Check In'].copy()
    check_out_df = filtered_logs_df[filtered_logs_df['Action'] == 'Check Out'].copy()
    
    # Ensure both DataFrames have the same column names before merging
    check_in_df = check_in_df.rename(columns={"Timestamp": "In_time"})
    check_out_df = check_out_df.rename(columns={"Timestamp": "Out_time"})

    # Merge Check-Ins with Check-Outs ensuring correct pairing
    report_df = pd.merge_asof(
        check_in_df.sort_values('In_time'),
        check_out_df.sort_values('Out_time'),
        left_on='In_time',
        right_on='Out_time',
        by='Name',
        direction='forward',  # Ensure check-out happens after check-in
        suffixes=('_in', '_out')
    )

    # Ensure 'Role' is preserved after the merge
    if 'Role_in' in report_df.columns:
        report_df['Role'] = report_df['Role_in']
    elif 'Role_out' in report_df.columns:
        report_df['Role'] = report_df['Role_out']
    else:
        report_df['Role'] = 'Unknown'

    # Check if the columns exist to avoid KeyError
    if 'In_time' in report_df.columns:
        report_df['In_time'] = report_df['In_time']
    else:
        report_df['In_time'] = pd.NaT

    if 'Out_time' in report_df.columns:
        report_df['Out_time'] = report_df['Out_time']
    else:
        report_df['Out_time'] = pd.NaT

    # Ensure 'Date' is created correctly
    report_df['Date'] = report_df['In_time'].dt.date

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
