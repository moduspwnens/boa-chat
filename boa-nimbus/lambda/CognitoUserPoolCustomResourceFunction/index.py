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

max_user_pool_name_length = 128

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
            "PoolName": get_pool_name(event.get("LogicalResourceId")),
            "AliasAttributes": ["email"],
            "AutoVerifiedAttributes": ["email"],
            "LambdaConfig": resource_props.get("LambdaConfig", {}),
            "Policies": {
                "PasswordPolicy": resource_props.get("PasswordPolicy", default_password_policy_dict)
            },
            "AdminCreateUserConfig": {
                #"AllowAdminCreateUserOnly": True
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
        
        aws_region = context.invoked_function_arn.split(":")[3]
        aws_account_id = context.invoked_function_arn.split(":")[4]
        
        physical_resource_id = user_pool_id
        response_data["Id"] = user_pool_id
        response_data["Name"] = user_pool_name
        response_data["Arn"] = "arn:aws:cognito-idp:{aws_region}:{aws_account_id}:userpool/{user_pool_id}".format(
            aws_region = aws_region,
            aws_account_id = aws_account_id,
            user_pool_id = user_pool_id
        )
        response_data["ProviderName"] = "cognito-idp.{aws_region}.amazonaws.com/{user_pool_id}".format(
            aws_region = aws_region,
            user_pool_id = user_pool_id
        )
    
    
    cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, physical_resource_id)

    return {}

def get_pool_name(logical_resource_id):
    
    uuid_string = str(uuid.uuid4())
    
    max_resource_part_length = max_user_pool_name_length - len(os.environ["PROJECT_GLOBAL_PREFIX"]) - len(uuid_string) - 2
    
    return "{}-{}-{}".format(
        os.environ["PROJECT_GLOBAL_PREFIX"],
        logical_resource_id[0:max_resource_part_length],
        uuid_string
    )