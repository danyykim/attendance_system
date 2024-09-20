*To check for Database connection availability using virtual environment*  
- open new cmd 
- run command on cmd : virtualenv\Scripts\activate 
- after that, run this command : jupyter notebook 
- open file "check_redis_connection.ipynb"
- configure hostname, portnumber & password

# Connect to Redis Client
hostname = 'redis-10380.c240.us-east-1-3.ec2.redns.redis-cloud.com'
portnumber = '10380' 
password = '6z4TqpJEaYTnp6dy9renIRjJV3Enlj9i'

- execute line-by-line
- ensure ping is "True"

* To adjust execution provider
# ['CUDAExecutionProvider', 'CPUExecutionProvider', 'AzureExecutionProvider']

*To run in streamlit web-app*
1 - run new cmd & insert virtual environment
- open new cmd 
- run command on cmd : virtualenv\Scripts\activate 

2- run streamlit
streamlit run Home.py



## for hosting in AWS use:

# to reconfigure HTTPS with apache2 using .conf file
1- To get public IPv4 address
- on AWS Services page, click Instances under Instances section.
- click on link for selected Instances ID
- copy Public IPv4 address.

2- To navigate Instances
- on the same page, click Connect
- edit Username for Ubuntu and click connect
- program will launch Instances

3- To navigate .conf file
- cd /var/www/html
- vi /etc/apache2/sites-available/deploy_attendance_app.conf

4- To configure new IPv4 address in configure.sh
- press "i" to start edit.
- configure for host 80 in ServerName & Redirect, and then for host 443 in ServerName.
- press ESC and type ":wqa".
- double check using vi /etc/apache2/sites-available/deploy_attendance_app.conf.


# to run program in server AWS
1- Enter directory
- cd /var/www/html

2- Enter working folder
- cd face-recognition-insightface

3- Run project
- streamlit run Home.py
