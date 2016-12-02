"""UserLoginHandlerFunction

Validates user login credentials and returns API access credentials if 
successful.

"""

from __future__ import print_function

import os
import json
import copy
import datetime
import calendar
import time
import boto3
import botocore
from apigateway_helpers.exception import APIGatewayException
from cognito_helpers import generate_cognito_sign_up_secret_hash
from project_local.generate_api_key import create_api_key_for_user_if_not_exists

cognito_idp_client = boto3.client("cognito-idp")
cognito_identity_client = boto3.client("cognito-identity")
cognito_sync_client = boto3.client("cognito-sync")

def lambda_handler(event, context):
    
    event_for_logging = copy.deepcopy(event)
    
    if "request-body" in event_for_logging and "password" in event_for_logging["request-body"]:
        event_for_logging["request-body"]["password"] = "********"
    
    print("Event: {}".format(json.dumps(event_for_logging)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    user_pool_id = os.environ["COGNITO_USER_POOL_ID"]
    user_pool_client_id = os.environ["COGNITO_USER_POOL_CLIENT_ID"]
    user_pool_client_secret = os.environ["COGNITO_USER_POOL_CLIENT_SECRET"]
    user_profile_dataset_name = os.environ["COGNITO_USER_PROFILE_DATASET_NAME"]
    identity_pool_id = os.environ["COGNITO_IDENTITY_POOL_ID"]
    s3_bucket_name = os.environ["SHARED_BUCKET"]
    stack_name = os.environ["STACK_NAME"]
    usage_plan_id = os.environ["USAGE_PLAN_ID"]
    
    email_address = event["request-body"].get("email-address", "")
    identity_id = event["request-body"].get("user-id", "")
    user_id = None
    
    submitted_password = event["request-body"].get("password", "")
    submitted_refresh_token = event["request-body"].get("refresh-token", None)
    
    auth_flow = None
    auth_parameters = {}
    
    if event["resource-path"] == "/user/login":
        auth_flow = "ADMIN_NO_SRP_AUTH"
        
        if submitted_password == "":
            raise APIGatewayException("Value for \"password\" must be specified in request body.", 400)
        
        if email_address == "":
            raise APIGatewayException("Value for \"email-address\" must be specified in request body.", 400)
        
        auth_parameters["PASSWORD"] = submitted_password
        auth_parameters["USERNAME"] = email_address
        
    elif event["resource-path"] == "/user/refresh":
        auth_flow = "REFRESH_TOKEN_AUTH"
        
        if identity_id == "":
            raise APIGatewayException("Value for \"user-id\" must be specified in request body.", 400)
        
        response = cognito_sync_client.list_records(
            IdentityPoolId = identity_pool_id,
            IdentityId = identity_id,
            DatasetName = user_profile_dataset_name
        )
        
        for each_record in response["Records"]:
            if each_record["Key"] == "user-id":
                user_id = each_record["Value"]
                break
        
        if submitted_refresh_token is None:
            raise APIGatewayException("Value for \"refresh-token\" must be specified in request body.", 400)
        
        auth_parameters["REFRESH_TOKEN"] = submitted_refresh_token
        auth_parameters["USERNAME"] = user_id
    
    secret_hash = generate_cognito_sign_up_secret_hash(auth_parameters["USERNAME"], user_pool_client_id, user_pool_client_secret)
    auth_parameters["SECRET_HASH"] = secret_hash
    
    print("Initiating auth ({}).".format(auth_flow))
    
    try:
        response = cognito_idp_client.admin_initiate_auth(
            UserPoolId = user_pool_id,
            ClientId = user_pool_client_id,
            AuthFlow = auth_flow,
            AuthParameters = auth_parameters
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'UserNotFoundException':
            raise APIGatewayException("User with e-mail address ({}) not found.".format(email_address), 404)
        elif e.response['Error']['Code'] == 'NotAuthorizedException':
            if auth_flow == "ADMIN_NO_SRP_AUTH":
                raise APIGatewayException("Password entered is not correct.", 403)
            elif auth_flow == "REFRESH_TOKEN_AUTH":
                raise APIGatewayException("Refresh token specified is invalid or expired.", 403)
        raise
    
    cognito_id_token = response["AuthenticationResult"]["IdToken"]
    cognito_refresh_token = response["AuthenticationResult"].get("RefreshToken", submitted_refresh_token)
    cognito_access_token = response["AuthenticationResult"]["AccessToken"]
    cognito_access_token_type = response["AuthenticationResult"]["TokenType"]
    
    response = cognito_idp_client.get_user(
        AccessToken = cognito_access_token
    )
    
    user_id = response["Username"]
    
    user_api_key = None
    user_email = None
    
    for each_attribute_pair in response["UserAttributes"]:
        if each_attribute_pair["Name"] == "custom:api_key":
            user_api_key = each_attribute_pair["Value"]
        elif each_attribute_pair["Name"] == "email":
            user_email = each_attribute_pair["Value"]
    
    if user_api_key is None:
        user_api_key = create_api_key_for_user_if_not_exists(
            user_id = user_id, 
            email_address = email_address,
            user_pool_id = user_pool_id,
            stack_name = stack_name,
            usage_plan_id = usage_plan_id,
            s3_bucket_name = s3_bucket_name
        )
    
    cognito_user_pool_provider_name = "cognito-idp.{}.amazonaws.com/{}".format(
        os.environ["AWS_DEFAULT_REGION"],
        user_pool_id
    )
    
    print("Fetching identity id.")
    
    response = cognito_identity_client.get_id(
        IdentityPoolId = identity_pool_id,
        Logins = {
            cognito_user_pool_provider_name: cognito_id_token
        }
    )
    
    identity_id = response["IdentityId"]
    
    response = cognito_sync_client.list_records(
        IdentityPoolId = identity_pool_id,
        IdentityId = identity_id,
        DatasetName = user_profile_dataset_name
    )
    
    sync_session_token = response["SyncSessionToken"]
    
    records_to_replace = {
        "api-key": user_api_key,
        "email-address": user_email,
        "user-id": user_id
    }
    
    for each_record in response["Records"]:
        if each_record["Key"] in records_to_replace and each_record["Value"] == records_to_replace[each_record["Key"]]:
            del records_to_replace[each_record["Key"]]
    
    record_patch_list = []
    
    for each_key in records_to_replace.keys():
        each_value = records_to_replace[each_key]
        record_patch_list.append({
            "Op": "replace",
            "Key": each_key,
            "Value": each_value,
            "SyncCount": 0
        })
    
    if len(record_patch_list) > 0:
        print("Updating identity {} records: {}".format(
            user_profile_dataset_name,
            json.dumps(records_to_replace)
        ))
        response = cognito_sync_client.update_records(
            IdentityPoolId = identity_pool_id,
            IdentityId = identity_id,
            DatasetName = user_profile_dataset_name,
            RecordPatches = record_patch_list,
            SyncSessionToken = sync_session_token
        )
    
    print("Fetching credentials.")
    
    response = cognito_identity_client.get_credentials_for_identity(
        IdentityId = identity_id,
        Logins = {
            cognito_user_pool_provider_name: cognito_id_token
        }
    )
    
    aws_access_key_id = response["Credentials"]["AccessKeyId"]
    aws_secret_access_key = response["Credentials"]["SecretKey"]
    aws_session_token = response["Credentials"]["SessionToken"]
    expiration_timestamp_seconds = calendar.timegm(response["Credentials"]["Expiration"].timetuple())
    
    return {
        "user": {
            "api-key": user_api_key,
            "user-id": identity_id,
            "email-address": user_email
        },
        "credentials": {
            "access-key-id": aws_access_key_id,
            "secret-access-key": aws_secret_access_key,
            "session-token": aws_session_token,
            "expiration": expiration_timestamp_seconds - int(time.time()),
            "refresh-token": cognito_refresh_token
        }
    }