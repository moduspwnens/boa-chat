"""UserLoginResponseHandlerFunction

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
import zbase32
from apigateway_helpers.exception import APIGatewayException

max_login_request_age_seconds = 900 # 900 seconds = 15 minutes

s3_client = boto3.client("s3")
apig_client = boto3.client("apigateway")

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    raise Exception("Test message")
    
    login_token = event["request-params"]["querystring"].get("token", "")
    
    if login_token == "":
        raise APIGatewayException("Value for \"token\" must be specified in message.", 400)
    
    s3_bucket_name = event["shared-bucket"]
    
    try:
        response = s3_client.get_object(
            Bucket = s3_bucket_name,
            Key = "login-requests/{}.json".format(login_token)
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise APIGatewayException("Login request token not found.", 404)
        raise
            
    login_request_object = json.loads(response["Body"].read())
    
    email_address = login_request_object["email-address"]
    request_age = int(time.time()) - login_request_object["created"]
    
    if request_age > max_login_request_age_seconds:
        raise APIGatewayException("Login request token age ({} seconds) exceeds maximum allowable ({} seconds).".format(
            request_age,
            max_login_request_age_seconds
        ), 400)
    
    user_id = None
    
    email_address_encoded = base64.b64encode(email_address)
    
    try:
        response = s3_client.get_object(
            Bucket = s3_bucket_name,
            Key = "user-email-addresses/{}.json".format(email_address_encoded)
        )
        
        user_id = json.loads(response["Body"].read())["user-id"]
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != 'NoSuchKey':
            raise
        
        generated_user_id = "{}".format(uuid.uuid4())
        
        s3_client.put_object(
            Bucket = s3_bucket_name,
            Key = "user-email-addresses/{}.json".format(email_address_encoded),
            Body = json.dumps({
                "user-id": generated_user_id
            }),
            ContentType = "application/json"
        )
        
        user_id = generated_user_id
    
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
            event["stack-name"],
            email_address
        )
        
        response = apig_client.create_api_key(
            name = api_key_name,
            description = "Web chat API key for {}.".format(email_address),
            enabled = True,
            value = generated_api_key
        )
        
        user_api_key_id = response["id"]
        
        response = apig_client.create_usage_plan_key(
            usagePlanId = event["usage-plan-id"],
            keyId = user_api_key_id,
            keyType = "API_KEY"
        )
        
        s3_client.put_object(
            Bucket = s3_bucket_name,
            Key = "api-key-user/{}.json".format(user_api_key_id),
            Body = json.dumps({
                "user-id": user_id
            }),
            ContentType = "application/json"
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
    
    
    s3_client.delete_object(
        Bucket = s3_bucket_name,
        Key = "login-requests/{}.json".format(login_token)
    )
    
    return {
        "api-key": user_api_key_value,
        "email-address": email_address,
        "user-id": user_id
    }

def generate_potential_api_key():
    # API key must be at least 30 characters.
    base_key = zbase32.b2a(uuid.uuid4().bytes)
    
    filler_content = "".join(random.sample(base_key, len(base_key)))
    
    return (zbase32.b2a(uuid.uuid4().bytes) + filler_content)[:30]