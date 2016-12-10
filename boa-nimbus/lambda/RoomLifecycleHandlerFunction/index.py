"""RoomLifecycleHandlerFunction

State machine and Lambda function for managing the chat room's state over its lifetime.

"""

from __future__ import print_function

import os
import json
import time
import boto3
import botocore

# Number of seconds to wait after closing the room to new messages before 
# deleting its resources.
inflight_wait_delay_seconds = 15

sns_client = boto3.client("sns")
sqs_client = boto3.client("sqs")
logs_client = boto3.client("logs")
s3_client = boto3.client("s3")

def lambda_handler(event, context):
    print('Event: {}'.format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    room_id = event["id"]
    log_group_name = event["config"]["log-group"]
    sns_topic_arn = event["config"]["sns-topic-arn"]
    
    if not event.get("new-posts-disabled", False):
        try:
            close_room_to_new_posts(sns_topic_arn)
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "AuthorizationError":
                print("Unable to set room topic policy. Presumed already deleted.")
            else:
                raise
        
        return dict(event, **{
            "new-posts-disabled": True,
            "inflight-wait-duration": inflight_wait_delay_seconds
        })
    
    else:
        print("Deleting room topic ({}).".format(sns_topic_arn))
        try:
            sns_client.delete_topic(TopicArn = sns_topic_arn)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'AuthorizationError':
                print("Unauthorized to delete room topic. Presumed already deleted.")
            else:
                raise
        
        print("Deleting log group ({}).".format(log_group_name))
        try:
            logs_client.delete_log_group(logGroupName=log_group_name)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print("Log group already deleted.")
            else:
                raise
        
        deleted_queue_url_map = {}
        
        while True:
        
            response = sqs_client.list_queues(
                QueueNamePrefix = "{}-{}-".format(
                    os.environ["PROJECT_GLOBAL_PREFIX"],
                    room_id.replace("-", "")
                )
            )
            
            queue_urls = response.get("QueueUrls", [])
            
            if len(queue_urls) == 0:
                print("Request for room's queues returned no results.")
                break
            
            deletions_attempted = 0
            
            for each_queue_url in queue_urls:
                if each_queue_url in deleted_queue_url_map:
                    continue
                
                print("Deleting queue: {}".format(each_queue_url))
                
                deletions_attempted += 1
                
                try:
                    sqs_client.delete_queue(
                        QueueUrl = each_queue_url
                    )
                    
                    deleted_queue_url_map[each_queue_url] = True
                except botocore.exceptions.ClientError as e:
                    if e.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
                        print("Queue already deleted.")
                    else:
                        raise
                        
            if deletions_attempted == 0:
                print("Last request for queues returned only queues we've already deleted.")
                break
    
    
    return dict(event, **{})

def close_room_to_new_posts(sns_topic_arn):
    print("Setting room topic to disallow new subscriptions and user posts.")
    
    sns_client.set_topic_attributes(
        TopicArn = sns_topic_arn,
        AttributeName = "Policy",
        AttributeValue = get_default_closed_sns_topic_policy(sns_topic_arn)
    )
    
    print("Posting final room closure message.")
    
    sns_client.publish(
        TopicArn = sns_topic_arn,
        Message = json.dumps({
            "identity-id": "SYSTEM",
            "author-name": "System Message",
            "message": "The room is now closed.",
            "type": "ROOM_CLOSED",
            "timestamp": int(time.time())
        })
    )
    
def get_default_closed_sns_topic_policy(sns_topic_arn):
    return json.dumps({
        "Version": "2008-10-17",
        "Statement": [
            {
                "Sid": "AllowRoomLifecycleActions",
                "Effect": "Allow",
                "Principal": {
                    "AWS": os.environ["OWN_FUNCTION_ROLE"]
                },
                "Action": [
                    "sns:DeleteTopic",
                    "sns:GetTopicAttributes",
                    "sns:ListSubscriptionsByTopic",
                    "sns:Publish",
                    "sns:SetTopicAttributes"
                ],
                "Resource": sns_topic_arn
            },
            {
                "Sid": "AllowCleanupByStackCleanup",
                "Effect": "Allow",
                "Principal": {
                    "AWS": os.environ["DELETE_ROOM_TOPIC_ROLE"]
                },
                "Action": "sns:DeleteTopic",
                "Resource": sns_topic_arn
            }
        ]
    })