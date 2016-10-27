from __future__ import print_function

import json, uuid, time
import boto3
from apigateway_helpers import get_public_api_base

sns_client = boto3.client("sns")

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    public_api_base = get_public_api_base(event)
    
    new_room_id = generate_new_room_id()
    
    new_topic_name = generate_room_sns_topic_name(event, new_room_id)
    
    sns_response = sns_client.create_topic(
        Name = new_topic_name
    )
    
    topic_arn = sns_response["TopicArn"]
    
    sns_client.set_topic_attributes(
        TopicArn = topic_arn,
        AttributeName = "Policy",
        AttributeValue = get_default_topic_policy(event, topic_arn)
    )
    
    s3_room_config_object = {
        "created": int(time.time()),
        "sns-topic-arn": topic_arn
    }
    
    s3_bucket_name = "webchat-sharedbucket-{}".format(event["api-id"])
    
    boto3.client("s3").put_object(
        Bucket = s3_bucket_name,
        Key = "room-topics/{}.json".format(new_room_id),
        Body = json.dumps(s3_room_config_object, indent=4)
    )
    
    return {
        "room": "{}{}/{}".format(
            public_api_base,
            event["resource-path"],
            new_room_id
        )
    }

def generate_room_sns_topic_name(event, room_id):
    return "web-chat-{}-{}-{}".format(
        event["api-id"],
        event["stage"],
        room_id
    )

def generate_new_room_id():
    return "{}".format(uuid.uuid4())
    
def get_default_topic_policy(event, sns_topic_arn):
    return json.dumps({
        "Version": "2008-10-17",
        "Statement": [
            {
                "Sid": "AllowSubscriptionFromRoomMessagePoller",
                "Effect": "Allow",
                "Principal": {
                    "AWS": event["subscribe-function-role"]
                },
                "Action": "sns:Subscribe",
                "Resource": sns_topic_arn
            },
            {
                "Sid": "AllowCleanup",
                "Effect": "Allow",
                "Principal": {
                    "AWS": event["delete-function-role"]
                },
                "Action": "sns:DeleteTopic",
                "Resource": sns_topic_arn
            }
        ]
    })
