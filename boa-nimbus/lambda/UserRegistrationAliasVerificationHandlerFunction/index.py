"""UserRegistrationAliasVerificationHandlerFunction

Validates a user login verification token and returns an API key for the 
logged-in user.

"""

from __future__ import print_function

import json
import uuid
import time
import base64
import random
import boto3
import botocore
from apigateway_helpers.exception import APIGatewayException
from cognito_helpers import generate_cognito_sign_up_secret_hash

s3_client = boto3.client("s3")
apig_client = boto3.client("apigateway")
cognito_client = boto3.client("cognito-idp")

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    user_id = event["request-params"]["querystring"].get("user-id", "")
    token = event["request-params"]["querystring"].get("token", "")
    
    if token == "":
        raise APIGatewayException("Value for \"token\" must be specified in URL.", 400)
    
    if user_id == "":
        raise APIGatewayException("Value for \"user-id\" must be specified in URL.", 400)
    
    client_id = event["cognito-user-pool-client-id"]
    client_secret = event["cognito-user-pool-client-secret"]
    
    try:
        cognito_client.confirm_sign_up(
            ClientId = client_id,
            SecretHash = generate_cognito_sign_up_secret_hash(user_id, client_id, client_secret),
            Username = user_id,
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