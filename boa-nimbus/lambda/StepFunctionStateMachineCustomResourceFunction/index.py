"""StepFunctionStateMachineCustomResourceFunction

AWS CloudFormation Custom Resource for a Step Functions State Machine.

"""

from __future__ import print_function

import json
import uuid
import time
import boto3
import botocore
import cfnresponse

sfn_client = boto3.client('stepfunctions')

def lambda_handler(event, context):
    print('Event: {}'.format(json.dumps(event)))
    
    request_type = event.get("RequestType")
    resource_props = event["ResourceProperties"]
    
    stack_id = event["StackId"]
    stack_name = stack_id.split(":")[5].split("/")[1]
    
    physical_resource_id = event.get("PhysicalResourceId")
    
    response_dict = {}
    
    if request_type in ["Update", "Delete"]:
        state_machine_arn = physical_resource_id
        
        sfn_client.delete_state_machine(
            stateMachineArn = state_machine_arn
        )
    
    if request_type == "Update":
        state_machine_arn = physical_resource_id
        
        print("Waiting for state machine to be deleted.")
        
        while True:
            try:
                response = sfn_client.describe_state_machine(
                    stateMachineArn = state_machine_arn
                )
                print(response)
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'StateMachineDoesNotExist':
                    break
                else:
                    raise
    
    if request_type in ["Create", "Update"]:
        
        state_machine_name = get_state_machine_name(stack_name)
        
        definition_dict = json.loads(resource_props["Definition"])
        
        response = sfn_client.create_state_machine(
            name = state_machine_name,
            definition = json.dumps(definition_dict),
            roleArn = resource_props["RoleArn"]
        )
        
        state_machine_arn = response["stateMachineArn"]
        
        physical_resource_id = state_machine_arn
        
        response_dict["StateMachineArn"] = state_machine_arn
        response_dict["StateMachineName"] = state_machine_name
        
        

    cfnresponse.send(event, context, cfnresponse.SUCCESS, response_dict, physical_resource_id)

    return {}

def get_state_machine_name(stack_name):
    return "{}-{}".format(
        stack_name,
        "{}".format(
            uuid.uuid4()
        ).replace("-", "")
    )