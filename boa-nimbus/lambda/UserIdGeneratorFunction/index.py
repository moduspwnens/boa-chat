"""UserIdGeneratorFunction

Returns a unique user ID the client can be used with other functions.

This is mostly a stub function for now. It will ultimately be replaced 
with a login process and an authentication credential that will avoid 
the client having to know or explicitly pass in their own user ID.

"""

from __future__ import print_function

import json, uuid, time
import boto3
from apigateway_helpers import get_public_api_base

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    public_api_base = get_public_api_base(event)
    
    new_user_id = generate_new_user_id()
    
    return {
        "user-id": new_user_id,
        "user": "{}{}/{}".format(
            public_api_base,
            event["resource-path"],
            new_user_id
        )
    }

def generate_new_user_id():
    return "{}".format(uuid.uuid4())
    