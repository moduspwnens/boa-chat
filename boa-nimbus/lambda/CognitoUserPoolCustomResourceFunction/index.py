"""CognitoUserPoolCustomResourceFunction

Used as a CloudFormation custom resource representing a Cognito User Pool.

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
    
    physical_resource_id = event.get("PhysicalResourceId")
    
    response_data = {}
    
    if request_type in ["Update", "Delete"]:
        
        user_pool_id = physical_resource_id
    
        try:
            cognito_idp_client.delete_user_pool(
                UserPoolId = user_pool_id
            )
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise
    
    if request_type in ["Update", "Create"]:
        
        default_password_policy_dict = {
            "MinimumLength": 6,
            "RequireUppercase": False,
            "RequireLowercase": False,
            "RequireNumbers": False,
            "RequireSymbols": False
        }
        
        create_user_pool_kwargs = {
            "PoolName": "{}-{}".format(
                os.environ["PROJECT_GLOBAL_PREFIX"],
                uuid.uuid4()
            ),
            "AliasAttributes": ["email"],
            "AutoVerifiedAttributes": ["email"],
            "LambdaConfig": {},
            "Policies": {
                "PasswordPolicy": resource_props.get("PasswordPolicy", default_password_policy_dict)
            },
            "Schema": [
                {
                    "Name": "email",
                    "AttributeDataType": "String",
                    "StringAttributeConstraints": {
                        "MinLength": "3",
                        "MaxLength": "2048"
                    },
                    "DeveloperOnlyAttribute": False,
                    "Mutable": True,
                    "Required": True
                },
                {
                    "Name": "email_verified",
                    "AttributeDataType": "Boolean",
                    "DeveloperOnlyAttribute": False,
                    "Mutable": True,
                    "Required": False
                },
                {
                    "Name": "updated_at",
                    "AttributeDataType": "Number",
                    "NumberAttributeConstraints": {
                        "MinValue": "0"
                    },
                    "DeveloperOnlyAttribute": False,
                    "Mutable": True,
                    "Required": False
                }
            ]
        }
        
        if "PostConfirmationTriggerFunctionArn" in resource_props:
            create_user_pool_kwargs["LambdaConfig"]["PostConfirmation"] = resource_props["PostConfirmationTriggerFunctionArn"]
        
        response = cognito_idp_client.create_user_pool(**create_user_pool_kwargs)
        
        user_pool_id = response["UserPool"]["Id"]
        user_pool_name = response["UserPool"]["Name"]
        
        physical_resource_id = user_pool_id
        response_data["Id"] = user_pool_id
        response_data["Name"] = user_pool_name
    
    
    cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, physical_resource_id)

    return {}