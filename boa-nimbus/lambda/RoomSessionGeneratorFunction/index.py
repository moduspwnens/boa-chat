"""RoomSessionGeneratorFunction

Returns a unique session ID for an instance of a user in a room.

By having a separate session ID, we can have the same user watching for messages from 
multiple places / clients / sessions.

On the back end, this:
 * Creates an SQS queue for the session to poll.
 * Subscribes the queue to the room's SNS topic.
 * Sets the SQS queue's policy to allow:
   * The room's SNS topic to send to it.
   * The polling function to receive messages from it.
   * The acknowledging function to delete messages from it.
   * The cleanup function to delete it.
 * Creates a pointer record in S3 so that the SQS queue can be found and
   cleaned up later.

Expected request time: ~1100ms. 
    Not particularly fast, but it only happens when first joining a room.

"""

from __future__ import print_function

import json
import uuid
import time
import hashlib
import boto3
from apigateway_helpers import get_public_api_base
from apigateway_helpers.exception import APIGatewayException

sqs_client = boto3.client("sqs")
s3_client = boto3.client("s3")

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    public_api_base = get_public_api_base(event)
    
    if event["request-body"].get("user-id", "") == "":
        raise APIGatewayException("Value for \"user-id\" must be specified in message.", 400)
    
    session_id = generate_new_session_id()
    
    sqs_queue_name = get_queue_name(event, session_id)
    create_and_initialize_queue(event, sqs_queue_name, session_id)
    
    return {
        "session": "{}{}/{}".format(
            public_api_base,
            event["resource-path"].format(**{
                "room-id": event["request-params"]["path"]["room-id"]
            }),
            session_id
        )
    }

def generate_new_session_id():
    return "{}".format(uuid.uuid4())

def create_and_initialize_queue(event, sqs_queue_name, session_id):
    s3_bucket_name = "webchat-sharedbucket-{}".format(event["api-id"])
    room_info_dict = json.loads(s3_client.get_object(Bucket=s3_bucket_name, Key="room-topics/{}.json".format(event["request-params"]["path"]["room-id"]))["Body"].read())
    sns_topic_arn = room_info_dict["sns-topic-arn"]
    
    queue_url = sqs_client.create_queue(
        QueueName = sqs_queue_name,
        Attributes = get_default_queue_attributes(event, sns_topic_arn)
    )["QueueUrl"]
    
    queue_arn = sqs_client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["QueueArn"])["Attributes"]["QueueArn"]
    
    subscribe_response = boto3.client("sns").subscribe(
        TopicArn = sns_topic_arn,
        Protocol = "sqs",
        Endpoint = queue_arn
    )
    
    s3_queue_config_object = {
        "created": int(time.time()),
        "sqs-queue-url": queue_url,
        "sns-subscription-arn": subscribe_response["SubscriptionArn"],
        "user-id": event["request-body"]["user-id"]
    }

    s3_client.put_object(
        Bucket = s3_bucket_name,
        Key = "room-queues/{}/{}.json".format(
            event["request-params"]["path"]["room-id"],
            session_id
        ),
        Body = json.dumps(s3_queue_config_object, indent=4)
    )

def get_queue_name(event, session_id):
    
    hash_string_base = "{}-{}-{}-{}".format(
        event["api-id"],
        event["stage"],
        event["request-params"]["path"]["room-id"],
        session_id
    )
    
    return "web-chat-{}".format(
        hashlib.md5(hash_string_base).hexdigest()
    )

def get_default_queue_attributes(event, sns_topic_arn):
    
    return {
        "Policy": json.dumps({
                    "Version": "2012-10-17",
                    "Statement": [
                {
                    "Sid": "AllowSNSRoomTopicSending",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "sqs:SendMessage",
                    "Resource": "*",
                    "Condition": {
                        "ArnEquals": {
                            "aws:SourceArn": sns_topic_arn
                        }
                    }
                },
                {
                    "Sid": "AllowRoomAcknowledgerActions",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": event["acknowledger-function-role"]
                    },
                    "Action": [
                        "sqs:GetQueueUrl",
                        "sqs:DeleteMessage"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "AllowRoomPollerActions",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": event["poller-function-role"]
                    },
                    "Action": [
                        "sqs:GetQueueUrl",
                        "sqs:ReceiveMessage"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "AllowCleanup",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": event["delete-function-role"]
                    },
                    "Action": "sqs:DeleteQueue",
                    "Resource": "*"
                }
            ]
        })
    }