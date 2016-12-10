"""RoomGeneratorFunction

Returns a unique ID for a chat room.

When doing this, it also:
 * Creates an SNS topic for posting messages to the room.
 * Sets the SNS topic's policy to allow subscription, publishing, and cleanup.
 * Sets up a CloudWatch log group for success / failure delivery notifications.
 * Sets the SNS topic to log success and failure content.
 * Creates a CloudWatch metric filter for the SNS message dwell time.

"""

from __future__ import print_function

import json
import uuid
import time
import os
import boto3
from apigateway_helpers.exception import APIGatewayException
from apigateway_helpers.headers import get_response_headers

room_duration_seconds = 7200 # 7200 seconds == Two hours
#room_duration_seconds = 15

sns_client = boto3.client("sns")
sts_client = boto3.client("sts")
logs_client = boto3.client("logs")
sfn_client = boto3.client("stepfunctions")


def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    new_room_id = generate_new_room_id()
    
    new_topic_name = generate_room_sns_topic_name(new_room_id)
    
    sns_response = sns_client.create_topic(
        Name = new_topic_name
    )
    
    topic_arn = sns_response["TopicArn"]
    
    topic_attributes_to_set = [
        ("Policy", get_default_topic_policy(topic_arn)),
        ("SQSFailureFeedbackRoleArn", os.environ["SNS_FAILURE_FEEDBACK_ROLE"]),
        ("SQSSuccessFeedbackRoleArn", os.environ["SNS_SUCCESS_FEEDBACK_ROLE"])
    ]
    
    for each_topic_attribute_tuple in topic_attributes_to_set:
        sns_client.set_topic_attributes(
            TopicArn = topic_arn,
            AttributeName = each_topic_attribute_tuple[0],
            AttributeValue = each_topic_attribute_tuple[1]
        )
    
    log_group_name = get_sns_cloudwatch_log_group_name(event, new_room_id)
    
    logs_client.create_log_group(
        logGroupName = log_group_name
    )
    
    logs_client.put_metric_filter(
        logGroupName = log_group_name,
        filterName = "SNSRoomTopicDwellTime",
        filterPattern = "{ $.delivery.dwellTimeMs > 0 }",
        metricTransformations = [
            {
                "metricName": "DwellTimeMs",
                "metricNamespace": "WebChat-{}".format(event["requestContext"]["apiId"]),
                "metricValue": "$.delivery.dwellTimeMs"
            }
        ]
    )
    
    created_timestamp_seconds = int(time.time())
    
    room_config_object = {
        "created": created_timestamp_seconds,
        "duration": room_duration_seconds,
        "sns-topic-arn": topic_arn,
        "log-group": log_group_name
    }
    
    room_lifecycle_state_machine_arn = os.environ["ROOM_LIFECYCLE_STATE_MACHINE_ARN"]
    
    response = sfn_client.start_execution(
        stateMachineArn = room_lifecycle_state_machine_arn,
        name = new_room_id,
        input = json.dumps({
            "id": new_room_id,
            "config": room_config_object
        })
    )
    
    print("Room lifecycle state machine execution ARN: {}".format(response["executionArn"]))
    
    return {
        "id": new_room_id
    }

def generate_room_sns_topic_name(room_id):
    return "{}-{}".format(
        os.environ["PROJECT_GLOBAL_PREFIX"],
        room_id
    )

def generate_new_room_id():
    return "{}".format(uuid.uuid4())

account_id = None
def get_own_account_id():
    global account_id
    
    if account_id is None:
        account_id = sts_client.get_caller_identity()["Account"]
    
    return account_id

def get_sns_cloudwatch_log_group_name(event, room_id):
    return "sns/{region}/{account_id}/{app_prefix}-{room_id}".format(
        region = os.environ["AWS_DEFAULT_REGION"],
        account_id = get_own_account_id(),
        app_prefix = os.environ["PROJECT_GLOBAL_PREFIX"],
        room_id = room_id
    )
    
def get_default_topic_policy(sns_topic_arn):
    return json.dumps({
        "Version": "2008-10-17",
        "Statement": [
            {
                "Sid": "AllowSubscriptionFromRoomSessionGenerator",
                "Effect": "Allow",
                "Principal": {
                    "AWS": os.environ["SUBSCRIBE_ROOM_TOPIC_ROLE"]
                },
                "Action": "sns:Subscribe",
                "Resource": sns_topic_arn
            },
            {
                "Sid": "AllowPublishingByRoomMessagePoster",
                "Effect": "Allow",
                "Principal": {
                    "AWS": os.environ["PUBLISH_ROOM_TOPIC_ROLE"]
                },
                "Action": "sns:Publish",
                "Resource": sns_topic_arn
            },
            {
                "Sid": "AllowRoomLifecycleManagement",
                "Effect": "Allow",
                "Principal": {
                    "AWS": os.environ["ROOM_LIFECYCLE_FUNCTION_ROLE"]
                },
                "Action": "sns:SetTopicAttributes",
                "Resource": sns_topic_arn
            },
            {
                "Sid": "AllowCleanup",
                "Effect": "Allow",
                "Principal": {
                    "AWS": os.environ["DELETE_ROOM_TOPIC_ROLE"]
                },
                "Action": "sns:DeleteTopic",
                "Resource": sns_topic_arn
            }
        ]
    })

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