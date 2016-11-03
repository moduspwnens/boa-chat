"""S3ObjectWriterFunction

Used as a CloudFormation custom resource to create / update an S3 object 
on create and delete it upon delete.

"""

from __future__ import print_function

import json
import cfnresponse
import boto3

s3_client = boto3.client("s3")

handler_object = None
def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    request_type = event.get("RequestType")
    
    resource_properties = event["ResourceProperties"]
    
    s3_bucket_name = resource_properties["Bucket"]
    s3_object_key = resource_properties["Key"]
    
    if request_type in ["Create", "Update"]:
        
        s3_object_content = resource_properties["Content"]
        s3_object_metadata = resource_properties.get("Metadata", {})
        
        put_object_kwargs = {
            "Bucket": s3_bucket_name,
            "Key": s3_object_key,
            "Body": s3_object_content,
            "Metadata": s3_object_metadata
        }
        
        if "Content-Type" in resource_properties:
            put_object_kwargs["ContentType"] = resource_properties["Content-Type"]
        
        s3_client.put_object(**put_object_kwargs)
        
    elif request_type == "Delete":
        
        s3_client.delete_object(
            Bucket = s3_bucket_name,
            Key = s3_object_key
        )
        
    cfnresponse.send(event, context, cfnresponse.SUCCESS, {}, None)

    return {}