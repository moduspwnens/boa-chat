"""SwaggerTemplatePresetFunction

A CloudFormation custom resource.

Downloads a Swagger file from S3, replaces region and AWS account IDs with the 
correct values, re-uploads the file and returns the S3 Bucket and Key for the 
new template.

"""

from __future__ import print_function

import json
import uuid
import boto3
import botocore
import cfnresponse

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))

    request_type = event.get("RequestType")
    resource_props = event["ResourceProperties"]
    
    physical_resource_id = event.get("PhysicalResourceId")
    
    response_data = {}
    
    if request_type in ["Update", "Delete"]:
        s3_client.delete_object(
            Bucket = resource_props["OutputBucket"],
            Key = get_s3_key_for_physical_resource_id(physical_resource_id)
        )
    
    if request_type in ["Create", "Update"]:
        
        physical_resource_id = "{}".format(uuid.uuid4())
        
        source_file_content = s3_client.get_object(Bucket = resource_props["SourceBucket"], Key = resource_props["SourceKey"])["Body"].read()
        
        aws_region = context.invoked_function_arn.split(":")[3]
        aws_account_id = context.invoked_function_arn.split(":")[4]
        
        replacements_map = {
            ":aws-region:": ":{}:".format(aws_region),
            ":000000000000:": ":{}:".format(aws_account_id),
            "path/000000000000/": "path/{}/".format(aws_account_id)
        }
        
        dest_file_content = source_file_content
        
        for each_key in replacements_map.keys():
            each_value = replacements_map[each_key]
            
            dest_file_content = dest_file_content.replace(each_key, each_value)
        
        s3_client.put_object(
            Bucket = resource_props["OutputBucket"],
            Key = get_s3_key_for_physical_resource_id(physical_resource_id),
            Body = dest_file_content
        )
        
        response_data["OutputBucket"] = resource_props["OutputBucket"]
        response_data["OutputKey"] = get_s3_key_for_physical_resource_id(physical_resource_id)

    cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, None)

    return {}

def get_s3_key_for_physical_resource_id(physical_resource_id):
    return "swagger-apigateway/{}.yaml".format(
        physical_resource_id
    )