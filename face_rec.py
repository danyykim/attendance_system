import numpy as np
import pandas as pd
import streamlit as st
import cv2
import redis
import pytz
# insight face
from insightface.app import FaceAnalysis
from sklearn.metrics import pairwise
# time
import time
from datetime import datetime

import os

# Connect to Redis Client
hostname = 'redis-10380.c240.us-east-1-3.ec2.redns.redis-cloud.com'
portnumber = '10380'
password = '6z4TqpJEaYTnp6dy9renIRjJV3Enlj9i'

r = redis.StrictRedis(host=hostname,
                      port=portnumber,
                      password=password)

# Retrive Data from database
def retrive_data(name):
    retrive_dict= r.hgetall(name)
    if not retrive_dict:  # Check if the retrieved dictionary is empty
        # Return an empty DataFrame with the expected columns
        return pd.DataFrame(columns=['Name', 'Role', 'IC', 'facial_features'])
    retrive_series = pd.Series(retrive_dict)
    retrive_series = retrive_series.apply(lambda x: np.frombuffer(x,dtype=np.float32))
    index = retrive_series.index
    index = list(map(lambda x: x.decode(), index))
    retrive_series.index = index
    retrive_df =  retrive_series.to_frame().reset_index()
    retrive_df.columns = ['name_role','facial_features']
    
    def safe_split(x):
        parts = x.split("@")
        if len(parts) == 3:
            return parts
        elif len(parts) == 2:
            return parts + ['Unknown']
        else:
            return['Unknown','Unknown','Unknown']
        
    retrive_df[['Name','Role','IC']] = retrive_df['name_role'].apply(safe_split).apply(pd.Series)
    
    return retrive_df[['Name','Role','IC','facial_features']]


# configure face analysis
faceapp = FaceAnalysis(name='buffalo_sc',root='insightface_model', providers = ['CPUExecutionProvider'])
faceapp.prepare(ctx_id = 0, det_size=(640,640), det_thresh = 0.5)

def get_current_time():
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time = datetime.now(malaysia_tz).strftime("%Y-%m-%d %H:%M:%S")
    return current_time
# ML Search Algorithm
def ml_search_algorithm(dataframe,feature_column,test_vector,
                        name_role=['Name','Role'],thresh=0.5):
    """
    cosine similarity base search algorithm
    """
    # step-1: take the dataframe (collection of data)
    dataframe = dataframe.copy()
    # step-2: Index face embeding from the dataframe and convert into array
    X_list = dataframe[feature_column].tolist()
    x = np.asarray(X_list)
    
    # step-3: Cal. cosine similarity
    similar = pairwise.cosine_similarity(x,test_vector.reshape(1,-1))
    similar_arr = np.array(similar).flatten()
    dataframe['cosine'] = similar_arr

    # step-4: filter the data
    data_filter = dataframe.query(f'cosine >= {thresh}')
    if len(data_filter) > 0:
        # step-5: get the person name
        data_filter.reset_index(drop=True,inplace=True)
        argmax = data_filter['cosine'].argmax()
        person_name, person_role = data_filter.loc[argmax][name_role]
        
    else:
        person_name = 'Unknown'
        person_role = 'Unknown'
        
    return person_name, person_role


### Real Time Prediction
# we need to save logs for every 1 mins
class RealTimePred:
    def __init__(self):
        self.logs = dict(name=[],role=[],current_time=[], action=[])
        
    def reset_dict(self):
        self.logs = dict(name=[],role=[],current_time=[], action=[])
        
    def saveLogs_redis(self):
    # Step 1: Create a logs DataFrame
            
        dataframe = pd.DataFrame(self.logs)
        # Step 2: Drop duplicate information (distinct name)
        dataframe.drop_duplicates(['name', 'action'], inplace=True)

        # Step 3: Push data to Redis database (list)
        # Encode the data
        name_list = dataframe['name'].tolist()
        role_list = dataframe['role'].tolist()
        ctime_list = dataframe['current_time'].tolist()
        action_list = dataframe['action'].tolist()
        encoded_data = []
        logged_names = []
        unknown_count = 0

        for name, role, ctime, action in zip(name_list, role_list, ctime_list, action_list):
            if name != 'Unknown':
                concat_string = f"{name}@{role}@{ctime}@{action}"
                encoded_data.append(concat_string)
                logged_names.append(name)
            else:
                unknown_count += 1

        if len(encoded_data) > 0:
            r.lpush('attendance:logs', *encoded_data)

            self.reset_dict() 
        
        return logged_names, unknown_count

    def face_prediction(self,test_image, dataframe,feature_column,
                            name_role=['Name','Role'],thresh=0.5, action="Check In"):
        # step-1: find the time
        current_time = get_current_time()
        
        # step-1: take the test image and apply to insight face
        results = faceapp.get(test_image)
        test_copy = test_image.copy()
        # step-2: use for loop and extract each embedding and pass to ml_search_algorithm

        for res in results:
            x1, y1, x2, y2 = res['bbox'].astype(int)
            embeddings = res['embedding']
            person_name, person_role = ml_search_algorithm(dataframe,
                                                        feature_column,
                                                        test_vector=embeddings,
                                                        name_role=name_role,
                                                        thresh=thresh)
            
            already_checked_in = False
            color = (0, 0, 255)  # Red for unknown user
            
            if person_name != 'Unknown':
                # Step-3: Check if the person is already checked in (from Redis status)
                check_in_status = r.hget('attendance:status', person_name)
                
                if check_in_status is None:  # First time check-in
                    r.hset('attendance:status', person_name, 'checked_in')
                    action = "Check In"
                    color = (0, 255, 0)  # Green for valid check-in
                    already_checked_in = False  # Not yet checked in
                    
                else:
                    # Step-4: Check if the logs have been updated in the last cycle (10 seconds)
                    if person_name in self.logs['name']:  # This means they've been logged
                        action = "Already Checked In"
                        color = (0, 255, 255)  # Yellow for already checked in
                        already_checked_in = True  # User is already checked in
                        
                    else:  # Data hasn't been saved yet, keep it green
                        action = "Check In"
                        color = (0, 255, 0)  # Keep it green until saved to logs
                    
        # Step-5: Draw rectangle and label


            cv2.rectangle(test_copy,(x1,y1),(x2,y2),color)

            text_gen = person_name
            cv2.putText(test_copy,text_gen,(x1,y1),cv2.FONT_HERSHEY_DUPLEX,0.7,color,2)
            cv2.putText(test_copy,current_time,(x1,y2+10),cv2.FONT_HERSHEY_DUPLEX,0.7,color,2)
            # save info in logs dict
            self.logs['name'].append(person_name)
            self.logs['role'].append(person_role)
            self.logs['current_time'].append(current_time)
            self.logs['action'].append(action)
            
        return test_copy, already_checked_in


#### Registration Form
class RegistrationForm:
    def __init__(self):
        self.sample = 0
    def reset(self):
        self.sample = 0
        
    def get_embedding(self,frame):
        # get results from insightface model
        results = faceapp.get(frame,max_num=1)
        embeddings = None
        for res in results:
            self.sample += 1
            x1, y1, x2, y2 = res['bbox'].astype(int)
            cv2.rectangle(frame, (x1,y1),(x2,y2),(0,255,0),1)
            # put text samples info
            text = f"samples = {self.sample}"
            cv2.putText(frame,text,(x1,y1),cv2.FONT_HERSHEY_DUPLEX,0.6,(255,255,0),2)
            
            # facial features
            embeddings = res['embedding']
            
        return frame, embeddings
    
    def check_ic_exists(self, ic_number):
        # Check if the IC number is already in the Redis database
        keys = r.hkeys('academy:register')  # Retrieve all keys from the specified hash
        for key in keys:
            # Split the key to check the IC number
            _, _, existing_ic = key.decode().split('@')  # Decode and split the key
            if existing_ic == ic_number:  # Compare with the given IC number
                return True
        return False

    def save_data_in_redis_db(self, name, role, ic_number):
        if not name or name.strip() == '':
            return 'name_false'
        
        # Check if the IC number already exists
        if self.check_ic_exists(ic_number):
            return 'ic_exists'

        if 'face_embedding.txt' not in os.listdir():
            return 'file_false'
        
        # Load face embeddings and save to Redis
        x_array = np.loadtxt('face_embedding.txt', dtype=np.float32)
        received_samples = int(x_array.size / 512)
        x_array = x_array.reshape(received_samples, 512).astype(np.float32)
        x_mean = x_array.mean(axis=0).astype(np.float32)
        x_mean_bytes = x_mean.tobytes()

        key = f'{name}@{role}@{ic_number}'
        r.hset(name='academy:register', key=key, value=x_mean_bytes)
        
        os.remove('face_embedding.txt')
        self.reset()
        
        return True
    