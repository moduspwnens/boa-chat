"""RoomMessageLogFetcherFunction

Fetches recent room messages.

"""

from __future__ import print_function

import os
import json
import time
import operator
from multiprocessing.pool import ThreadPool
import boto3
import botocore
from apigateway_helpers.exception import APIGatewayException
from apigateway_helpers.headers import get_response_headers

s3_bucket_name = os.environ["SHARED_BUCKET"]

s3_client = boto3.client("s3")

max_records_per_request = 10

s3_key_get_results = {}

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    s3_key_get_results.clear()
    
    room_id = event["pathParameters"]["room-id"]
    
    if event.get("queryStringParameters") is None:
        event["queryStringParameters"] = {}
    
    list_direction = event["queryStringParameters"].get("direction", "forward")
    
    valid_directions = ["reverse"]
    
    if list_direction not in valid_directions:
        raise APIGatewayException("URL parameter \"direction\" should be one of: {}".format(", ".join(valid_directions)), 400)
    
    next_token = event["queryStringParameters"].get("next-token")
    
    default_from = int(time.time())
    if list_direction == "forward":
        default_from = 0
    
    from_timestamp = event["queryStringParameters"].get("from", default_from)
    
    try:
        from_timestamp = int(from_timestamp)
    except:
        raise APIGatewayException("URL parameter \"from\" should be a unix timestamp.", 400)
    
    list_objects_kwargs = {
        "Bucket": s3_bucket_name,
        "Prefix": "room-event-logs/{}/reverse/".format(
            room_id
        ),
        "StartAfter": "room-event-logs/{}/reverse/{}-".format(
            room_id,
            get_reverse_lexi_string_for_timestamp(from_timestamp)
        )
    }
    
    list_objects_kwargs["MaxKeys"] = max_records_per_request
    
    if next_token is not None:
        list_objects_kwargs["ContinuationToken"] = next_token
    
    response = s3_client.list_objects_v2(**list_objects_kwargs)
    
    is_truncated = response["IsTruncated"]
    
    print("List operation returned {} key(s). Is truncated? {}".format(
        response["KeyCount"],
        is_truncated
    ))
    
    pool_map_args = []
    
    for each_object_dict in response.get("Contents", []):
        each_key = each_object_dict["Key"]
        
        pool_map_args.append(each_key)
        
    pool = ThreadPool(processes=10)
    
    s3_fetch_start_time = time.time()
    pool.map(get_s3_bucket_object, pool_map_args)
    s3_fetch_end_time = time.time()
    
    print("Fetched {} S3 objects in {} seconds.".format(
        len(pool_map_args),
        s3_fetch_end_time - s3_fetch_start_time
    ))
    
    message_list = []
    
    for each_key in s3_key_get_results:
        
        each_filename = each_key.split("/")[-1]
        filename_parts = each_filename.split("-")
        
        each_message_id = "-".join(filename_parts[2:]).split(".")[0]
        each_message_object = s3_key_get_results[each_key]
        
        each_message_object["message-id"] = each_message_id
        
        message_list.append(each_message_object)
    
    message_list.sort(key=operator.itemgetter("timestamp"))
    
    if list_direction == "reverse":
        message_list.reverse()
    
    response_object = {
        "messages": message_list,
        "truncated": is_truncated
    }
    
    if "NextContinuationToken" in response:
        response_object["next-token"] = response["NextContinuationToken"]
    
    return response_object

def get_s3_bucket_object(key):
    session = boto3.session.Session()
    
    s3_client = session.client("s3")
    
    s3_key_get_results[key] = json.loads(s3_client.get_object(Bucket = s3_bucket_name, Key = key)["Body"].read())

def get_reverse_lexi_string_for_timestamp(timestamp):
    timestamp_string = str(timestamp).zfill(10)
    
    character_list = []
    
    for each_character in timestamp_string:
        new_character = 9 - int(each_character)
        character_list.append(str(new_character))
    
    return "".join(character_list)

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