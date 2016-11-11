"""RoomMessagePollerFunction

Expected request time: ~250ms if message is available
    The request will stay open for up to 20 seconds waiting for a message.

"""

from __future__ import print_function

import json, time, hashlib
import boto3
from apigateway_helpers.exception import APIGatewayException

queue_url_cache = {}
sqs_client = boto3.client("sqs")

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    sqs_queue_name = get_queue_name(event)
    queue_url = get_queue_url(sqs_queue_name)
    
    response = sqs_client.receive_message(
        QueueUrl = queue_url,
        MaxNumberOfMessages = 10,
        WaitTimeSeconds = 20
    )
    
    receipt_handles = []
    return_messages = []
    
    for each_message in response.get("Messages", []):
        sns_notification = json.loads(each_message["Body"])
        sns_message = json.loads(sns_notification["Message"])
        sns_message["message-id"] = sns_notification["MessageId"]
        return_messages.append(sns_message)
        receipt_handles.append(each_message["ReceiptHandle"])
    
    return {
        "messages": return_messages,
        "receipt-handles": receipt_handles
    }

def get_queue_name(event):
    
    hash_string_base = "{}-{}-{}-{}".format(
        event["api-id"],
        event["stage"],
        event["request-params"]["path"]["room-id"],
        event["request-params"]["path"]["session-id"]
    )
    
    return "web-chat-{}".format(
        hashlib.md5(hash_string_base).hexdigest()
    )

def get_queue_url(sqs_queue_name):
    if sqs_queue_name not in queue_url_cache:
        queue_url_cache[sqs_queue_name] = sqs_client.get_queue_url(QueueName=sqs_queue_name)["QueueUrl"]
    
    return queue_url_cache[sqs_queue_name]