"""RoomMessagePollerFunction

The request will stay open for up to 20 seconds waiting for a message.

"""

from __future__ import print_function

import json, time, hashlib
import boto3
import botocore
from apigateway_helpers.exception import APIGatewayException
from apigateway_helpers.headers import get_response_headers

queue_url_cache = {}
sqs_client = boto3.client("sqs")

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    sqs_queue_name = get_queue_name(event)
    
    try:
        queue_url = get_queue_url(sqs_queue_name)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
            raise APIGatewayException("Room session doesn't exist or you don't have access to it.", 400)
        raise
    
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
        event["requestContext"]["apiId"],
        event["requestContext"]["stage"],
        event["pathParameters"]["room-id"],
        event["pathParameters"]["session-id"]
    )
    
    return "web-chat-{}".format(
        hashlib.md5(hash_string_base).hexdigest()
    )

def get_queue_url(sqs_queue_name):
    if sqs_queue_name not in queue_url_cache:
        queue_url_cache[sqs_queue_name] = sqs_client.get_queue_url(QueueName=sqs_queue_name)["QueueUrl"]
    
    return queue_url_cache[sqs_queue_name]

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