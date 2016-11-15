"""UserCredentialsGeneratorFunction

Generates temporary IAM credentials for a user based on the given API key.

"""

from __future__ import print_function

import json
import boto3
import botocore
from apigateway_helpers.exception import APIGatewayException

s3_client = boto3.client("s3")

api_key_user_id_map = {}

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    s3_bucket_name = event["shared-bucket"]
    
    user_id = get_user_id_for_api_key(s3_bucket_name, event["api-key"])
    
    return {
        "user-id": user_id
    }

def get_user_id_for_api_key(s3_bucket_name, api_key):
    
    if api_key in api_key_user_id_map:
        return api_key_user_id_map[api_key]
    
    try:
        response = s3_client.get_object(
            Bucket = s3_bucket_name,
            Key = "api-key-user/{}.json".format(
                api_key
            )
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != 'NoSuchKey':
            raise
        raise APIGatewayException("Invalid API Key.", 403)
    
    api_key_user_config = json.loads(response["Body"].read())
    
    user_id = api_key_user_config["user-id"]
    
    api_key_user_id_map[api_key] = user_id
    
    return user_id