import boto3
import config, elb_op
import mysql.connector
from datetime import datetime, timedelta
import time

def change_instances_number():
    # Open DB Connection
    cnx = mysql.connector.connect(user=config.db_config['user'], password=config.db_config['password'],
                                  host=config.db_config['host'],
                                  database=config.db_config['database'])
    cursor = cnx.cursor()

    # Query DB for Autoscale settings
    cursor.execute("SELECT scale,upper_bound,lower_bound,scale_up,scale_down FROM autoscale WHERE id = 1")
    auto_scale_data = cursor.fetchall()

    if (len(auto_scale_data) == 0):
        print("Database is missing autoscale data")
        return False

    for scale, upper_bound, lower_bound, scale_up, scale_down in auto_scale_data:
        AUTO_SCALE = scale
        AUTO_UPPER_BOUND = upper_bound
        AUTO_LOWER_BOUND = lower_bound
        AUTO_SCALE_UP = scale_up
        AUTO_SCALE_DOWN = scale_down

    print("AUTO PARAMS: %s %s %s %s %s" % (
        AUTO_SCALE, AUTO_UPPER_BOUND, AUTO_LOWER_BOUND, AUTO_SCALE_UP, AUTO_SCALE_DOWN))
    # Close DB Connection
    cursor.close()
    cnx.close()

    # Create EC2 Resource
    ec2 = boto3.resource('ec2')

    # Get All EC2 Instances
    instances = ec2.instances.all()

    instances_ids = []
    for instance in instances:
        if ((instance.state['Name'] != 'terminated') and (instance.state['Name'] != 'shutting-down')) and (
                instance.tags[0]['Value'] == 'work'):
            instances_ids.append(instance.id)

    # testing
    print(instances_ids)

    avgs = []
    n_instances = 0

    # Get minute avg CPU utilization for every worker instance
    for id in instances_ids:
        instance = ec2.Instance(id)
        client = boto3.client('cloudwatch')
        metric_name = 'CPUUtilization'
        namespace = 'AWS/EC2'
        statistic = 'Average'  # could be Sum,Maximum,Minimum,SampleCount,Average

        cpu = client.get_metric_statistics(
            Period=2 * 60,
            StartTime=datetime.utcnow() - timedelta(seconds=2 * 60),
            EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
            MetricName=metric_name,
            Namespace=namespace,  # Unit='Percent',
            Statistics=[statistic],
            Dimensions=[{'Name': 'InstanceId', 'Value': id}]
        )

        datapoints = cpu['Datapoints']
        if datapoints:
            data = datapoints[0]
            average = data["Average"]
            avgs.append(average)
        n_instances = n_instances + 1

    sum_avg = 0
    for avg in avgs:
        sum_avg = sum_avg + avg

    if n_instances:
        instances_average = sum_avg / n_instances
    else:
        instances_average = 0
    print("cpu utilization avg:%f" % instances_average)

    if (AUTO_SCALE == 'ON' and n_instances >= 1):
        if instances_average >= AUTO_UPPER_BOUND: #cpu_avg
            print("CPU Average is greater than threshold.")
            print("Increasing nodes from %d to %f" % (n_instances, min(10, n_instances * AUTO_SCALE_UP)))
            add_workers(min(int(n_instances * AUTO_SCALE_UP), 10) - n_instances)
        elif instances_average <= AUTO_LOWER_BOUND:
            print("CPU Average is lower than threshold.")
            print("Decreasing nodes from %d to %d" % (n_instances, max(int(n_instances / AUTO_SCALE_DOWN), 1)))
            delete_workers(n_instances - max(int(n_instances / AUTO_SCALE_DOWN), 1))
        else:
            print("CPU Average is within operating window. Total Workers %d" % (n_instances))



def add_workers(add_instances):
    ec2 = boto3.resource('ec2')
    if add_instances == 0:
        print("Cannot create more worker")
        return "fail"
    new_instances = ec2.create_instances(ImageId=config.ami_id,
                                         MinCount=add_instances,
                                         MaxCount=add_instances,
                                         UserData=config.EC2_userdata,
                                         InstanceType=config.EC2_instance,
                                         KeyName=config.EC2_keyName,
                                         SecurityGroupIds=config.EC2_security_group_id,
                                         Monitoring={'Enabled': config.EC2_monitor},
                                         TagSpecifications=[{'ResourceType': 'instance', 'Tags': [
                                             {'Key': config.EC2_target_key, 'Value': config.EC2_target_value}, ]}, ])

    for instance in new_instances:
        elb_op.elb_add_instance(instance.id)  # Add New Instance to ELB
    print ("create worker done")
    return 'OK'


def delete_workers(delete_instances):
    if delete_instances == 0:
        print("Cannot delete anymore for minimun worker is 1")
        return

    print("Going to delete %d workers to save resource" % delete_instances)

    # Create EC2 Resource
    ec2 = boto3.resource('ec2')

    # Get All EC2 Instances
    instances = ec2.instances.all()

    # Test CloudWatch avgs
    instances_ids = []
    for instance in instances:
        if ((instance.tags[0]['Value'] == 'work') and (
                (instance.state['Name'] != 'terminated') and (instance.state['Name'] != 'shutting-down'))):
            instances_ids.append(instance.id)

    avgs = []
    n_instances = 0

    # Get minute avg CPU utilization for every worker instance
    for id in instances_ids:
        instance = ec2.Instance(id)
        client = boto3.client('cloudwatch')
        metric_name = 'CPUUtilization'
        namespace = 'AWS/EC2'
        statistic = 'Average'  # could be Sum,Maximum,Minimum,SampleCount,Average

        cpu = client.get_metric_statistics(
            Period=2 * 60,
            StartTime=datetime.utcnow() - timedelta(seconds=2 * 60),
            EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
            MetricName=metric_name,
            Namespace=namespace,  # Unit='Percent',
            Statistics=[statistic],
            Dimensions=[{'Name': 'InstanceId', 'Value': id}]
        )

        datapoints = cpu['Datapoints']
        if datapoints:
            data = datapoints[0]
            average = data["Average"]
            avgs.append(average)
        n_instances = n_instances + 1

    print("Averages:")
    print(avgs)

    # Sort Instances by CPU Averages in Non-Increasing order
    X = instances_ids
    Y = avgs

    Z = [x for _, x in sorted(zip(Y, X))]
    print("Sorted:")
    print(Z)

    # Delete Necessary Instances by Non-Increasing CPU Average order
    for i in range(0, delete_instances):
        del_instances = ec2.instances.filter(InstanceIds=[Z[i]])
        for instance in del_instances:
            elb_op.elb_remove_instance(instance.id)  # Remove Instance from ELB
            instance.terminate()  # Terminate Instance

# EXECUTE AUTOSCALE every 1 minutes
wait_time = 60
#First we set if to be ture to run function
end_loop_time = time.time() + wait_time
while True:
    current_time = time.time()
    if current_time > end_loop_time:
        end_loop_time = time.time() + wait_time
        change_instances_number()
    print("rest for a while for next autoscale judgement")
    time.sleep(10)
    
