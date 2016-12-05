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

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    cognito_user_id = event.get("queryStringParameters", {}).get("registration-id", "")
    token = event.get("queryStringParameters", {}).get("token", "")
    
    if token == "":
        raise APIGatewayException("Value for \"token\" must be specified in URL.", 400)
    
    if cognito_user_id == "":
        raise APIGatewayException("Value for \"registration-id\" must be specified in URL.", 400)
    
    client_id = os.environ["COGNITO_USER_POOL_CLIENT_ID"]
    client_secret = os.environ["COGNITO_USER_POOL_CLIENT_SECRET"]
    
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
    
    
    
    return {
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