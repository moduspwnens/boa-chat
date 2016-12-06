"""ApiUsagePlanLinkerFunction

AWS CloudFormation Custom Resource for adding an API Gateway REST API and 
stage to a usage plan.

"""

from __future__ import print_function

import json
import boto3
import botocore
import cfnresponse

apig_client = boto3.client('apigateway')

def lambda_handler(event, context):
    print('Event: {}'.format(json.dumps(event)))
    
    request_type = event.get("RequestType")
    
    resource_properties = event["ResourceProperties"]

    if request_type in ["Create", "Update"]:
        try:
            apig_client.update_usage_plan(
                usagePlanId = resource_properties["UsagePlan"],
                patchOperations = [
                    {
                        "op": "add",
                        "path": "/apiStages",
                        "value": "{}:{}".format(
                            resource_properties["RestApi"],
                            resource_properties["Stage"]
                        )
                    }
                ]
            )
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] != "ConflictException":
                raise
    
    elif request_type == "Delete":
        try:
            apig_client.update_usage_plan(
                usagePlanId = resource_properties["UsagePlan"],
                patchOperations = [
                    {
                        "op": "remove",
                        "path": "/apiStages",
                        "value": "{}:{}".format(
                            resource_properties["RestApi"],
                            resource_properties["Stage"]
                        )
                    }
                ]
            )
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] != "NotFoundException":
                raise

    cfnresponse.send(event, context, cfnresponse.SUCCESS, {}, None)

    return {}