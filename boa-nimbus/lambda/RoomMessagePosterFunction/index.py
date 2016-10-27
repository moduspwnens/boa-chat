from __future__ import print_function

import json
import time
import boto3
from apigateway_helpers.exception import APIGatewayException

s3_client = boto3.client("s3")
sns_client = boto3.client("sns")
room_id_topic_arn_map = {}

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    if event.get("user-id", "") == "":
        raise APIGatewayException("URL parameter \"user-id\" is required.", 400)
    
    if event["request-body"].get("version", "1") != "1":
        raise APIGatewayException("Unsupported message version: {}".format(event["request-body"]["version"]), 400)
    
    sns_topic_arn = get_room_topic_arn(event)
    
    response = sns_client.publish(
        TopicArn = sns_topic_arn,
        Message = json.dumps({
            "user-id": event["user-id"],
            "message": event["request-body"].get("message", ""),
            "timestamp": int(time.time())
        })
    )
    
    return {
        "message-id": response["MessageId"]
    }

def get_room_topic_arn(event):
    if event["room-id"] not in room_id_topic_arn_map:
        s3_bucket_name = "webchat-sharedbucket-{}".format(event["api-id"])
        room_info_dict = json.loads(s3_client.get_object(Bucket=s3_bucket_name, Key="room-topics/{}.json".format(event["room-id"]))["Body"].read())
        room_id_topic_arn_map[event["room-id"]] = room_info_dict["sns-topic-arn"]
    
    return room_id_topic_arn_map[event["room-id"]]