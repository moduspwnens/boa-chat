"""RoomMessagePosterFunction

Allows posting a message to a room. Returns the message ID of the posted 
message.

"""

from __future__ import print_function

import os
import json
import time
import boto3
import botocore
from apigateway_helpers.exception import APIGatewayException
from apigateway_helpers.headers import get_response_headers

client_message_id_max_length = 36

sns_client = boto3.client("sns")
cognito_idp_client = boto3.client("cognito-idp")
logs_client = boto3.client("logs")

room_streams_created_map = {}

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    event["request-body"] = json.loads(event["body"])
    
    cognito_identity_id = event["requestContext"]["identity"]["cognitoIdentityId"]
    
    if event["request-body"].get("version", "1") != "1":
        raise APIGatewayException("Unsupported message version: {}".format(event["request-body"]["version"]), 400)
    
    client_message_id = event["request-body"].get("client-message-id")
    
    if client_message_id is not None and len(client_message_id) > client_message_id_max_length:
        raise APIGatewayException("Parameter \"client-message-id\" must be {} bytes or fewer.".format(client_message_id_max_length), 400)
    
    room_id = event["pathParameters"]["room-id"]
    
    sns_topic_arn = get_room_topic_arn(event, context, room_id)
    
    user_profile_dataset_name = os.environ["COGNITO_USER_PROFILE_DATASET_NAME"]
    identity_pool_id = event["requestContext"]["identity"]["cognitoIdentityPoolId"]
    
    cognito_auth_provider_string = event["requestContext"]["identity"]["cognitoAuthenticationProvider"]
    cognito_idp_name = cognito_auth_provider_string.split(",")[0]
    user_pool_id = "/".join(cognito_idp_name.split("/")[1:])
    cognito_user_pool_sub_value = cognito_auth_provider_string.split(",")[1].split(":")[2]
    
    
    author_name = cognito_identity_id
    
    response = cognito_idp_client.list_users(
        UserPoolId = user_pool_id,
        AttributesToGet = ["email"],
        Filter = "sub = \"{}\"".format(cognito_user_pool_sub_value),
        Limit = 1
    )

    author_name = response["Users"][0]["Attributes"][0]["Value"]
    
    message_object = {
        "identity-id": cognito_identity_id,
        "author-name": author_name,
        "message": event["request-body"].get("message", ""),
        "timestamp": int(time.time())
    }
    
    if client_message_id is not None:
        message_object["client-message-id"] = client_message_id
    
    try:
        response = sns_client.publish(
            TopicArn = sns_topic_arn,
            Message = json.dumps(message_object)
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] in ['InvalidParameter', 'AuthorizationError']:
            raise APIGatewayException("Room \"{}\" either doesn't exist or you don't have access to it.".format(room_id), 400)
        else:
            raise
    
    
    return {
        "message-id": response["MessageId"]
    }

def generate_room_sns_topic_name(room_id):
    return "{}-{}".format(
        os.environ["PROJECT_GLOBAL_PREFIX"],
        room_id
    )

def get_room_topic_arn(event, context, room_id):
    sns_topic_name = generate_room_sns_topic_name(room_id)
    
    return "arn:aws:sns:{aws_region}:{aws_account_id}:{sns_topic_name}".format(
        aws_region = context.invoked_function_arn.split(":")[3],
        aws_account_id = context.invoked_function_arn.split(":")[4],
        sns_topic_name = sns_topic_name
    )

def proxy_lambda_handler(event, context):
    
    response_headers = get_response_headers(event, context)
    
    try:
        return_dict = lambda_handler(event, context)
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
        "body": json.dumps(return_dict)
    }