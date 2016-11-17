"""CognitoUserPoolResourceFunction

Used as a CloudFormation custom resource to create / update / delete 
the Cognito User Pool.

"""

from __future__ import print_function

import json
import cfnresponse
import boto3

s3_client = boto3.client("s3")
cognito_client = boto3.client("cognito-idp")
cognito_user_pool_config_s3_key = "cognito-user-pool.json"

handler_object = None
def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    request_type = event.get("RequestType")
    
    resource_properties = event["ResourceProperties"]
    stack_name = event["StackId"].split(":")[5].split("/")[1]
    s3_bucket_name = resource_properties["SharedBucket"]
    
    response_data = {}
    
    if request_type in ["Create"]:
        
        create_user_pool_kwargs = {
            "PoolName": stack_name,
            "AliasAttributes": ["email"],
            "AutoVerifiedAttributes": ["email"],
            "LambdaConfig": {},
            "Policies": {
                "PasswordPolicy": {
                    "MinimumLength": 6,
                    "RequireUppercase": False,
                    "RequireLowercase": False,
                    "RequireNumbers": False,
                    "RequireSymbols": False
                }
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
        
        if "PostConfirmationTriggerFunctionArn" in resource_properties:
            create_user_pool_kwargs["LambdaConfig"]["PostConfirmation"] = resource_properties["PostConfirmationTriggerFunctionArn"]
        
        response = cognito_client.create_user_pool(**create_user_pool_kwargs)
        
        user_pool_id = response["UserPool"]["Id"]
        user_pool_name = response["UserPool"]["Name"]
        
        response = cognito_client.create_user_pool_client(
            UserPoolId = user_pool_id,
            ClientName = "default-web",
            GenerateSecret = True
        )
        
        user_pool_client_id = response["UserPoolClient"]["ClientId"]
        user_pool_client_name = response["UserPoolClient"]["ClientName"]
        user_pool_client_secret = response["UserPoolClient"]["ClientSecret"]
        
        s3_client.put_object(
            Bucket = s3_bucket_name,
            Key = cognito_user_pool_config_s3_key,
            Body = json.dumps({
                "id": user_pool_id,
                "name": user_pool_name,
                "client": {
                    "id": user_pool_client_id,
                    "name": user_pool_client_name,
                    "secret": user_pool_client_secret
                }
            }),
            ContentType = "application/json"
        )
        
        response_data["CognitoUserPoolId"] = user_pool_id
        response_data["CognitoUserPoolName"] = user_pool_name
        response_data["CognitoUserPoolClientId"] = user_pool_client_id
        response_data["CognitoUserPoolClientName"] = user_pool_client_name
        response_data["CognitoUserPoolClientSecret"] = user_pool_client_secret
        
    elif request_type == "Delete":
        
        response = s3_client.get_object(
            Bucket = s3_bucket_name,
            Key = cognito_user_pool_config_s3_key
        )
        
        user_pool_id = json.loads(response["Body"].read())["id"]
        
        cognito_client.delete_user_pool(
            UserPoolId = user_pool_id
        )
        
        s3_client.delete_object(
            Bucket = s3_bucket_name,
            Key = cognito_user_pool_config_s3_key
        )
    
    cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, None)

    return {}