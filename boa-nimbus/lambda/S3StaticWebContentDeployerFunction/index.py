"""S3StaticWebContentDeployerFunction

Used as a CloudFormation custom resource.

Downloads a pre-uploaded ZIP file from the specified S3 bucket, unzips it, 
then uploads its contents to a different S3 bucket.

"""

from __future__ import print_function

import os
import zipfile
import tempfile
import shutil
import json
import mimetypes
import boto3
import cfnresponse

s3_resource = boto3.resource("s3")

temporary_directory = "/tmp"

def lambda_handler(event, context):
    print('Event: {}'.format(json.dumps(event)))
    
    request_type = event.get("RequestType")
    
    resource_properties = event["ResourceProperties"]
    
    source_s3_bucket = resource_properties["Source"]["S3Bucket"]
    source_s3_key = resource_properties["Source"]["S3Key"]
    
    target_s3_bucket = resource_properties["Target"]["S3Bucket"]
    target_s3_key_prefix = resource_properties["Target"]["S3KeyPrefix"]

    if request_type in ["Create", "Update"]:
        
        f = tempfile.NamedTemporaryFile(delete=False)
        f.close()
        
        downloaded_file_path = f.name
        
        temp_dir = tempfile.mkdtemp()
        
        s3_resource.meta.client.download_file(
            source_s3_bucket,
            source_s3_key,
            downloaded_file_path
        )
        
        zfile = zipfile.ZipFile(downloaded_file_path)
        zfile.extractall(temp_dir)
        zfile.close()
        
        for dir_name, subdir_list, file_list in os.walk(temp_dir):
            for each_file_name in file_list:
                
                if each_file_name in [".DS_Store"]:
                    continue
                
                file_path = os.path.join(dir_name, each_file_name)
                
                relative_path = file_path[len(temp_dir)+1:]
                
                file_s3_key = target_s3_key_prefix + relative_path
                
                extra_args = {}
                
                mime_type = mimetypes.MimeTypes().guess_type(each_file_name)[0]
                
                if mime_type is not None:
                    extra_args["ContentType"] = mime_type
                    print("Uploading {} ({})".format(file_s3_key, mime_type))
                else:
                    print("Uploading {}".format(file_s3_key))    
                
                
                s3_resource.meta.client.upload_file(
                    file_path,
                    target_s3_bucket,
                    file_s3_key,
                    ExtraArgs = extra_args
                )
        
        
        os.unlink(downloaded_file_path)
        shutil.rmtree(temp_dir)

    cfnresponse.send(event, context, cfnresponse.SUCCESS, {}, None)

    return {}