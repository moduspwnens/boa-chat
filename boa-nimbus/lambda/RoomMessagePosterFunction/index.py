"""RoomMessagePosterFunction

Allows posting a message to a room. Returns the message ID of the posted 
message.

"""

from __future__ import print_function

import os
import json
import time
import boto3
import botocore
from apigateway_helpers.exception import APIGatewayException
from apigateway_helpers.headers import get_response_headers

s3_client = boto3.client("s3")
sns_client = boto3.client("sns")
cognito_sync_client = boto3.client("cognito-sync")
room_id_topic_arn_map = {}

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    event["request-body"] = json.loads(event["body"])
    
    cognito_identity_id = event["requestContext"]["identity"]["cognitoIdentityId"]
    
    if event["request-body"].get("version", "1") != "1":
        raise APIGatewayException("Unsupported message version: {}".format(event["request-body"]["version"]), 400)
    
    try:
        sns_topic_arn = get_room_topic_arn(event)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'AccessDenied':
            room_id = event["pathParameters"]["room-id"]
            raise APIGatewayException("Room \"{}\" either doesn't exist or you don't have access to it.".format(room_id), 403)
        else:
            raise
    
    user_profile_dataset_name = os.environ["COGNITO_USER_PROFILE_DATASET_NAME"]
    identity_pool_id = event["requestContext"]["identity"]["cognitoIdentityPoolId"]
    
    response = cognito_sync_client.list_records(
        IdentityPoolId = identity_pool_id,
        IdentityId = cognito_identity_id,
        DatasetName = user_profile_dataset_name
    )
    
    author_name = cognito_identity_id
    for each_record in response["Records"]:
        if each_record["Key"] == "email-address":
            author_name = each_record["Value"]
            break
    
    response = sns_client.publish(
        TopicArn = sns_topic_arn,
        Message = json.dumps({
            "identity-id": cognito_identity_id,
            "author-name": author_name,
            "message": event["request-body"].get("message", ""),
            "timestamp": int(time.time())
        })
    )
    
    return {
        "message-id": response["MessageId"]
    }

def get_room_topic_arn(event):
    room_id = event["pathParameters"]["room-id"]
    
    if room_id not in room_id_topic_arn_map:
        s3_bucket_name = "webchat-sharedbucket-{}".format(event["requestContext"]["apiId"])
        room_info_dict = json.loads(s3_client.get_object(Bucket=s3_bucket_name, Key="room-topics/{}.json".format(room_id))["Body"].read())
        room_id_topic_arn_map[room_id] = room_info_dict["sns-topic-arn"]
    
    return room_id_topic_arn_map[room_id]

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