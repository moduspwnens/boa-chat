"""PreWarmerFunction

Warms the Lambda functions as passed in via its own event.

Used with a timed CloudWatch event rule to allow an arbitrary number of 
functions to be prewarmed by a single event rule.

Default AWS limits allow a maximum of 10 CloudWatch event rules, each of 
which with a maximum of 5 targets.

"""

from __future__ import print_function

import json
import traceback
import boto3

lambda_client = boto3.client('lambda')
cloudformation_client = boto3.client('cloudformation')

def lambda_handler(event, context):
    print('Event: {}'.format(json.dumps(event)))
    
    functions_to_prewarm = []
    
    stack_id = event["stack-id"]
    
    response_iterator = cloudformation_client.get_paginator('list_stack_resources').paginate(
        StackName = stack_id
    )
    
    lambda_function_resources = []
    
    for each_response in response_iterator:
        resource_list = each_response.get("StackResourceSummaries", [])
        for each_resource in resource_list:
            if each_resource["ResourceType"] == "AWS::Lambda::Function":
                lambda_function_resources.append(each_resource)
    
    for each_resource in lambda_function_resources:
        response = cloudformation_client.describe_stack_resource(
            StackName = stack_id,
            LogicalResourceId = each_resource["LogicalResourceId"]
        )
        
        each_resource_summary = response["StackResourceDetail"]
        
        each_resource_metadata = {}
        try:
            each_resource_metadata = json.loads(each_resource_summary.get("Metadata", "{}"))
        except:
            pass
        
        if str(each_resource_metadata.get("PreWarming", "false")) == "true":
            functions_to_prewarm.append(each_resource["PhysicalResourceId"])
    
    for each_function_arn in functions_to_prewarm:
        
        try:
            lambda_client.invoke(
                FunctionName = each_function_arn,
                InvocationType = 'Event',
                Payload = json.dumps(event['payload'])
            )
            print('Invoked {} successfully.'.format(each_function_arn))
        except Exception as e:
            print(traceback.format_exc())
            print('Error invoking {}.'.format(each_function_arn))

    return {}