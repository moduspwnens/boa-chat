"""CognitoUserPoolCustomMessageFunction

Used with a Cognito User Pool to customize an e-mail verification message.

"""

from __future__ import print_function

import json
import boto3

cognito_idp_client = boto3.client('cognito-idp')

def lambda_handler(event, context):
    print('Event: {}'.format(json.dumps(event)))
    
    event["response"]["emailSubject"] = "Your verification code"
    event["response"]["emailMessage"] = "Your confirmation code is {}".format(
        event["request"]["codeParameter"]
    )
    
    return event