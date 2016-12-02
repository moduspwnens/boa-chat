"""CognitoSharedResourceFunction

Used as a CloudFormation custom resource to create / update / delete:
 * Cognito Identity Pool
 * Cognito User Pool
 * Cognito User Pool Client (the API itself)

"""

from __future__ import print_function

import json
import os
import cfnresponse
import boto3
import botocore

s3_client = boto3.client("s3")
cognito_idp_client = boto3.client("cognito-idp")
cognito_identity_client = boto3.client("cognito-identity")

cognito_user_pool_config_s3_key = "cognito-user-pool.json"
cognito_identity_pool_config_s3_key = "cognito-identity-pool.json"

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
        
        response = cognito_idp_client.create_user_pool(**create_user_pool_kwargs)
        
        user_pool_id = response["UserPool"]["Id"]
        user_pool_name = response["UserPool"]["Name"]
        
        response = cognito_idp_client.create_user_pool_client(
            UserPoolId = user_pool_id,
            ClientName = "default-web",
            GenerateSecret = True,
            ExplicitAuthFlows = [
                "ADMIN_NO_SRP_AUTH"
            ]
        )
        
        user_pool_client_id = response["UserPoolClient"]["ClientId"]
        user_pool_client_name = response["UserPoolClient"]["ClientName"]
        user_pool_client_secret = response["UserPoolClient"]["ClientSecret"]
        
        response_data["CognitoUserPoolId"] = user_pool_id
        response_data["CognitoUserPoolName"] = user_pool_name
        response_data["CognitoUserPoolClientId"] = user_pool_client_id
        response_data["CognitoUserPoolClientName"] = user_pool_client_name
        response_data["CognitoUserPoolClientSecret"] = user_pool_client_secret
        
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
        
        response = cognito_identity_client.create_identity_pool(
            IdentityPoolName = stack_name,
            AllowUnauthenticatedIdentities = False,
            CognitoIdentityProviders = [
                {
                    "ProviderName": "cognito-idp.{aws_region}.amazonaws.com/{cognito_user_pool_id}".format(
                        aws_region = os.environ["AWS_DEFAULT_REGION"],
                        cognito_user_pool_id = user_pool_id
                    ),
                    "ClientId": user_pool_client_id
                }
            ]
        )
        
        identity_pool_id = response["IdentityPoolId"]
        identity_pool_name = response["IdentityPoolName"]
        
        response_data["CognitoIdentityPoolId"] = identity_pool_id
        response_data["CognitoIdentityPoolName"] = identity_pool_name
        
        s3_client.put_object(
            Bucket = s3_bucket_name,
            Key = cognito_identity_pool_config_s3_key,
            Body = json.dumps({
                "id": identity_pool_id,
                "name": identity_pool_name
            }),
            ContentType = "application/json"
        )
        
    elif request_type == "Delete":
        
        user_pool_id = None
        
        try:
            response = s3_client.get_object(
                Bucket = s3_bucket_name,
                Key = cognito_user_pool_config_s3_key
            )
            
            user_pool_id = json.loads(response["Body"].read())["id"]
            
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchKey':
                raise
        
        if user_pool_id is not None:
        
            try:
                cognito_idp_client.delete_user_pool(
                    UserPoolId = user_pool_id
                )
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    raise
        
            s3_client.delete_object(
                Bucket = s3_bucket_name,
                Key = cognito_user_pool_config_s3_key
            )
        
        identity_pool_id = None
        
        try:
            response = s3_client.get_object(
                Bucket = s3_bucket_name,
                Key = cognito_identity_pool_config_s3_key
            )
            
            identity_pool_id = json.loads(response["Body"].read())["id"]
            
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchKey':
                raise
                
        if identity_pool_id is not None:
            
            try:
                cognito_identity_client.delete_identity_pool(
                    IdentityPoolId = identity_pool_id
                )
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    raise
        
            s3_client.delete_object(
                Bucket = s3_bucket_name,
                Key = cognito_identity_pool_config_s3_key
            )
    
    cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, None)

    return {}