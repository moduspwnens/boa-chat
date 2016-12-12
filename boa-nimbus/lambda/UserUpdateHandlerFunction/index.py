"""UserUpdateHandlerFunction

Updates a user's profile attributes.

"""

from __future__ import print_function

import os
import json
import boto3
import botocore
from apigateway_helpers.exception import APIGatewayException
from apigateway_helpers.headers import get_response_headers

cognito_idp_client = boto3.client("cognito-idp")

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    event["request-body"] = json.loads(event.get("body", "{}"))
    
    new_email_address = event["request-body"].get("email-address", "")
    
    if new_email_address == "":
        raise APIGatewayException("Value for \"email-address\" must be specified in request body.", 400)
    
    cognito_auth_provider_string = event["requestContext"]["identity"]["cognitoAuthenticationProvider"]
    cognito_idp_name = cognito_auth_provider_string.split(",")[0]
    user_pool_id = "/".join(cognito_idp_name.split("/")[1:])
    cognito_user_pool_sub_value = cognito_auth_provider_string.split(",")[1].split(":")[2]
    
    response = cognito_idp_client.list_users(
        UserPoolId = user_pool_id,
        AttributesToGet = [],
        Filter = "sub = \"{}\"".format(cognito_user_pool_sub_value),
        Limit = 1
    )
    
    cognito_user_pool_username = response["Users"][0]["Username"]
    
    cognito_idp_client.admin_update_user_attributes(
        UserPoolId = user_pool_id,
        Username = cognito_user_pool_username,
        UserAttributes = [
            {
                "Name": "email",
                "Value": new_email_address
            }
        ]
    )
    
    return {
        "registration-id": cognito_user_pool_username,
        "message": "E-mail address verification message sent."
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