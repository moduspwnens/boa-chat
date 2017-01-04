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

"""

from __future__ import print_function

import os
import json
import uuid
import time
import hashlib
import base64
import boto3
import botocore
import zbase32
from apigateway_helpers.exception import APIGatewayException
from apigateway_helpers.headers import get_response_headers

sqs_client = boto3.client("sqs")
s3_client = boto3.client("s3")

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    session_id = generate_new_session_id()
    
    sqs_queue_name = get_queue_name(event, session_id)
    create_and_initialize_queue(event, context, sqs_queue_name, session_id)
    
    return {
        "id": session_id
    }

def generate_new_session_id():
    return zbase32.b2a(uuid.uuid4().bytes)

def create_and_initialize_queue(event, context, sqs_queue_name, session_id):
    
    sns_topic_arn = "arn:aws:sns:{aws_region}:{aws_account_id}:{topic_name}".format(
        aws_region = context.invoked_function_arn.split(":")[3],
        aws_account_id = context.invoked_function_arn.split(":")[4],
        topic_name = generate_room_sns_topic_name(event["pathParameters"]["room-id"])
    )
    
    response = sqs_client.create_queue(
        QueueName = sqs_queue_name,
        Attributes = get_default_queue_attributes(sns_topic_arn)
    )
    
    queue_url = response["QueueUrl"]
    
    response = sqs_client.get_queue_attributes(
        QueueUrl = queue_url,
        AttributeNames = ["QueueArn"]
    )
    
    queue_arn = response["Attributes"]["QueueArn"]
    
    try:
        subscribe_response = boto3.client("sns").subscribe(
            TopicArn = sns_topic_arn,
            Protocol = "sqs",
            Endpoint = queue_arn
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'AuthorizationError':
            print("Unauthorized to subscribe to room's SNS topic ({}). Assuming it doesn't exist.".format(
                sns_topic_arn
            ))
            
            sqs_client.delete_queue(
                QueueUrl = queue_url
            )
            
            raise APIGatewayException("Room specified doesn't exist or you don't have access to it.", 400)
        else:
            raise
        
        

def generate_room_sns_topic_name(room_id):
    return "{}-{}".format(
        os.environ["PROJECT_GLOBAL_PREFIX"],
        room_id
    )

def get_queue_name(event, session_id):
    
    return "{}-{}-{}".format(
        os.environ["PROJECT_GLOBAL_PREFIX"],
        event["pathParameters"]["room-id"].replace("-", ""),
        session_id.replace("-", "")
    )

def get_default_queue_attributes(sns_topic_arn):
    
    policy_dict = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowDeletionIfSubscriptionFails",
                "Effect": "Allow",
                "Principal": {
                    "AWS": os.environ["OWN_FUNCTION_ROLE"]
                },
                "Action": "sqs:DeleteQueue",
                "Resource": "*"
            },
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
                    "AWS": os.environ["ACKNOWLEDGER_FUNCTION_ROLE"]
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
                    "AWS": os.environ["SESSION_POLLER_ROLE"]
                },
                "Action": [
                    "sqs:GetQueueUrl",
                    "sqs:ReceiveMessage"
                ],
                "Resource": "*"
            },
            {
                "Sid": "AllowRoomLifecycleActions",
                "Effect": "Allow",
                "Principal": {
                    "AWS": os.environ["ROOM_LIFECYCLE_FUNCTION_ROLE"]
                },
                "Action": "sqs:DeleteQueue",
                "Resource": "*"
            },
            {
                "Sid": "AllowCleanup",
                "Effect": "Allow",
                "Principal": {
                    "AWS": os.environ["QUEUE_DELETE_FUNCTION_ROLE"]
                },
                "Action": "sqs:DeleteQueue",
                "Resource": "*"
            }
        ]
    }
    
    return {
        "Policy": json.dumps(policy_dict)
    }

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