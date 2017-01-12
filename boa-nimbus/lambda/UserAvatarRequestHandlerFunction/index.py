"""UserAvatarRequestHandlerFunction

Fetches the Gravatar of a user.

Using this Lambda-backed API Gateway endpoint as a proxy, we avoid having to 
expose the plain MD5 hash of each user's e-mail address. This allows for more 
realistic e-mail address privacy.

"""

from __future__ import print_function

import os
import json
import time
import base64
import hashlib
from datetime import datetime
import requests
import boto3
import botocore
from apigateway_helpers.exception import APIGatewayException
from apigateway_helpers.headers import get_response_headers as get_base_response_headers

cognito_identity_client = boto3.client("cognito-identity")
cognito_idp_client = boto3.client("cognito-idp")
cognito_sync_client = boto3.client("cognito-sync")
s3_client = boto3.client("s3")

shared_bucket_name = os.environ["SHARED_BUCKET"]
identity_pool_id = os.environ["COGNITO_IDENTITY_POOL_ID"]
user_pool_id = os.environ["COGNITO_USER_POOL_ID"]
user_profile_dataset_name = os.environ["COGNITO_USER_PROFILE_DATASET_NAME"]

cached_gravatars_prefix = "cached-gravatars/"
http_strftime_format = "%a, %d %b %Y %H:%M:%S %Z"

def lambda_handler(event, context):
    
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    identity_id = event["pathParameters"].get("user-id", "")
    
    if identity_id == "":
        raise APIGatewayException("Parameter \"user-id\" specified in path must be longer than zero characters.", 400)
    
    user_specified_author_avatar_hash = event["queryStringParameters"].get("hash")
    
    # Pixels
    image_size = 80
    
    if "s" in event["queryStringParameters"]:
        try:
            image_size = int(event["queryStringParameters"]["s"])
            if image_size < 1:
                raise Exception
            if image_size > 2048:
                raise Exception
        except:
            raise APIGatewayException("Parameter \"s\" must be a positive integer up to 2048.", 400)
    
    cached_avatar_available = False
    cached_avatar_last_modified_string = None
    force_fresh_gravatar_pull = False
    
    try:
        response = s3_client.head_object(
            Bucket = shared_bucket_name,
            Key = get_cached_gravatar_s3_key(identity_id, image_size)
        )
        
        expires_datetime = datetime.strptime(response["Metadata"]["expires"], http_strftime_format)
        
        current_datetime = datetime.utcnow().replace(tzinfo=expires_datetime.tzinfo)
        
        seconds_until_expiration = int((expires_datetime - current_datetime).total_seconds())
        
        if seconds_until_expiration > 0:
            cached_avatar_available = True
            print("Expires in {} second(s).".format(seconds_until_expiration))
        else:
            print("Cached avatar expired {} second(s) ago.".format(-1 * seconds_until_expiration))
        
        cached_avatar_last_modified_string = response["Metadata"].get("source-last-modified")
        
        if "author-avatar-hash" in response["Metadata"] and user_specified_author_avatar_hash is not None:
            if user_specified_author_avatar_hash != response["Metadata"]["author-avatar-hash"]:
                cached_avatar_available = False
                force_fresh_gravatar_pull = True
                print("Cached avatar is for a different e-mail address than user requested.")
        
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            pass
        else:
            raise
    
    if cached_avatar_available:
        print("Cached avatar not yet expired. Returning it.")
        
        return return_cached_object(identity_id, image_size)
    
    
    try:
        response = cognito_sync_client.list_records(
            IdentityPoolId = identity_pool_id,
            IdentityId = identity_id,
            DatasetName = user_profile_dataset_name
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ValidationException':
            raise APIGatewayException("Parameter \"user-id\" specified in path does not correspond to a valid user.", 400)
        else:
            raise
    
    user_pool_user_id = None
    
    for each_record in response.get("Records", []):
        if each_record["Key"] == "user-id":
            user_pool_user_id = each_record["Value"]
            break
    
    if user_pool_user_id is None:
        raise APIGatewayException("Parameter \"user-id\" specified in path does not correspond to a valid user.", 400)
    
    response = cognito_idp_client.admin_get_user(
        UserPoolId = user_pool_id,
        Username = user_pool_user_id
    )
    
    user_email_address = None
    user_email_address_verified = False
    user_sub = None
    
    for each_attribute_set in response.get("UserAttributes", []):
        if each_attribute_set["Name"] == "email":
            user_email_address = each_attribute_set["Value"]
        elif each_attribute_set["Name"] == "email_verified":
            user_email_address_verified = each_attribute_set["Value"]
        elif each_attribute_set["Name"] == "sub":
            user_sub = each_attribute_set["Value"]
    
    author_avatar_hash = hashlib.md5("{}{}".format(user_sub, user_email_address)).hexdigest()
    
    if user_email_address is None:
        raise Exception("Unable to find e-mail address in Cogito User Pool record.")
    elif not user_email_address_verified:
        raise Exception("User's e-mail address is not yet verified.")
    
    print("Request is for avatar of user with e-mail address: {}".format(user_email_address))
    
    # http://en.gravatar.com/site/implement/hash/
    email_address_gravatar_hash = hashlib.md5(user_email_address.strip().lower()).hexdigest()
    
    request_kwargs = {
        "params": {
            "s": str(image_size),
            "r": "pg",
            "d": "identicon"
        },
        "headers": {}
    }
    
    if cached_avatar_last_modified_string is not None and not force_fresh_gravatar_pull:
        print("Last modified: {}".format(cached_avatar_last_modified_string))
        request_kwargs["headers"]["If-Modified-Since"] = cached_avatar_last_modified_string
    
    r = requests.get(
        "https://www.gravatar.com/avatar/{}".format(email_address_gravatar_hash),
        **request_kwargs
    )
    
    r.raise_for_status()
    
    if r.status_code == 304:
        
        print("Gravatar not modified since cached version. Returning cached version.")
        
        response = s3_client.copy_object(
            Bucket = shared_bucket_name,
            Key = get_cached_gravatar_s3_key(identity_id, image_size),
            CopySource = {
                "Bucket": shared_bucket_name,
                "Key": get_cached_gravatar_s3_key(identity_id, image_size)
            },
            MetadataDirective = "REPLACE",
            Metadata = {
                "Author-Avatar-Hash": author_avatar_hash,
                "Expires": r.headers["Expires"],
                "Source-Last-Modified": r.headers["Last-Modified"]
            }
        )
        
        # We can keep serving our cached version.
        return return_cached_object(identity_id, image_size)
        
    else:
        # Save this new version.
        
        print("Caching Gravatar response image and returning live result.")
        
        s3_client.put_object(
            Bucket = shared_bucket_name,
            Key = get_cached_gravatar_s3_key(identity_id, image_size),
            Body = r.content,
            Metadata = {
                "Author-Avatar-Hash": author_avatar_hash,
                "Expires": r.headers["Expires"],
                "Source-Last-Modified": r.headers["Last-Modified"]
            }
        )
    
        return base64.b64encode(r.content)

def get_cached_gravatar_s3_key(identity_id, image_size):
    return "{}{}/{}.png".format(
        cached_gravatars_prefix,
        identity_id,
        image_size
    )

def return_cached_object(identity_id, image_size):
    
    response = s3_client.get_object(
        Bucket = shared_bucket_name,
        Key = get_cached_gravatar_s3_key(identity_id, image_size)
    )
    
    return base64.b64encode(response["Body"].read())

def proxy_lambda_handler(event, context):
    
    response_headers = get_response_headers(event, context)
    
    try:
        return_var = lambda_handler(event, context)
    except APIGatewayException as e:
        return {
            "statusCode": e.http_status_code,
            "headers": response_headers,
            "body": json.dumps({
                "message": e.http_status_message
            })
        }
    
    return {
        "statusCode": 200,
        "headers": response_headers,
        "body": return_var
    }