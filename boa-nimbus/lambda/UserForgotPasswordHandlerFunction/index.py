"""UserForgotPasswordHandlerFunction

Accepts "forgot password" requests.

"""

from __future__ import print_function

import os
import json
import boto3
import botocore
from apigateway_helpers.exception import APIGatewayException
from apigateway_helpers.headers import get_response_headers
from cognito_helpers import generate_cognito_sign_up_secret_hash

cognito_idp_client = boto3.client("cognito-idp")

def lambda_handler(event, context):
    
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    event["request-body"] = json.loads(event["body"])
    
    user_pool_client_id = os.environ["COGNITO_USER_POOL_CLIENT_ID"]
    user_pool_client_secret = os.environ["COGNITO_USER_POOL_CLIENT_SECRET"]
    
    email_address = event["request-body"].get("email-address", "")
    
    if email_address == "":
        raise APIGatewayException("Value for \"email-address\" must be specified in request body.", 400)
    
    secret_hash = generate_cognito_sign_up_secret_hash(email_address, user_pool_client_id, user_pool_client_secret)
    
    try:
        response = cognito_idp_client.forgot_password(
            ClientId = user_pool_client_id,
            SecretHash = secret_hash,
            Username = email_address
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'UserNotFoundException':
            raise APIGatewayException("User with e-mail address ({}) not found.".format(email_address), 404)
        else:
            raise
    
    return {
        "message": "Password reset code sent."
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