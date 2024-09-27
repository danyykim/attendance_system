import streamlit as st 
from Home import face_rec
import pandas as pd

if not st.session_state.get("authentication_status", False):
    st.warning("You must log in first.")
    st.stop()

st.set_page_config(page_title='Reporting',layout='wide')
st.subheader('Reporting')


# Retrive logs data and show in Report.py
# extract data from redis list
name = 'attendance:logs'
def load_logs(name,end=-1):
    logs_list = face_rec.r.lrange(name,start=0,end=end) # extract all data from the redis database
    return logs_list

# tabs to show the info
tab1, tab2, tab3 = st.tabs(['Registered Data','Logs','Attendance Report'])

with tab1:
    if st.button('Refresh Data'):
        # Retrive the data from Redis Database
        with st.spinner('Retriving Data from Redis DB ...'):    
            redis_face_db = face_rec.retrive_data(name='academy:register')
          
            if len(redis_face_db['Name']) == len(redis_face_db['Role']) == len(redis_face_db['IC']):
                st.dataframe(redis_face_db[['Name', 'Role', 'IC']])
            else:
                st.error("Data inconsistency: Column lengths do not match!")

with tab2:
    if st.button('Refresh Logs'):
        st.write(load_logs(name=name))
        
with tab3:
    st.subheader('Attendance Report')

    #load logs into attribute logs_list
    logs_list = load_logs(name=name)
    
    # step -1: convert the logs that in list of bytes into list of string
    convert_byte_to_string = lambda x: x.decode("utf-8")
    logs_list_string = list(map(convert_byte_to_string, logs_list))
    
    #step 2 - split string by @ and create nested list
    split_string = lambda x: x.split('@')
    logs_nested_list = list(map(split_string, logs_list_string))
    #convert nested list info into dataframe
    
    logs_df = pd.DataFrame(logs_nested_list, columns= ['Name','Role','Timestamp'])
    
    # step -3 Time based Analysis or Report
    logs_df["Timestamp"] = pd.to_datetime(logs_df['Timestamp'])
    logs_df["Date"] = logs_df['Timestamp'].dt.date
    
    #step 3.1 Call Intime and Outtime
    # In time: At which person is first detected in that day(min Timestamp of the date)
    # Out Time: At which person is last detected in that day(min Timestamp of the date)
    
    report_df = logs_df.groupby(by=['Date','Name','Role','IC']).agg(
        In_time = pd.NamedAgg('Timestamp','min'), #in time
        Out_time = pd.NamedAgg('Timestamp','max'), # out time
    ).reset_index()
    
    report_df['In_time'] = pd.to_datetime(report_df['In_time'])
    report_df['Out_time'] = pd.to_datetime(report_df['Out_time'])

    report_df['Duration'] = report_df['Out_time'] - report_df['In_time']
    st.dataframe(report_df)