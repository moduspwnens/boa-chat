from __future__ import print_function

import json
import uuid
import zbase32
import random
import boto3
import botocore

def generate_potential_api_key():
    # API key must be at least 30 characters.
    base_key = zbase32.b2a(uuid.uuid4().bytes)
    
    filler_content = "".join(random.sample(base_key, len(base_key)))
    
    return (zbase32.b2a(uuid.uuid4().bytes) + filler_content)[:30]

def create_api_key_for_user_if_not_exists(user_id, email_address, user_pool_id, stack_name, usage_plan_id, s3_bucket_name):
    
    s3_client = boto3.client("s3")
    apig_client = boto3.client("apigateway")
    cognito_idp_client = boto3.client("cognito-idp")
    
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
        
        cognito_idp_client.admin_update_user_attributes(
            UserPoolId = user_pool_id,
            Username = user_id,
            UserAttributes = [
                {
                    "Name": "custom:api_key",
                    "Value": generated_api_key
                }
            ]
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
    
    return user_api_key_value