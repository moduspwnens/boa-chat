"""RoomLogEventProcessorFunction

Used as a subscription filter to room event logs to send events to S3 for 
durable long-term storage.

"""

from __future__ import print_function

import json
import boto3
import botocore

s3_client = boto3.client("s3")

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    for each_record in event["Records"]:
        sns_message = each_record["Sns"]
        sns_topic_arn = sns_message["TopicArn"]
        
        room_id = "-".join(sns_topic_arn.split(":")[5].split("-")[1:])
        message_id = sns_message["MessageId"]
        event_object = json.loads(sns_message["Message"])
        
        print("Room ID: {}".format(room_id))
        print("Message ID: {}".format(message_id))
        print("Event: {}".format(json.dumps(event_object)))
        

    return {}