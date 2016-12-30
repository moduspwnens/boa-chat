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

import os
import json
import boto3
import botocore
import cfnresponse

s3_client = boto3.client("s3")
sns_client = boto3.client("sns")
sqs_client = boto3.client("sqs")
logs_client = boto3.client("logs")
apig_client = boto3.client("apigateway")

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))

    request_type = event.get("RequestType")

    if request_type == "Delete":
        handle_cleanup_event(event, context)

    cfnresponse.send(event, context, cfnresponse.SUCCESS, {}, None)

    return {}

def handle_cleanup_event(event, context):
    
    resource_props = event.get("ResourceProperties", {})
    
    bucket_content_type = resource_props.get("BucketContentType")
    
    if bucket_content_type == "Default":
        
        aws_region = context.invoked_function_arn.split(":")[3]
        aws_account_id = context.invoked_function_arn.split(":")[4]
        
        cleanup_sns_topics()
        
        cleanup_log_groups(aws_region, aws_account_id)
        
        cleanup_sqs_queues()
        
        cleanup_s3_bucket(resource_props["Bucket"])
    
    elif bucket_content_type == "PrecreatedApiKey":
        
        cleanup_precreated_api_keys(resource_props["Bucket"])
        
        cleanup_s3_bucket(resource_props["Bucket"])
    
    else:
        cleanup_s3_bucket(resource_props["Bucket"])

def cleanup_sns_topics():
    
    print("Listing SNS topics to clean up.")
    
    stack_topic_prefix = "{}-".format(os.environ["PROJECT_GLOBAL_PREFIX"])
    
    for each_response in sns_client.get_paginator('list_topics').paginate():
        topic_arns_list = list(x["TopicArn"] for x in each_response.get("Topics", []))
        
        topics_to_delete = []
        for each_topic_arn in topic_arns_list:
            each_topic_name = ":".join(each_topic_arn.split(":")[5:])
            if each_topic_name.startswith(stack_topic_prefix):
                topics_to_delete.append(each_topic_arn)
        
        for each_topic_arn in topics_to_delete:
            print("Deleting SNS topic: {}".format(each_topic_arn))
            
            try:
                sns_client.delete_topic(
                    TopicArn = each_topic_arn
                )
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'AuthorizationError':
                    print("Unauthorized to delete room topic. Presumed already deleted.")
                else:
                    raise

def cleanup_log_groups(aws_region, aws_account_id):
    
    prefix_list = []
    
    # Log groups created for SNS delivery logs.
    prefix_list.append(
        "sns/{aws_region}/{aws_account_id}/{project_prefix}-".format(
            aws_region = aws_region,
            aws_account_id = aws_account_id,
            project_prefix = os.environ["PROJECT_GLOBAL_PREFIX"]
        )
    )
    
    for each_prefix in prefix_list:
        
        print("Listing CloudWatch log groups to clean up starting with {}".format(each_prefix))
        
        response_iterator = logs_client.get_paginator("describe_log_groups").paginate(
            logGroupNamePrefix = each_prefix
        )
        
        for each_response in response_iterator:
            log_group_names = list(x["logGroupName"] for x in each_response.get("logGroups", []))
            
            for each_log_group_name in log_group_names:
                print("Deleting CloudWatch log group: {}".format(each_log_group_name))
                
                try:
                    logs_client.delete_log_group(
                        logGroupName = each_log_group_name
                    )
                except botocore.exceptions.ClientError as e:
                    if e.response['Error']['Code'] == 'ResourceNotFoundException':
                        print("Log group already deleted.")
                    else:
                        raise

def cleanup_sqs_queues():
    
    print("Listing SQS queues to clean up.")
    
    deleted_queue_url_map = {}
    
    while True:
    
        response = sqs_client.list_queues(
            QueueNamePrefix = "{}-".format(
                os.environ["PROJECT_GLOBAL_PREFIX"]
            )
        )
        
        queue_urls = response.get("QueueUrls", [])
        
        if len(queue_urls) == 0:
            print("Request for stack's queues returned no results.")
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

def cleanup_s3_bucket(s3_bucket_name):
    
    print("Deleting objects in S3 bucket: {}".format(s3_bucket_name))
    
    response_iterator = s3_client.get_paginator("list_objects_v2").paginate(
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
    
    if len(keys_to_delete) > 0:
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

def cleanup_precreated_api_keys(s3_bucket_name):
    
    print("Deleting precreated API keys in S3 bucket: {}".format(s3_bucket_name))
    
    response_iterator = s3_client.get_paginator("list_objects_v2").paginate(
        Bucket = s3_bucket_name,
        Prefix = "generated-api-keys/"
    )

    for each_list_response in response_iterator:
        for each_item in each_list_response.get("Contents", []):
            each_key = each_item["Key"]
            
            try:
                response = s3_client.get_object(
                    Bucket = s3_bucket_name,
                    Key = each_key
                )
            except botocore.exceptions.ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchKey":
                    # Object is already deleted.
                    continue
                else:
                    raise
            
            api_key_dict = json.loads(response["Body"].read())
            api_key_id = api_key_dict["api-key-id"]
            
            print("Deleting API Key: {}".format(api_key_id))
            
            try:
                apig_client.delete_api_key(
                    apiKey = api_key_id
                )
            except botocore.exceptions.ClientError as e:
                if e.response["Error"]["Code"] == "NotFoundException":
                    print("API Key not found. Assumed already deleted.")
                else:
                    raise