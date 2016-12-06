"""SwaggerTemplatePresetFunction

A CloudFormation custom resource.

Downloads a Swagger file from S3, replaces region and AWS account IDs with the 
correct values, re-uploads the file and returns the S3 Bucket and Key for the 
new template.

"""

from __future__ import print_function

import json
import boto3
import botocore
import cfnresponse

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))

    request_type = event.get("RequestType")
    resource_props = event["ResourceProperties"]
    
    response_data = {}
    
    if request_type in ["Create", "Update"]:
        
        source_file_content = s3_client.get_object(Bucket = resource_props["SourceBucket"], Key = resource_props["SourceKey"])["Body"].read()
        
        aws_region = context.invoked_function_arn.split(":")[3]
        aws_account_id = context.invoked_function_arn.split(":")[4]
        
        replacements_map = {
            ":aws-region:": ":{}:".format(aws_region),
            ":000000000000:": ":{}:".format(aws_account_id)
        }
        
        dest_file_content = source_file_content
        
        for each_key in replacements_map.keys():
            each_value = replacements_map[each_key]
            
            dest_file_content = dest_file_content.replace(each_key, each_value)
        
        s3_client.put_object(
            Bucket = resource_props["OutputBucket"],
            Key = resource_props["OutputKey"],
            Body = dest_file_content
        )
        
        response_data["OutputBucket"] = resource_props["OutputBucket"]
        response_data["OutputKey"] = resource_props["OutputKey"]
    
    elif request_type == "Delete":
        s3_client.delete_object(
            Bucket = resource_props["OutputBucket"],
            Key = resource_props["OutputKey"]
        )

    cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, None)

    return {}