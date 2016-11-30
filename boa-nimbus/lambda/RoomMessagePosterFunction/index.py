"""RoomMessagePosterFunction

Allows posting a message to a room. Returns the message ID of the posted 
message.

Expected request time: ~250ms.

"""

from __future__ import print_function

import os
import json
import time
import boto3
import botocore
from apigateway_helpers.exception import APIGatewayException

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
    
    cognito_identity_id = event["cognito-identity-id"]
    
    if event["request-body"].get("version", "1") != "1":
        raise APIGatewayException("Unsupported message version: {}".format(event["request-body"]["version"]), 400)
    
    try:
        sns_topic_arn = get_room_topic_arn(event)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'AccessDenied':
            room_id = event["request-params"]["path"]["room-id"]
            raise APIGatewayException("Room \"{}\" either doesn't exist or you don't have access to it.".format(room_id), 403)
        else:
            raise
    
    user_profile_dataset_name = os.environ["COGNITO_USER_PROFILE_DATASET_NAME"]
    identity_pool_id = os.environ["COGNITO_IDENTITY_POOL_ID"]
    
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
    room_id = event["request-params"]["path"]["room-id"]
    
    if room_id not in room_id_topic_arn_map:
        s3_bucket_name = "webchat-sharedbucket-{}".format(event["api-id"])
        room_info_dict = json.loads(s3_client.get_object(Bucket=s3_bucket_name, Key="room-topics/{}.json".format(room_id))["Body"].read())
        room_id_topic_arn_map[event["request-params"]["path"]["room-id"]] = room_info_dict["sns-topic-arn"]
    
    return room_id_topic_arn_map[room_id]