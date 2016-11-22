"""CognitoUserPostConfirmationTrigger

Called when a new user is confirmed.

"""

from __future__ import print_function

import os
import json
from project_local.generate_api_key import create_api_key_for_user_if_not_exists

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        return {
            "message": "Warmed!"
        }
    
    s3_bucket_name = os.environ["SHARED_BUCKET"]
    stack_name = os.environ["STACK_NAME"]
    usage_plan_id = os.environ["USAGE_PLAN_ID"]
    
    user_id = event["userName"]
    email_address = event["request"]["userAttributes"]["email"]
    user_pool_id = event["userPoolId"]
    
    create_api_key_for_user_if_not_exists(
        user_id = user_id, 
        email_address = email_address,
        user_pool_id = user_pool_id,
        stack_name = stack_name,
        usage_plan_id = usage_plan_id,
        s3_bucket_name = s3_bucket_name
    )
    
    return event

