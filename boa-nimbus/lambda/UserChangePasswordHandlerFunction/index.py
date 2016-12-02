"""UserChangePasswordHandlerFunction

Handles requests to change a user's password.

"""

from __future__ import print_function

import os
import json
import boto3
import botocore
from apigateway_helpers.exception import APIGatewayException
from cognito_helpers import generate_cognito_sign_up_secret_hash

cognito_idp_client = boto3.client("cognito-idp")
cognito_sync_client = boto3.client("cognito-sync")

def lambda_handler(event, context):
    
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    user_pool_id = os.environ["COGNITO_USER_POOL_ID"]
    identity_pool_id = os.environ["COGNITO_IDENTITY_POOL_ID"]
    user_pool_client_id = os.environ["COGNITO_USER_POOL_CLIENT_ID"]
    user_pool_client_secret = os.environ["COGNITO_USER_POOL_CLIENT_SECRET"]
    user_profile_dataset_name = os.environ["COGNITO_USER_PROFILE_DATASET_NAME"]
    
    new_password = event["request-body"].get("password")
    
    if new_password is None:
        raise APIGatewayException("Value for \"password\" must be specified in request body.", 400)
    
    
    user_id = None
    password_change_method = None
    old_password = None
    password_reset_code = None
    
    if event["resource-path"] == "/user/password":
        print("Authenticated user password change request.")
        
        password_change_method = "Authenticated"
        
        identity_id = event["cognito-identity-id"]
        
        response = cognito_sync_client.list_records(
            IdentityPoolId = identity_pool_id,
            IdentityId = identity_id,
            DatasetName = user_profile_dataset_name
        )
        
        for each_record in response["Records"]:
            if each_record["Key"] == "user-id":
                user_id = each_record["Value"]
                break
        
        # We require the user's current password in addition to the new password.
        
        old_password = event["request-body"].get("old-password")
    
        if old_password is None:
            raise APIGatewayException("Value for \"old-password\" must be specified in request body.", 400)
    
    elif event["resource-path"] == "/user/forgot/password":
        print("Unathenticated (forgotten) user password change request.")
        
        password_change_method = "Unauthenticated"
        
        user_id = event["request-body"].get("email-address")
    
        if user_id is None:
            raise APIGatewayException("Value for \"email-address\" must be specified in request body.", 400)
        
        # We require the a password reset code in addition to the new password.
        
        password_reset_code = event["request-body"].get("token")
    
        if password_reset_code is None:
            raise APIGatewayException("Value for \"token\" must be specified in request body.", 400)
    
    if password_change_method is None:
        raise APIGatewayException("Unsure how to process request.")
    
        
    
    secret_hash = generate_cognito_sign_up_secret_hash(user_id, user_pool_client_id, user_pool_client_secret)
    
    if password_change_method == "Authenticated":
        
        try:
            response = cognito_idp_client.admin_initiate_auth(
                AuthFlow = "ADMIN_NO_SRP_AUTH",
                UserPoolId = user_pool_id,
                ClientId = user_pool_client_id,
                AuthParameters = {
                    "USERNAME": user_id,
                    "SECRET_HASH": secret_hash,
                    "PASSWORD": old_password
                }
            )
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NotAuthorizedException':
                raise APIGatewayException("Password provided is incorrect.", 400)
            elif e.response['Error']['Code'] == 'ParamValidationError':
                raise APIGatewayException("New password does not meet password requirements.", 400)
            else:
                raise
        
        access_token = response["AuthenticationResult"]["AccessToken"]
        
        try:
            cognito_idp_client.change_password(
                PreviousPassword = old_password,
                ProposedPassword = new_password,
                AccessToken = access_token
            )
        except botocore.exceptions.ParamValidationError as e:
            raise APIGatewayException("New password does not meet password requirements.", 400)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'InvalidPasswordException':
                raise APIGatewayException("New password does not meet password requirements.", 400)
        
        
    elif password_change_method == "Unauthenticated":
        
        try:
            cognito_idp_client.confirm_forgot_password(
                ClientId = user_pool_client_id,
                SecretHash = secret_hash,
                Username = user_id,
                ConfirmationCode = password_reset_code,
                Password = new_password
            )
        except botocore.exceptions.ParamValidationError as e:
            raise APIGatewayException("New password does not meet password requirements.", 400)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] in ['CodeMismatchException', 'ExpiredCodeException']:
                raise APIGatewayException("Invalid password reset code.", 400)
            elif e.response['Error']['Code'] == 'ParamValidationError':
                raise APIGatewayException("New password does not meet password requirements.", 400)
            elif e.response['Error']['Code'] == 'InvalidPasswordException':
                raise APIGatewayException("New password does not meet password requirements.", 400)
            else:
                raise
    
    return {
        "message": "Password changed successfully."
    }