"""StepFunctionStateMachineCustomResourceFunction

AWS CloudFormation Custom Resource for a Step Functions State Machine.

"""

from __future__ import print_function

import os
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
        
        on_delete_steps = resource_props.get("OnDelete", [])
        
        if "StopExecutions" in on_delete_steps:
            
            next_token = None
            
            while True:
                
                list_executions_kwargs = {
                    "stateMachineArn": state_machine_arn,
                    "statusFilter": "RUNNING"
                }
                
                if next_token is not None:
                    list_executions_kwargs["nextToken"] = next_token
                
                try:
                    response = sfn_client.list_executions(**list_executions_kwargs)
                except botocore.exceptions.ClientError as e:
                    if e.response['Error']['Code'] == 'StateMachineDoesNotExist':
                        print("State machine has no executions because it doesn't exist.")
                        break
                    else:
                        raise
                
                for each_execution in response.get("executions", []):
                    each_execution_arn = each_execution["executionArn"]
                    
                    print("Stopping execution: {}".format(each_execution_arn))
                    sfn_client.stop_execution(
                        executionArn = each_execution_arn,
                        error = "StateMachineDeletion",
                        cause = "The state machine performing this execution is pending deletion."
                    )
                
                if "nextToken" not in response:
                    break
                else:
                    next_token = response["nextToken"]
        
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
                print(response["status"])
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'StateMachineDoesNotExist':
                    break
                else:
                    raise
            
            time.sleep(5)
    
    if request_type in ["Create", "Update"]:
        
        state_machine_name = get_state_machine_name()
        
        definition_dict = json.loads(resource_props["Definition"])
        
        try:
            response = sfn_client.create_state_machine(
                name = state_machine_name,
                definition = json.dumps(definition_dict, indent=4),
                roleArn = resource_props["RoleArn"]
            )
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'InvalidDefinition':
                cfnresponse.send(event, context, cfnresponse.FAILED, {}, physical_resource_id)
            raise
        
        state_machine_arn = response["stateMachineArn"]
        
        physical_resource_id = state_machine_arn
        
        response_dict["StateMachineArn"] = state_machine_arn
        response_dict["StateMachineName"] = state_machine_name
        
        

    cfnresponse.send(event, context, cfnresponse.SUCCESS, response_dict, physical_resource_id)

    return {}

def get_state_machine_name():
    return "{}-{}".format(
        os.environ["PROJECT_GLOBAL_PREFIX"],
        "{}".format(
            uuid.uuid4()
        ).replace("-", "")
    )