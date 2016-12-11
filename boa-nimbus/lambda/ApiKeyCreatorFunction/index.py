"""ApiKeyCreatorFunction

Used with a state machine to create a new API key for a user.

"""

from __future__ import print_function

import os
import json
import uuid
import random
import boto3
import botocore
import zbase32

cognito_sync_client = boto3.client("cognito-sync")
apig_client = boto3.client("apigateway")

def lambda_handler(event, context):
    print('Event: {}'.format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    identity_id = event["identity-id"]
    
    stack_name = os.environ["STACK_NAME"]
    usage_plan_id = os.environ["USAGE_PLAN_ID"]
    user_profile_dataset_name = os.environ["COGNITO_USER_PROFILE_DATASET_NAME"]
    identity_pool_id = os.environ["COGNITO_IDENTITY_POOL_ID"]
    
    user_api_key_id = None
    user_api_key_value = None
    
    response = cognito_sync_client.list_records(
        IdentityPoolId = identity_pool_id,
        IdentityId = identity_id,
        DatasetName = user_profile_dataset_name
    )
    
    key_sync_count_map = {}
    
    old_user_api_key_id = None
    
    for each_record in response.get("Records", []):
        key_sync_count_map[each_record["Key"]] = each_record.get("SyncCount", 0)
        
        if each_record["Key"] == "api-key-id":
            old_user_api_key_id = each_record["Value"]
    
    sync_session_token = response["SyncSessionToken"]
    
    # User needs new API key.
    api_key_name = "{} - {}".format(
        stack_name,
        identity_id
    )

    response = apig_client.create_api_key(
        name = api_key_name,
        description = "Web chat API key for {}.".format(identity_id),
        enabled = True,
        value = generate_potential_api_key()
    )

    user_api_key_id = response["id"]
    user_api_key_value = response["value"]

    response = apig_client.create_usage_plan_key(
        usagePlanId = usage_plan_id,
        keyId = user_api_key_id,
        keyType = "API_KEY"
    )
    
    records_to_replace = {
        "api-key-id": user_api_key_id,
        "api-key-value": user_api_key_value
    }
    
    for each_record in response.get("Records", []):
        if each_record["Key"] in records_to_replace and each_record["Value"] == records_to_replace[each_record["Key"]]:
            del records_to_replace[each_record["Key"]]
    
    record_patch_list = []
    
    for each_key in records_to_replace.keys():
        each_value = records_to_replace[each_key]
        record_patch_list.append({
            "Op": "replace",
            "Key": each_key,
            "Value": each_value,
            "SyncCount": key_sync_count_map.get(each_key, 0)
        })
    
    if len(record_patch_list) > 0:
        print("Updating identity {} records: {}".format(
            user_profile_dataset_name,
            json.dumps(records_to_replace)
        ))
        response = cognito_sync_client.update_records(
            IdentityPoolId = identity_pool_id,
            IdentityId = identity_id,
            DatasetName = user_profile_dataset_name,
            RecordPatches = record_patch_list,
            SyncSessionToken = sync_session_token
        )
    
    if old_user_api_key_id is not None:
        print("Deleting user's previous API key ({}).".format(old_user_api_key_id))
        apig_client.delete_api_key(
            apiKey = old_user_api_key_id
        )
    
    return {
        "api-key-id": user_api_key_id,
        "api-key-value": user_api_key_value
    }

def generate_potential_api_key():
    # API key must be at least 30 characters.
    base_key = zbase32.b2a(uuid.uuid4().bytes)
    
    filler_content = "".join(random.sample(base_key, len(base_key)))
    
    return (zbase32.b2a(uuid.uuid4().bytes) + filler_content)[:30]