from __future__ import print_function

import json, time, hashlib, boto3

queue_url_cache = {}
sqs_client = boto3.client("sqs")
s3_client = boto3.client("s3")

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    if event.get("user-id", "") == "":
        raise APIGatewayException("URL parameter \"user-id\" is required.", 400)
    
    sqs_queue_name = get_queue_name(event)
    if sqs_queue_name not in queue_url_cache:
        create_and_initialize_queue(sqs_queue_name, event)
    
    queue_url = queue_url_cache[sqs_queue_name]
    
    response = sqs_client.receive_message(
        QueueUrl = queue_url,
        MaxNumberOfMessages = 10,
        WaitTimeSeconds = 20
    )
    
    return {
        "messages": list(x["Body"] for x in response.get("Messages", []))
    }

def create_and_initialize_queue(sqs_queue_name, event):
    s3_bucket_name = "webchat-sharedbucket-{}".format(event["api-id"])
    room_info_dict = json.loads(s3_client.get_object(Bucket=s3_bucket_name, Key="room-topics/{}.json".format(event["room-id"]))["Body"].read())
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
        "sns-subscription-arn": subscribe_response["SubscriptionArn"]
    }

    s3_client.put_object(
        Bucket = s3_bucket_name,
        Key = "room-queues/{}/{}.json".format(
            event["room-id"],
            event["user-id"]
        ),
        Body = json.dumps(s3_queue_config_object, indent=4)
    )
    
    queue_url_cache[sqs_queue_name] = queue_url

def get_queue_name(event):
    
    hash_string_base = "{}-{}-{}-{}".format(
        event["api-id"],
        event["stage"],
        event["room-id"],
        event["user-id"]
    )
    
    return "web-chat-{}".format(
        hashlib.md5(hash_string_base).hexdigest()
    )

def get_default_queue_attributes(event, sns_topic_arn):
    
    statements_list = [
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
            "Sid": "AllowRoomPollerActions",
            "Effect": "Allow",
            "Principal": {
                "AWS": event["function-role"]
            },
            "Action": [
                "sqs:ReceiveMessage",
                "sqs:DeleteMessage"
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
    
    return {
        "Policy": json.dumps({
            "Version": "2012-10-17",
            "Statement": statements_list
        })
    }

class APIGatewayException(Exception):

    def __init__(self, message, http_status_code = 500):

        # Encode this exception as a JSON object so it can be decoded by API Gateway.
        new_message_object = {
            "http-status": http_status_code,
            "message": message
        }
        new_message = json.dumps(new_message_object, separators=(",", ":"))
        Exception.__init__(self, new_message)