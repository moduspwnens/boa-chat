"""StackCleanupFunction

Cleans up leftover resources upon stack deletion.

This function ensures dangling resources created through the app's usage (not
through CloudFormation) are deleted, too.

This includes:
 * S3 bucket objects
 * SNS topics
 * SQS queues
 * CloudWatch log groups

"""

from __future__ import print_function

import json
import boto3, botocore
import cfnresponse

s3_client = boto3.client("s3")
sns_client = boto3.client("sns")
sqs_client = boto3.client("sqs")
logs_client = boto3.client("logs")

class LambdaHandler(object):
    
    def __init__(self, context):
        pass

    def handle_event(self, event, context):
        print("Event: {}".format(json.dumps(event)))

        request_type = event.get("RequestType")

        if request_type == "Delete":
            self.handle_cleanup_event(event, context)

        cfnresponse.send(event, context, cfnresponse.SUCCESS, {}, None)

        return {}

    def handle_cleanup_event(self, event, context):
        
        s3_bucket_name = event["ResourceProperties"]["Bucket"]
        bucket_content_type = event["ResourceProperties"].get("BucketContentType")

        paginator = s3_client.get_paginator("list_objects_v2")

        response_iterator = paginator.paginate(
            Bucket = s3_bucket_name
        )

        for each_list_response in response_iterator:
          keys_to_delete = []

          for each_item in each_list_response.get("Contents", []):
              keys_to_delete.append(each_item["Key"])

          if len(keys_to_delete) == 0:
              print("Last request for objects in {} returned none.".format(
                  s3_bucket_name
              ))
              break
          
          if bucket_content_type != "Static Content":
              # Also delete other resources specified by the S3 objects' contents.
              
              for each_key in keys_to_delete:
                  if each_key.startswith("room-topics/"):
                      # This S3 object represents an SNS topic that needs to be deleted.
                      room_topic_config = json.loads(s3_client.get_object(Bucket = s3_bucket_name, Key = each_key)["Body"].read())
                      sns_topic_arn = room_topic_config["sns-topic-arn"]
                      print("Deleting {}.".format(sns_topic_arn))
                      sns_client.delete_topic(TopicArn = sns_topic_arn)
                  
                      log_group_name = room_topic_config["log-group"]
                  
                      print("Deleting {}.".format(log_group_name))
                      logs_client.delete_log_group(logGroupName=log_group_name)
              
                  elif each_key.startswith("room-queues/"):
                      # This S3 object represents an SQS queue that needs to be deleted.
                      queue_config = json.loads(s3_client.get_object(Bucket = s3_bucket_name, Key = each_key)["Body"].read())
                      sqs_queue_url = queue_config["sqs-queue-url"]
                      try:
                          print("Deleting {}.".format(sqs_queue_url))
                          sqs_client.delete_queue(QueueUrl = sqs_queue_url)
                      except botocore.exceptions.ClientError as e:
                          if e.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
                              pass
                          else:
                              raise
          
          print("Deleting {} object(s) from {}.".format(
              len(keys_to_delete),
              s3_bucket_name
          ))

          s3_client.delete_objects(
              Bucket = s3_bucket_name,
              Delete = {
                  "Objects": list({"Key": x} for x in keys_to_delete)
              }
          )

          print("Object(s) deleted.")

handler_object = None
def lambda_handler(event, context):
    global handler_object

    if handler_object is None:
        handler_object = LambdaHandler(context)

    return handler_object.handle_event(event, context)
    