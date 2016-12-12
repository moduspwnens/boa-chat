"""UserRegistrationRequestHandlerFunction

Validates an e-mail address and then sends an e-mail with a unique link 
that allows the user to click it to verify their e-mail address.

"""

from __future__ import print_function

import os
import json
import uuid
import time
import boto3
import botocore
import dns.resolver
from apigateway_helpers.exception import APIGatewayException
from apigateway_helpers.headers import get_response_headers
from cognito_helpers import generate_cognito_sign_up_secret_hash

cognito_client = boto3.client("cognito-idp")


def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    event["request-body"] = json.loads(event["body"])
    
    email_address = event["request-body"].get("email-address", "")
    new_password = event["request-body"].get("password", "")
    
    if email_address == "":
        raise APIGatewayException("Value for \"email-address\" must be specified in message.", 400)
    
    if new_password == "":
        raise APIGatewayException("Value for \"password\" must be specified in message.", 400)
    
    validate_email_address(email_address)
    
    new_username = "{}".format(uuid.uuid4())
    
    client_id = os.environ["COGNITO_USER_POOL_CLIENT_ID"]
    client_secret = os.environ["COGNITO_USER_POOL_CLIENT_SECRET"]
    
    try:
        cognito_client.sign_up(
            ClientId = client_id,
            SecretHash = generate_cognito_sign_up_secret_hash(new_username, client_id, client_secret),
            Username = new_username,
            Password = new_password,
            UserAttributes = [
                {
                    "Name": "email",
                    "Value": email_address
                }
            ]
        )
    except botocore.exceptions.ParamValidationError as e:
        raise APIGatewayException("Password does not meet complexity requirements.", 400)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'InvalidPasswordException':
            raise APIGatewayException("Password does not meet complexity requirements.", 400)
        elif e.response['Error']['Code'] == 'CodeDeliveryFailureException':
            raise APIGatewayException("Unable to deliver code to the e-mail address specified.", 400)
    
    return {
        "registration-id": new_username,
        "email-address": email_address
    }

def validate_email_address(email_address):
    email_address_parts = email_address.split("@")
    
    if len(email_address_parts) != 2:
        raise APIGatewayException("E-mail address must contain a single @ symbol.", 400)
    
    email_address_user = email_address_parts[0]
    email_address_domain = email_address_parts[1]
    
    if len(email_address_user) < 1:
        raise APIGatewayException("An e-mail address should have at least one character before the @ symbol.", 400)
    
    if len(email_address_domain) < 1:
        raise APIGatewayException("An e-mail address should have at least one character after the @ symbol.", 400)
    
    mx_server_found = False
    
    try:
        mx_answers = dns.resolver.query(email_address_domain, 'MX')
        for rdata in mx_answers:
            mx_server_found = True
            break
    except dns.resolver.NXDOMAIN as e:
        raise APIGatewayException("Unable to find name servers for e-mail address's domain.", 400)
    except dns.resolver.Timeout as e:
        raise APIGatewayException("Timed out trying to reach e-mail address's domain's nameserver(s).", 400)
    
    if not mx_server_found:
        raise APIGatewayException("Unable to look up e-mail address domain's mail servers.", 400)

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