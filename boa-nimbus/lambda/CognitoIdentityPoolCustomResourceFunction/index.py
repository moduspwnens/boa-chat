"""CognitoIdentityPoolCustomResourceFunction

Used as a CloudFormation custom resource representing a Cognito Identity Pool.

"""

from __future__ import print_function

import os
import json
import uuid
import cfnresponse
import boto3
import botocore

cognito_identity_client = boto3.client("cognito-identity")

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    request_type = event.get("RequestType")
    
    resource_props = event["ResourceProperties"]
    stack_name = event["StackId"].split(":")[5].split("/")[1]
    
    physical_resource_id = event.get("PhysicalResourceId")
    
    response_data = {}
    
    if request_type in ["Update", "Delete"]:
        
        identity_pool_id = physical_resource_id
            
        try:
            cognito_identity_client.delete_identity_pool(
                IdentityPoolId = identity_pool_id
            )
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise
    
    if request_type in ["Update", "Create"]:
        
        response = cognito_identity_client.create_identity_pool(
            IdentityPoolName = "{}_{}".format(
                os.environ["PROJECT_GLOBAL_PREFIX"],
                "{}".format(uuid.uuid4()).replace("-", "")
            ),
            AllowUnauthenticatedIdentities = False,
            CognitoIdentityProviders = resource_props.get("CognitoIdentityProviders", [])
        )
        
        identity_pool_id = response["IdentityPoolId"]
        identity_pool_name = response["IdentityPoolName"]
        
        aws_region = context.invoked_function_arn.split(":")[3]
        aws_account_id = context.invoked_function_arn.split(":")[4]
        
        physical_resource_id = identity_pool_id
        response_data["Id"] = identity_pool_id
        response_data["Name"] = identity_pool_name
        response_data["Arn"] = "arn:aws:cognito-identity:{aws_region}:{aws_account_id}:identitypool/{identity_pool_id}".format(
            aws_region = aws_region,
            aws_account_id = aws_account_id,
            identity_pool_id = identity_pool_id
        )
        response_data["SyncArn"] = "arn:aws:cognito-sync:{aws_region}:{aws_account_id}:identitypool/{identity_pool_id}".format(
            aws_region = aws_region,
            aws_account_id = aws_account_id,
            identity_pool_id = identity_pool_id
        )
    
    cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, physical_resource_id)

    return {}