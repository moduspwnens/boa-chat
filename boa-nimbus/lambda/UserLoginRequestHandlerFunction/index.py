"""UserLoginRequestHandlerFunction

Validates an e-mail address and then sends an e-mail with a unique link 
that allows the user to click it to verify their e-mail address.

"""

from __future__ import print_function

import json
import uuid
import time
import boto3
import botocore
import dns.resolver
import zbase32
from apigateway_helpers import get_public_api_base
from apigateway_helpers.exception import APIGatewayException

email_send_as_name = "Web Chat"
email_subject = "Sign in to Web Chat"

s3_client = boto3.client("s3")
ses_client = boto3.client("ses")

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    public_api_base = get_public_api_base(event)
    
    if event["request-body"].get("email-address", "") == "":
        raise APIGatewayException("Value for \"email-address\" must be specified in message.", 400)
    
    if event["request-body"].get("sign-in-url", "") == "":
        raise APIGatewayException("Value for \"sign-in-url\" must be specified in message.", 400)
    
    email_address = event["request-body"]["email-address"]
    
    validate_email_address(email_address)
    
    sign_in_token = generate_sign_in_token(
        event["shared-bucket"],
        email_address
    )
    
    plaintext_message = "Your log in code is: {}".format(sign_in_token)
    
    html_message = "Your log in code is: <b>{}</b>".format(sign_in_token)
    
    try:
        response = ses_client.send_email(
            Source="\"{}\" <{}>".format(
                email_send_as_name,
                event["email-from-address"]
            ),
            Destination={
                "ToAddresses": [email_address]
            },
            Message={
                "Subject": {
                    "Data": email_subject,
                    "Charset": "utf-8"
                },
                "Body": {
                    "Text": {
                        "Data": plaintext_message,
                        "Charset": "utf-8"
                    },
                    "Html": {
                        "Data": html_message,
                        "Charset": "utf-8"
                    }
                }
            }
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'MessageRejected':
            if 'Email address is not verified.' in e.response['Error']['Message']:
                raise APIGatewayException("Amazon SES e-mail address verification required.", 479)
            raise
    
    return {}

def generate_sign_in_token(s3_bucket_name, email_address):
    token_pre_encoded = uuid.uuid4().bytes
    token_encoded = zbase32.b2a(token_pre_encoded)
    
    s3_client.put_object(
        Bucket = s3_bucket_name,
        Key = "login-requests/{}.json".format(token_encoded),
        Body = json.dumps({
            "email-address": email_address,
            "created": int(time.time())
        }),
        ContentType = "application/json"
    )
    
    return token_encoded

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