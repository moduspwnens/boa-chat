"""RoomLogEventProcessorFunction

Used as a subscription filter to room event logs to send events to S3 for 
durable long-term storage.

"""

from __future__ import print_function

import os
import json
import datetime
import boto3
import botocore

s3_client = boto3.client("s3")

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    s3_bucket_name = os.environ["SHARED_BUCKET"]
    
    for each_record in event["Records"]:
        sns_message = each_record["Sns"]
        sns_topic_arn = sns_message["TopicArn"]
        
        room_id = "-".join(sns_topic_arn.split(":")[5].split("-")[1:])
        message_id = sns_message["MessageId"]
        event_object = json.loads(sns_message["Message"])
        
        print("Room ID: {}".format(room_id))
        print("Message ID: {}".format(message_id))
        print("Event: {}".format(json.dumps(event_object)))
        
        s3_client.put_object(
            Bucket = s3_bucket_name,
            Key = get_s3_key_for_room_event(room_id, message_id, event_object),
            Body = json.dumps(event_object),
            ContentType = "application/json"
        )

    return {}

def get_s3_key_for_room_event(room_id, message_id, event_object):
    
    event_timestamp = event_object["timestamp"]
    event_datetime = datetime.datetime.utcfromtimestamp(event_timestamp)
    
    return "room-event-logs/{}/reverse/{}-{}-{}.json".format(
        room_id,
        get_reverse_lexi_string_for_timestamp(event_timestamp),
        event_timestamp,
        message_id
    )

def get_reverse_lexi_string_for_timestamp(timestamp):
    timestamp_string = str(timestamp).zfill(10)
    
    character_list = []
    
    for each_character in timestamp_string:
        new_character = 9 - int(each_character)
        character_list.append(str(new_character))
    
    return "".join(character_list)
    