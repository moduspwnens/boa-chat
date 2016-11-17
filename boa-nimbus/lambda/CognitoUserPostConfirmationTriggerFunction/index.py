"""CognitoUserPostConfirmationTrigger

Called when a new user is confirmed.

"""

from __future__ import print_function

import json
import random
import uuid
import boto3
import botocore
import zbase32
from project_local import get_own_cloudformation_metadata

s3_client = boto3.client("s3")
apig_client = boto3.client("apigateway")

function_metadata = get_own_cloudformation_metadata("CognitoUserPostConfirmationTriggerFunction")

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    s3_bucket_name = function_metadata["SharedBucket"]
    stack_name = function_metadata["StackName"]
    usage_plan_id = function_metadata["UsagePlanId"]
    
    user_id = event["userName"]
    email_address = event["request"]["userAttributes"]["email"]
    
    user_api_key_value = None
    user_api_key_id = None
    
    try:
        response = s3_client.get_object(
            Bucket = s3_bucket_name,
            Key = "user-api-keys/{}.json".format(user_id)
        )
        
        user_api_key_object = json.loads(response["Body"].read())
        
        user_api_key_value = user_api_key_object["api-key-value"]
        user_api_key_id = user_api_key_object["api-key-id"]
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != 'NoSuchKey':
            raise
        
        generated_api_key = generate_potential_api_key()
        
        api_key_name = "{} - {}".format(
            stack_name,
            email_address
        )
        
        response = apig_client.create_api_key(
            name = api_key_name,
            description = "Web chat API key for {}.".format(email_address),
            enabled = True,
            value = generated_api_key
        )
        
        user_api_key_id = response["id"]
        user_api_key_value = response["value"]
        
        response = apig_client.create_usage_plan_key(
            usagePlanId = usage_plan_id,
            keyId = user_api_key_id,
            keyType = "API_KEY"
        )
        
        s3_client.put_object(
            Bucket = s3_bucket_name,
            Key = "user-api-keys/{}.json".format(user_id),
            Body = json.dumps({
                "api-key-id": user_api_key_id,
                "api-key-value": generated_api_key
            }),
            ContentType = "application/json"
        )
        
        user_api_key_value = generated_api_key
    
    return event

def generate_potential_api_key():
    # API key must be at least 30 characters.
    base_key = zbase32.b2a(uuid.uuid4().bytes)
    
    filler_content = "".join(random.sample(base_key, len(base_key)))
    
    return (zbase32.b2a(uuid.uuid4().bytes) + filler_content)[:30]