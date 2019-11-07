import boto3


def elb_add_instance(instance_id):

    elbList = boto3.client('elb')

    # Adding instances to ELB:
    response = elbList.register_instances_with_load_balancer(
        LoadBalancerName='A2loadbalance',
        Instances=[
            {
                'InstanceId': instance_id
            },
        ]
    )
    print(response)


def elb_remove_instance(instance_id):

    elb_list = boto3.client('elb')

    # Removing instance from ELB:
    response = elb_list.deregister_instances_from_load_balancer(
        LoadBalancerName='A2loadbalance',
        Instances=[
            {
                'InstanceId':  instance_id
            },
        ]
    )
    print(response)
