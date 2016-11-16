"""CognitoUserPoolResourceFunction

Used as a CloudFormation custom resource to create / update / delete 
the Cognito User Pool.

"""

from __future__ import print_function

import json
import cfnresponse
import boto3

s3_client = boto3.client("s3")
cognito_client = boto3.client("cognito-idp")
cognito_user_pool_config_s3_key = "cognito-user-pool.json"

handler_object = None
def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    request_type = event.get("RequestType")
    
    resource_properties = event["ResourceProperties"]
    stack_name = event["StackId"].split(":")[5].split("/")[1]
    s3_bucket_name = resource_properties["SharedBucket"]
    
    response_data = {}
    
    if request_type in ["Create"]:
        response = cognito_client.create_user_pool(
            PoolName = stack_name,
            AutoVerifiedAttributes = ["email"]
        )
        
        user_pool_id = response["UserPool"]["Id"]
        user_pool_name = response["UserPool"]["Name"]
        
        s3_client.put_object(
            Bucket = s3_bucket_name,
            Key = cognito_user_pool_config_s3_key,
            Body = json.dumps({
                "id": user_pool_id,
                "name": user_pool_name
            })
        )
        
    elif request_type == "Delete":
        
        response = s3_client.get_object(
            Bucket = s3_bucket_name,
            Key = cognito_user_pool_config_s3_key
        )
        
        user_pool_id = json.loads(response["Body"].read())["id"]
        
        cognito_client.delete_user_pool(
            UserPoolId = user_pool_id
        )
        
        s3_client.delete_object(
            Bucket = s3_bucket_name,
            Key = cognito_user_pool_config_s3_key
        )
    
    cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, None)

    return {}