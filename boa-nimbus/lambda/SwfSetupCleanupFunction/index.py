"""SwfSetupCleanupFunction

Creates SWF resources on stack creation and deletes them on stack deletion.

This is essentially a stub until CloudFormation supports these resources.

"""

from __future__ import print_function

import json
import boto3
import botocore
import cfnresponse

workflow_retention_days = 7
default_execution_timeout = 300

workflow_types = [
    {
        "name": "ChatRoom",
        "version": "1.0",
        "description": "Workflow for the lifecycle of a chat room",
        "defaultTaskStartToCloseTimeout": "NONE",
        "defaultExecutionStartToCloseTimeout": "{}".format(default_execution_timeout),
        "defaultTaskList": {
            "name": "tasklist1"
        },
        "defaultChildPolicy": "TERMINATE"
    }
]

swf_client = boto3.client('swf')

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    stack_id = event["StackId"]
    workflow_lambda_execution_role_arn = event["ResourceProperties"]["SwfWorkflowLambdaExecutionRoleArn"]
    swf_domain_name = get_swf_domain_name(stack_id)
    
    response_data = {
        "SwfDomainName": swf_domain_name,
        "SwfDomainArn": get_swf_domain_arn(stack_id)
    }

    request_type = event.get("RequestType")
    
    if request_type == "Create":
        create_swf_resources(swf_domain_name, workflow_lambda_execution_role_arn)
    elif request_type == "Delete":
        delete_swf_resources(swf_domain_name)

    cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, None)

    return {}

def create_swf_resources(domain_name, lambda_execution_role):
    
    print("Creating domain.")
    
    try:
        swf_client.register_domain(
            name = domain_name,
            workflowExecutionRetentionPeriodInDays = '{}'.format(workflow_retention_days)
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != 'DomainAlreadyExistsFault':
            raise
    
    for each_workflow_type_def in workflow_types:
        
        print("Creating workflow type: {}".format(each_workflow_type_def["name"]))
        
        new_workflow_type = each_workflow_type_def.copy()
        new_workflow_type["domain"] = domain_name
        new_workflow_type["defaultLambdaRole"] = each_workflow_type_def.get("defaultLambdaRole", lambda_execution_role)
        
        try:
            swf_client.register_workflow_type(**new_workflow_type)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] != 'TypeAlreadyExistsFault':
                raise
    
def delete_swf_resources(domain_name):
    try:
        swf_client.deprecate_domain(
            name = domain_name
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != 'DomainDeprecatedFault':
            raise

def get_swf_domain_name(stack_id):
    return "/".join(stack_id.split(":")[5].split("/")[1:])

def get_swf_domain_arn(stack_id):
    aws_region = stack_id.split(":")[3]
    aws_account_id = stack_id.split(":")[4]
    domain_name = get_swf_domain_name(stack_id)
    
    return "arn:aws:swf:{aws_region}:{aws_account_id}:/domain/{domain_name}".format(
        aws_region = aws_region,
        aws_account_id = aws_account_id,
        domain_name = domain_name
    )