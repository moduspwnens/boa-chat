"""UserApiKeyResetHandlerFunction

Resets a user's API key value to a new one.

"""

from __future__ import print_function

import os
import json
import boto3
import botocore
from apigateway_helpers.exception import APIGatewayException
from apigateway_helpers.headers import get_response_headers

lambda_client = boto3.client("lambda")

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    api_key_generator_function_arn = os.environ["API_KEY_CREATOR_FUNCTION_ARN"]
    identity_id = event["requestContext"]["identity"]["cognitoIdentityId"]
    
    response = lambda_client.invoke(
        FunctionName = api_key_generator_function_arn,
        Payload = json.dumps({
            "identity-id": identity_id
        })
    )
    
    response_object = json.loads(response["Payload"].read())
    
    api_key_value = response_object.get("api-key-value")
    
    if api_key_value is None:
        print(json.dumps(response_object))
        raise Exception("Unexpected response from API Key creator function.")
    
    return {
        "api-key": api_key_value
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