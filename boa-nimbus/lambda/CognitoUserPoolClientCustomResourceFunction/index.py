"""CognitoUserPoolClientCustomResourceFunction

Used as a CloudFormation custom resource representing a Cognito User Pool 
client.

"""

from __future__ import print_function

import os
import json
import uuid
import cfnresponse
import boto3
import botocore

cognito_idp_client = boto3.client("cognito-idp")

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    request_type = event.get("RequestType")
    
    resource_props = event["ResourceProperties"]
    user_pool_id = resource_props.get("UserPoolId")
    
    physical_resource_id = event.get("PhysicalResourceId")
    
    response_data = {}
    
    if request_type in ["Update", "Delete"]:
    
        try:
            cognito_idp_client.delete_user_pool_client(
                UserPoolId = user_pool_id,
                ClientId = physical_resource_id
            )
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise
    
    if request_type in ["Update", "Create"]:
        
        response = cognito_idp_client.create_user_pool_client(
            UserPoolId = user_pool_id,
            ClientName = "{}-{}".format(
                os.environ["PROJECT_GLOBAL_PREFIX"],
                uuid.uuid4()
            ),
            GenerateSecret = True,
            ExplicitAuthFlows = [
                "ADMIN_NO_SRP_AUTH"
            ]
        )

        user_pool_client_id = response["UserPoolClient"]["ClientId"]
        user_pool_client_name = response["UserPoolClient"]["ClientName"]
        user_pool_client_secret = response["UserPoolClient"]["ClientSecret"]
        
        physical_resource_id = user_pool_client_id
        response_data["Id"] = user_pool_client_id
        response_data["Name"] = user_pool_client_name
        response_data["Secret"] = user_pool_client_secret
    
    cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, physical_resource_id)

    return {}