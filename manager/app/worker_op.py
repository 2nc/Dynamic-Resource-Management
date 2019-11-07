import boto3
from app import config, elb_op
from datetime import datetime, timedelta


def increase_worker_nodes(add_instances):
    ec2 = boto3.resource('ec2')

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

    return 'OK'


def decrease_worker_nodes(delete_instances):
    if delete_instances == 0:
        print("Cant delete anymore")
        return

    print("Going to delete %d" % delete_instances)

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

    print("Instances:")
    print(instances_ids)
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