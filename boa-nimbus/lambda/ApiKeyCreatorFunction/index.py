"""ApiKeyCreatorFunction

Used to create a new API key.

Additional complexity necessary to work around the few second delay between 
an API key being linked to a usage plan and API Gateway recognizing that and 
not rejecting its requests.

It will precreate an API key ahead of time to return later if one isn't 
requested for a user on its first invocation.

There are four contexts under which it can be invoked:

  - Prewarming
        This will precreate an API key if one is not already ready.
  - S3 Event Notification
        This happens when a previously precreated API key is at least a day 
        old. If it hasn't been assigned to a user, it needs to be deleted 
        since it must belong to a terminated Lambda instance.
  - Precreate request
        This is an asynchronous invocation from another instance of this 
        Lambda function. This happens when the function is about to return 
        an API key for a request, but needs a new one to be precreated for the 
        next request.
  - API key request
        A direct invocation for an API key to be created and attached to an 
        identity. This will invoke a precreate request, then return a 
        precreated key (if available) or create one on the fly and return it.
  

"""

from __future__ import print_function

import os
import json
import uuid
import time
import random
import traceback
import boto3
import botocore
import zbase32

cognito_sync_client = boto3.client("cognito-sync")
apig_client = boto3.client("apigateway")
s3_client = boto3.client("s3")
lambda_client = boto3.client("lambda")

precreated_api_key_pointer_id = None
precreated_api_key_bucket = os.environ["PRECREATED_API_KEY_BUCKET"]

def lambda_handler(event, context):
    print('Event: {}'.format(json.dumps(event)))
    
    return_value = None
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return_value = warming_event_received(event, context)
    elif "Records" in event:
        return_value = s3_event_notification_received(event, context)
    elif "precreate-api-key-request-id" in event:
        return_value = precreate_api_key_request_received(event, context)
    elif "identity-id" in event:
        return_value = create_api_key_for_user_request_received(event, context)
    else:
        raise Exception("Invalid request event.")
    
    print("Precreated API key pointer for next request: {}".format(precreated_api_key_pointer_id))
    
    return return_value

def generate_potential_api_key():
    # API key must be at least 30 characters.
    base_key = zbase32.b2a(uuid.uuid4().bytes)
    
    filler_content = "".join(random.sample(base_key, len(base_key)))
    
    return (zbase32.b2a(uuid.uuid4().bytes) + filler_content)[:30]

def warming_event_received(event, context):
    
    precreate_own_api_key_if_none_cached()
    
    return {
        "message": "Warmed!"
    }

def s3_event_notification_received(event, context):
    
    for each_record in event.get("Records", []):
        s3_event_notification_record_received(each_record, context)
    
    return {}

def s3_event_notification_record_received(record, context):
    
    s3_bucket_name = record["s3"]["bucket"]["name"]
    s3_object_key = record["s3"]["object"]["key"]
    
    api_key_claimed = False
    
    s3_object_filename = s3_object_key.split("/")[-1]
    api_key_pointer_id = s3_object_filename.split(".")[0]
    
    target_object_key = "claimed-api-keys/{}".format(s3_object_filename)
    
    try:
        response = s3_client.head_object(
            Bucket = s3_bucket_name,
            Key = target_object_key
        )
        
        api_key_claimed = True
        
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            pass
        else:
            raise
    
    if not api_key_claimed:
        print("Received delete event notification for unclaimed key pointer: {}".format(api_key_pointer_id))
        
        target_object_key = "generated-api-keys/{}".format(s3_object_filename)
        
        try:
            response = s3_client.get_object(
                Bucket = s3_bucket_name,
                Key = target_object_key
            )
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                print("No pointer file available to lookup API key details. Assuming already deleted.")
                precreate_own_api_key_if_none_cached()
                return
            else:
                raise
        
        api_key_dict = json.loads(response["Body"].read())
        
        api_key_id = api_key_dict["api-key-id"]
        
        print("Deleting API key with pointer ({}) and ID: {}".format(
            api_key_pointer_id,
            api_key_id
        ))
        
        try:
            apig_client.delete_api_key(
                apiKey = api_key_id
            )
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NotFoundException":
                pass
            else:
                raise
        
        s3_client.delete_object(
            Bucket = s3_bucket_name,
            Key = target_object_key
        )
    
    precreate_own_api_key_if_none_cached()

def precreate_api_key_request_received(event, context):
    
    # First, precreate the API key that was asked for.
    precreate_api_key_with_id(event["precreate-api-key-request-id"])
    
    # Next, create one for this Lambda container instance.
    precreate_own_api_key_if_none_cached()

def precreate_own_api_key_if_none_cached():
    if precreated_api_key_pointer_id is None:
        new_api_key_pointer_id = str(uuid.uuid4())
        precreate_api_key_with_id(new_api_key_pointer_id)
        set_precreated_api_key_pointer(new_api_key_pointer_id)

def precreate_api_key_with_id(new_api_key_pointer_id):
    
    print("Precreating new API key with pointer: {}".format(new_api_key_pointer_id))
    
    new_api_key_dict = create_new_api_key()
    
    wait_until_api_key_ready(new_api_key_dict["api-key-value"])
    
    for each_prefix in ["available-api-keys", "generated-api-keys"]:
        s3_client.put_object(
            Bucket = precreated_api_key_bucket,
            Key = "{}/{}.json".format(
                each_prefix,
                new_api_key_pointer_id
            ),
            Body = json.dumps(new_api_key_dict, indent=4)
        )
    
    return new_api_key_dict

def set_precreated_api_key_pointer(new_api_key_pointer_id):
    global precreated_api_key_pointer_id
    
    precreated_api_key_pointer_id = new_api_key_pointer_id
    print("New precreated API key cached with pointer: {}".format(precreated_api_key_pointer_id))

def create_new_api_key():
    
    stack_name = os.environ["STACK_NAME"]
    usage_plan_id = os.environ["USAGE_PLAN_ID"]
    
    # User needs new API key.
    api_key_name = "{} - {}".format(
        stack_name,
        str(uuid.uuid4())
    )

    response = apig_client.create_api_key(
        name = api_key_name,
        description = "Web chat API key",
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
    
    return {
        "api-key-id": user_api_key_id,
        "api-key-value": user_api_key_value
    }

def send_precreate_api_key_request(function_arn):
    
    print("Sending asynchronous precreate API key request.")
    
    new_api_key_pointer_id = str(uuid.uuid4())
    
    lambda_client.invoke_async(
        FunctionName = function_arn,
        InvokeArgs = json.dumps({
            "precreate-api-key-request-id": new_api_key_pointer_id
        })
    )
    
    set_precreated_api_key_pointer(new_api_key_pointer_id)

def get_cached_precreated_api_key_with_pointer():
    
    if precreated_api_key_pointer_id is None:
        return None
    
    target_object_key = "generated-api-keys/{}.json".format(precreated_api_key_pointer_id)
    print("Fetching pointer object from S3 ({})".format(
        target_object_key
    ))
    try:
        response = s3_client.get_object(
            Bucket = precreated_api_key_bucket,
            Key = target_object_key
        )
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            print("No pointer object found on S3.")
            return None
        raise
    
    api_key_dict = json.loads(response["Body"].read())
    
    claimed_target_key = "claimed-api-keys/{}.json".format(precreated_api_key_pointer_id)
    
    s3_client.put_object(
        Bucket = precreated_api_key_bucket,
        Key = claimed_target_key,
        Body = json.dumps({})
    )
    
    return api_key_dict

def create_api_key_for_user_request_received(event, context):
    
    sent_precreate_request = False
    api_key_created_new = False
    
    api_key_dict = get_cached_precreated_api_key_with_pointer()
    
    if api_key_dict is None:
        # We have no precreated API key pointer available.
        send_precreate_api_key_request(context.invoked_function_arn)
        sent_precreate_request = True
    
    identity_id = event["identity-id"]
    
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
    
    # User needs a new API key.
    if api_key_dict is None:
        print("No cached API key is available. Creating a new one for this request.")
        api_key_dict = create_new_api_key()
        api_key_created_new = True
    
    user_api_key_id = api_key_dict["api-key-id"]
    user_api_key_value = api_key_dict["api-key-value"]
    
    
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
    
    if not sent_precreate_request:
        # We started out with a precreated API key pointer.
        set_precreated_api_key_pointer(None)
        send_precreate_api_key_request(context.invoked_function_arn)
    
    
    if old_user_api_key_id is not None:
        print("Deleting user's previous API key ({}).".format(old_user_api_key_id))
        apig_client.delete_api_key(
            apiKey = old_user_api_key_id
        )
    
    if api_key_created_new:
        wait_until_api_key_ready(user_api_key_value)
    
    return {
        "api-key-id": user_api_key_id,
        "api-key-value": user_api_key_value
    }

def wait_until_api_key_ready(api_key):
    fresh_api_key_wait_delay_seconds = 10
    
    print("Waiting {} seconds to ensure API key is ready to be used.".format(fresh_api_key_wait_delay_seconds))
    time.sleep(fresh_api_key_wait_delay_seconds)