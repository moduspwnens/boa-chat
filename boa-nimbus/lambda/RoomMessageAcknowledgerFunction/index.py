"""RoomMessageAcknowledgerFunction

Receives a list of SQS receipt handles and uses them to delete the messages 
from the queue. This makes sure the client receives any messages that were 
sent out.

"""

from __future__ import print_function

import json, time, hashlib
import boto3
import botocore
from apigateway_helpers.exception import APIGatewayException
from apigateway_helpers.headers import get_response_headers

queue_url_cache = {}
sqs_client = boto3.client("sqs")

sqs_max_batch_delete = 10

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    event["request-body"] = json.loads(event["body"])
    
    receipt_handles = None
    
    try:
        receipt_handles = event["request-body"]["receipt-handles"]
        if len(receipt_handles) == 0:
            raise Exception
    except:
        raise APIGatewayException("Value for \"receipt-handles\" must be an array including at least one string.", 400)
    
    sqs_queue_name = get_queue_name(event)
    
    try:
        queue_url = get_queue_url(sqs_queue_name)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
            raise APIGatewayException("Room session doesn't exist or you don't have access to it.", 400)
        raise
    
    
    # Format each receipt handle into expected format for boto3.
    
    receipt_handle_entries = []
    
    for i, each_receipt_handle in enumerate(receipt_handles):
        receipt_handle_entries.append({
            "Id": "{}".format(i),
            "ReceiptHandle": each_receipt_handle
        })
    
    for each_receipt_handle_group in chunker(receipt_handle_entries, sqs_max_batch_delete):
        response = sqs_client.delete_message_batch(
            QueueUrl = queue_url,
            Entries = each_receipt_handle_group
        )
        
        failed_deletes = response.get("Failed", [])
        
        if len(failed_deletes) > 0:
            print("Failed delete(s): {}".format(json.dumps(failed_deletes)))
    
    return {}

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

# http://stackoverflow.com/a/434328
def chunker(seq, size):
    return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))

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