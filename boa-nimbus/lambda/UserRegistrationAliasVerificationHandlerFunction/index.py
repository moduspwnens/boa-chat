"""UserRegistrationAliasVerificationHandlerFunction

Validates a user login verification token and returns an API key for the 
logged-in user.

"""

from __future__ import print_function

import os
import json
import uuid
import time
import base64
import random
import boto3
import botocore
from apigateway_helpers.exception import APIGatewayException
from apigateway_helpers.headers import get_response_headers
from cognito_helpers import generate_cognito_sign_up_secret_hash

s3_client = boto3.client("s3")
apig_client = boto3.client("apigateway")
cognito_idp_client = boto3.client("cognito-idp")
cognito_sync_client = boto3.client("cognito-sync")


def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    client_id = os.environ["COGNITO_USER_POOL_CLIENT_ID"]
    client_secret = os.environ["COGNITO_USER_POOL_CLIENT_SECRET"]
    user_profile_dataset_name = os.environ["COGNITO_USER_PROFILE_DATASET_NAME"]
    user_pool_id = os.environ["COGNITO_USER_POOL_ID"]
    
    
    token = ""
    
    try:
        token = event["queryStringParameters"]["token"]
    except:
        pass
    
    if token == "":
        raise APIGatewayException("Value for \"token\" must be specified in URL.", 400)
    
    cognito_user_id = None
    
    if event["resource"] == "/user/register/verify":
        # This is an unauthenticated request confirming a new user registration.
        
        cognito_user_id = event.get("queryStringParameters", {}).get("registration-id", "")
        
        if cognito_user_id == "":
            raise APIGatewayException("Value for \"registration-id\" must be specified in URL.", 400)
        
        try:
            cognito_idp_client.confirm_sign_up(
                ClientId = client_id,
                SecretHash = generate_cognito_sign_up_secret_hash(cognito_user_id, client_id, client_secret),
                Username = cognito_user_id,
                ConfirmationCode = token
            )
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'AliasExistsException':
                raise APIGatewayException("E-mail address already confirmed by another account.", 400)
            elif e.response['Error']['Code'] == 'NotAuthorizedException':
                raise APIGatewayException("Token provided is expired, invalid, or already used.", 400)
            elif e.response['Error']['Code'] == 'CodeMismatchException':
                raise APIGatewayException("Token provided is incorrect.", 400)
            elif e.response['Error']['Code'] == 'ExpiredCodeException':
                raise APIGatewayException("Invalid token provided. Please request another.", 400)
            raise
    
    elif event["resource"] == "/user/email/verify":
        
        cognito_auth_provider_string = event["requestContext"]["identity"]["cognitoAuthenticationProvider"]
        cognito_idp_name = cognito_auth_provider_string.split(",")[0]
        cognito_user_pool_sub_value = cognito_auth_provider_string.split(",")[1].split(":")[2]
        
        response = cognito_idp_client.list_users(
            UserPoolId = user_pool_id,
            AttributesToGet = [],
            Filter = "sub = \"{}\"".format(cognito_user_pool_sub_value),
            Limit = 1
        )
    
        cognito_user_id = response["Users"][0]["Username"]
        
        identity_id = event["requestContext"]["identity"]["cognitoIdentityId"]
        identity_pool_id = event["requestContext"]["identity"]["cognitoIdentityPoolId"]
        
        response = cognito_sync_client.list_records(
            IdentityPoolId = identity_pool_id,
            IdentityId = identity_id,
            DatasetName = user_profile_dataset_name
        )
        
        idp_credentials = None
        
        for each_record in response.get("Records", []):
            if each_record["Key"] == "idp-credentials":
                idp_credentials = json.loads(each_record["Value"])
                break
        
        if idp_credentials is None or idp_credentials.get("expires", 0) < int(time.time()):
            raise APIGatewayException("Identity provider credentials expired. Please log in and try again.", 400)
        
        access_token = idp_credentials["access-token"]
        
        try:
            cognito_idp_client.verify_user_attribute(
                AccessToken = access_token,
                AttributeName = "email",
                Code = token
            )
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'CodeMismatchException':
                raise APIGatewayException("Token provided is incorrect.", 400)
            elif e.response['Error']['Code'] == 'NotAuthorizedException':
                raise APIGatewayException("Token provided is expired, invalid, or already used.", 400)
            elif e.response['Error']['Code'] == 'ExpiredCodeException':
                raise APIGatewayException("Invalid token provided. Please request another.", 400)
            else:
                raise
    
    response = cognito_idp_client.admin_get_user(
        UserPoolId = user_pool_id,
        Username = cognito_user_id
    )
    
    new_user_email = None
    
    for each_attribute_pair in response.get("UserAttributes", []):
        if each_attribute_pair["Name"] == "email":
            new_user_email = each_attribute_pair["Value"]
            break
    
    if new_user_email is None:
        raise Exception("Unable to determine user's new e-mail address.")
    
    return {
        "email-address": new_user_email,
        "message": "E-mail address confirmed successfully."
    }

def proxy_lambda_handler(event, context):
    
    response_headers = get_response_headers(event, context)
    
    try:
        return_dict = lambda_handler(event, context)
    except APIGatewayException as e:
        return {
            "statusCode": e.http_status_code,
            "headers": response_headers,
            "body": json.dumps({
                "message": e.http_status_message
            })
        }
    
    return {
        "statusCode": 200,
        "headers": response_headers,
        "body": json.dumps(return_dict)
    }