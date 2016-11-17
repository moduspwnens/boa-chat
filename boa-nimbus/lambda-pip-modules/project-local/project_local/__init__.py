from __future__ import print_function

import json
import boto3

cached_cloudformation_metadata = None

def get_own_cloudformation_metadata(function_logical_name):
    global cached_cloudformation_metadata
    
    if cached_cloudformation_metadata is not None:
        return cached_cloudformation_metadata

    caller_arn = boto3.client("sts").get_caller_identity()["Arn"]
    caller_role = caller_arn.split(":")[5].split("/")[1]

    policy_response = boto3.client("iam").get_role_policy(
        RoleName = caller_role,
        PolicyName = "{}RoleActions".format(
            function_logical_name
        )
    )

    this_stack_id = None

    for each_statement in policy_response["PolicyDocument"]["Statement"]:
        if len(each_statement.get("Action", [])) == 0:
            continue

        if each_statement["Action"][0].lower() == "cloudformation:describeStackResource".lower():
            this_stack_id = each_statement["Resource"]
            break

    if this_stack_id is None:
        raise Exception("Unable to determine CloudFormation stack ID from IAM policy.")
    
    response = boto3.client("cloudformation").describe_stack_resource(
        StackName = this_stack_id,
        LogicalResourceId = function_logical_name
    )

    own_metadata = json.loads(response["StackResourceDetail"]["Metadata"])

    cached_cloudformation_metadata = own_metadata

    return own_metadata