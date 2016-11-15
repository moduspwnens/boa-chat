"""ApiUsagePlanLinkerFunction

AWS CloudFormation Custom Resource for adding an API Gateway REST API and 
stage to a usage plan.

Necessary to avoid a CloudFormation dependency loop.

"""

from __future__ import print_function

import json
import boto3
import cfnresponse

lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    print('Event: {}'.format(json.dumps(event)))
    
    request_type = event.get("RequestType")

    if request_type in ["Create", "Update"]:
        pass

    cfnresponse.send(event, context, cfnresponse.SUCCESS, {}, None)

    return {}