# dynamic-resource-management

## To Run & Test the Application Within EC2 Instance

## 1. Log in to EC

We are using AWS educate account. To avoid unexpected situations, username and passward are
mentioned in **credentials.txt** as well. Click AWS sign-in page to sign in to the console, and find
EC2 among all services.


```
AWS Management Console
```
**2. Start the instance**

After logging into the EC2 dashboard, click **Running Instances** in **resources** and choose the
instance named **Manager**. Choose **Actions → Instance State → Start** to start the instance.


```
The Manager Instance
```
**3.Connect to the instance using SSH**

The keypair is sent along with the documentation (named **keypair.pem** ). To connect to the
instance using SSH and a VNC Client,a detailed video tutorial is given here.

**4. Run the code using start.sh**

You can find a shell script named **start.sh** to initialize our web application, whose directory path
is

```
/home/ubuntu/Desktop
```
Use the commend line to run **start.sh** and start the application by typing:

**5. Test on load generator**

You can find a load generator named **gen.py** to initialize our web application, whose directory
path is

```
/home/ubuntu
```
To run the generator, run the python script using:

For example:

```
$ cd /home/ubuntu/Desktop
$ ./start.sh
```
```
python3.7 gen.py upload_url username password
upload_rate(upload_per_second) image_folder number_of_uploads
```

### To Use the Web Application

The whole application has been divided into two parts: Manger and User.

The manager controls the worker pool with the following functions:

1. Manager have access to the real time situation of the workers. With clicking on the detail
    button, manger can also watch the charts on CPU utilization and http requests of each
    worker.
2. Manager is able to change the worker size manually once a time either adding or shrinking.
3. A strategy called auto-scaling can be used to changing the number of the workers to make
    sure that CPU and ratio would stay in the range which manager sets.
4. Manager can be stopped and all user applications can be destroyed on the main page.

User web application running on each worker is substantially an album, which allows you to
register, log in and out, as well as upload photos. Our application will save your uploaded photo
as well as its thumbnail and result of text-detection, which is a new photo with green rectangle
around texts. When you go into your own album, you will see thumbnails of all your uploaded
photos. Click on one of them to see the origin photo, thumbnail and result of text-detection.

Detailed directions are shown below with sample screenshots.

## Demonstration on the UI

### 1 Manager app:

**Main Page:**

```
python3.7 gen.py http://9.9.9.9:5000/api/upload user pass 1 ./my-photos/
100
```

This main page shows all functions and information of manager. Manager can use the buttons to
control the workers so that to reach the balance.

This page is set to refresh every 1 minute to update the real time situation of workers.

Instance information shows the id,type,availablitity zone and status of all current ec2 worker
instances.

We use increase and decrease to manually change the worker pool size.


By changing the threshold and ratio of the cpu we can obeserve the terminal so that the workers
change will be clearly showed. We also have some notation like "CPU Average is within operating
window" or "lower" or "greater than threshold". Every minute the autoscaler will check the cpu
utilization.

**Details:**

Click on detail we can get the two kind of information of the worker in past 30 minutes: average
of cpu utilization and number of http requests. This page is also set to refresh every 1 minute to
get the real time information of cpu utilization and request count chart.


```
instance info
```
**e.g.**

### !

### User app:

**Visit the Webpage**


```
Welcome Page
```
```
Login&Register Page
```
In order to make load balancer work, when using user-app, we should open the browser and
enter the load balancer's DNS name as shown in manager UI **load balancer's DNS + :5000** to
access the welcome page.

**Register or Login**

Click on **"Login&Register"** to either login your previous account or create a new account. Also,
you can simply put mouse on **"Login&Register"** and choose from the drop-down menu.

**Upload Photos**

After successfully logged in, you will be automatically redirected to the upload page. Follow the
instructions to upload your photo once a time. Notice that the format is restricted to **.png** , **.jpg**
and **.jpeg**. Also, your photo can not be bigger than **100MB**.


```
Upload Page
```
```
Success Message
```
```
Album
```
After uploading, your photo will be saved, as well as its thumbnail and result of text-detection.
After going through all these steps, it will return a message to show that you have successfully
uploaded a photo. You can choose to upload more photos or click on **album** to view your
previous photos in thumbnail.

**Album**

Your album is somewhere that contains all your uploaded photos. Instead of origin photos, the
page shows thumbnails.


```
Show a Photo Transformation
```
Click on a thumbnail, and you will get a new page for the origin photo, thumbnail and result of
text-detection, which draws green rectangles around texts.

**Log Out**

You can log out at any time by clicking **logout**. However, neither upload nor album function can
be used without logging in.

## Results

To demonstrate the functionality of our auto-scaling algorithm and it’s reliability as load increases
and decreases, we designed some cases to test its relaibility.

In order to simulate the load when user-app is working, we use the stress tool to increase the
load of cpu. https://www.howtoing.com/linux-cpu-load-stress-test-with-stress-ng-tool/

**case 1**

```
input autoscale policy :
CPU High Threshold 75
CPU Low Threshold 25
Ratio Up 2
Ratio Down 2
```

We can watch the screenshots clearly that with the change of cpu utilization the workers change
by autoscale policy so that it keeps the cpu in the range we set. First from 1 to 2 ,then from 2 to 1
(circled in the picture above). To clearly show the relationship between average CPU utilization
,CPU threshold and number of worker pools, we drew chart using MATLAB as below.


From the chart, we can say that the auto-scaling algorithm is reliable as load increases and
decreases. Also, when load is within the range, the number of worker pool is stable.

**case 2**

In another test case, since it is difficult to keep loading in a high rate, we set small upperbound to
test the auto increasing and decreasing of worker pools.

```
input autoscale policy :
CPU High Threshold : 5
CPU Low Threshold : 1
Ratio Up : 2
Ratio Down : 2
```

## Developer's Reference

### General Architecture of the Project


----Manger
├── app
│ ├── __init__.py
│ ├── config.py #store parameters of configure
│ ├── db
│ │ ├── addautoscaling.sql
│ │ ├── manager.mwb
│ ├── elb_op.py #loadbalancer operations
│ ├── main.py #main function of manager UI
│ ├── templates
│ │ ├── base.html #base template of manager UI
│ │ ├── ec2_examples
│ │ │ ├── list.html #webpage to display the main page of manager UI
│ │ │ └── view.html #webpage to display the information of individual
workers
│ └── worker_op.py #operations to workers
└── run.py

----User\
|----gen.py # load generator
|----run.py # run the web application
|----db\ # database
| |----create_table.sql
|----app\ # main application
| |----static\ # a static path to store photos in the local system
| |----templates\ # HTML templates
| | |----base.html
| | |----show.html
| | |----album.html
| | |----register.html
| | |----user.html
| | |----login.html
| | |----view.html
| | |----welcome.html
| | |----upload.html
| |----__init__.py
| |----main.py # the initial function
| |----config.py # database configuration
| |----user_op_data.py # functions related to database
| |----user_op.py # functions related to register & log in
| |----upload.py # functions related to photo uploading and saving
| |----view.py # functions related to photo showing
| |----suppression.py # the pre-trained EAST text detector
| |----frozen_east_text_detection.pb # text detector

----autoscale\
|----autoscale.py #main function in autoscale
|----config.py
|----elb_op.py #function with load balancer


### Important functions in python files

### Manager:

**main.py**

```
get_requests_per_minute():
get and fliter the needed data from database, and calcutate the number of requests in
a selected period of time and a particular instance
ec2_view(id):
get and show all EC2 instances presented
ec2_create():
create new EC2 instances
ec2_destroy(id):
shutdown EC2 instances
scaling_modified():
get the scaling policy
config_scaling:
store the policy in database
increase1():
manually create a new EC2 instance
decrease1():
manually shutdown a new EC2 instance
delete_all_worker:
terminates all workers and shutdown the manager
```
**autoscale.py**

```
change_instances_number():
change instances number with the setting autoscale policy applying add workers and
delete workers to make sure that the cpu utilization in the range
add workers(add_instances):
create worker instances in ec
delete workers(delete_instances):
shutdown worker instances in ec
```
**elb_op.py**

```
elb_add_instance(instance_id) & elb_delete_instance(instance_id):
add instance and delete instances from load balancer
```
**worker_op.py**

```
increase_worker_nodes(add_instances):
create worker instances in ec
decrease_worker_nodes(delete_instances):
```

```
shutdown worker instances in ec
```
### User:

We define a function **record_requests** and call it after each webapp.route to record every HTTP
request that occurs.

**user_op.py**

```
login() :
set information for username and error message of login interface
return login.html template to display the login form
login_submit() :
judge if username and password are in the form
compare user information with the information in the database
when login succussed, redirect to url for disphoto function
when login failed, redirect to url for login function with error message
register() :
set information of username and error message in register interface
return register.html template to display the register form
register_submit() :
judge if all information is in the form
judge if the username to be registered is invalid(more than 100 characters, or duplicate
username)
judge if two passwords are different
save valid information into database
when register successed, return url for login() with success message
when register failed, return url for register() with error message
logout() :
clear all session information
disPhoto() :
set error message if the message exists
redirect url for disphoto, which is the main inferface of upload photos and display
photos
```
**upload.py**

```
upload():
save the uploaded file in a certain path
generate and save the thumbnail of original file using PIL
generate and save the result of text-detction using OpenCV
save the paths in database
return "Upload successed!"
showphoto(filename):
select a certain row in database according a certain path of thumbnail
```
**view.py**


```
Flow Chart
```
```
view():
select path of all thumbnails corresponding to the username of the authorized user,
and pass it to view.html
```
**Flow Chart**

## Database Schema


```
Database Schema
```
There are four tables:

```
user_information table includes three columns:
user_id: unique id for every user, basiclly is the num+1 when new user is registering,
primary key
username: information for username
password: salted password saved in the password column
image table inculdes four columns:
user_id: in order to conncet to table user_information, primary key
origin_path: file path for original photos
thumb_path: file path for thumbnails
text_path: file path for photos after text-detction process
autoscale table is used for the storage of autoscale policies, and inculdes six columns:
id: the unique id for every different police, primary key
scale: the status of autoscaling function. It can be either 'ON' or 'OFF'
upper_bound: the upper bound of CPU threshold (average for all workers over past 2
minutes) for growing the worker pool
lower_bound: the lower bound of CPU threshold (average for all workers over past 2
minutes) for shrinking the worker pool
scale_up: the ratio by which to expand the worker pool
scale_down: the ratio by which to shrink the worker pool
requestperminute table is used for the storage of each HTTP request, and has three tables:
requestid: the unique id for every request, primary key. We set it automatically increase
to count the number of total request
instanceid: the unique id for each instance where the requests belong, used to fliter the
```

```
results
timestamp: the unique timestamp for each request, used to fliter the results
```
Copyright 2019, Nianchong Wu & Jingwen Zhang & Yiyun Xu. Created using Markdown
