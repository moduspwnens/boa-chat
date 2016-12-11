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

lambda_client = boto3.client("lambda")

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    
    
    return {
        "message": "test message"
    }

def proxy_lambda_handler(event, context):
    
    response_headers = get_response_headers(event, context)
    print(response_headers)
    
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