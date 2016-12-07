"""ApiGatewayLambdaSetupFunction

Performs necessary API Gateway / Lambda setup.
 * Adds Lambda execution permissions to API Gateway endpoints
 * Adds necessary stage variables so function name mappings (from Swagger 
   for CORS) will work
 * Adds necessary stage variables so necessary CORS headers can be resolved 
   by each function

"""

from __future__ import print_function

import json
import re
import hashlib
import boto3
import botocore
import cfnresponse

apig_client = boto3.client('apigateway')
cloudformation_client = boto3.client('cloudformation')
lambda_client = boto3.client('lambda')
s3_client = boto3.client('s3')

cors_headers_stage_variable_map = {
    "Access-Control-Allow-Methods": "CorsMethodsByResource",
    "Access-Control-Allow-Headers": "CorsHeadersByResource"
}

cors_headers_to_save = cors_headers_stage_variable_map.keys()

cors_json_s3_key = "api-cors.json"

def lambda_handler(event, context):
    print('Event: {}'.format(json.dumps(event)))
    
    stack_id = event["StackId"]
    stack_region = stack_id.split(":")[3]
    stack_account_id = stack_id.split(":")[4]
    
    request_type = event.get("RequestType")
    
    resource_props = event["ResourceProperties"]

    if request_type in ["Create", "Update"]:
        
        rest_api_id = resource_props["RestApi"]
        stage_name = resource_props["StageName"]
        bucket_name = resource_props["Bucket"]
        cors_origin_list = resource_props.get("CorsOriginList", "")
        
        stage_redeploy_required = False
        
        paginator = apig_client.get_paginator("get_resources")
        response_iterator = paginator.paginate(
            restApiId = rest_api_id
        )
        
        resource_list = []
        
        for each_response in response_iterator:
            resource_list.extend(each_response["items"])
        
        lambda_function_resource_map = {}
        resource_cors_map = {}
        
        for each_resource in resource_list:
            
            for each_method in each_resource.get("resourceMethods", {}).keys():
                response = apig_client.get_method(
                    restApiId = rest_api_id,
                    resourceId = each_resource["id"],
                    httpMethod = each_method
                )
                
                method_integration = response.get("methodIntegration", {})
                
                if method_integration.get("type") in ["AWS", "AWS_PROXY"] and ":lambda:" in method_integration.get("uri"):
                    integration_uri = method_integration["uri"]
                    lambda_arn = ":".join(integration_uri.split(":")[6:]).split("/")[0]
                    lambda_function_name = lambda_arn.split(":")[5]
                    
                    m = re.search(r"\${stageVariables\.([^}]+)}", lambda_function_name)
                    for each_lambda_function_resource_name in m.groups():
                        if each_lambda_function_resource_name not in lambda_function_resource_map:
                            lambda_function_resource_map[each_lambda_function_resource_name] = []
                        
                        lambda_function_resource_map[each_lambda_function_resource_name].append({
                            "resource": each_resource["path"],
                            "method": each_method
                        })
                
                elif method_integration.get("type", "").upper() == "MOCK":
                    
                    default_status_code = "200"
                    default_response_dict = response["methodIntegration"]["integrationResponses"][default_status_code]
                    
                    response_parameters = default_response_dict.get("responseParameters", {})
                    
                    cors_origin_mapping_key = "method.response.header.Access-Control-Allow-Origin"
                    
                    if response_parameters.get(cors_origin_mapping_key, "") != cors_origin_list:
                        print("Updating {} {} integration response parameter {}".format(
                            each_resource["path"],
                            each_method,
                            cors_origin_mapping_key
                        ))
                        apig_client.update_integration_response(
                            restApiId = rest_api_id,
                            resourceId = each_resource["id"],
                            httpMethod = each_method,
                            statusCode = default_status_code,
                            patchOperations = [{
                                "op": "replace",
                                "path": "/responseParameters/{}".format(cors_origin_mapping_key),
                                "value": "'{}'".format(cors_origin_list)
                            }]
                        )
                        stage_redeploy_required = True
                    
                    if each_method.upper() == "OPTIONS":
                        headers_dict = {}
                        for each_key in response_parameters.keys():
                            if each_key.startswith("method.response.header."):
                                header_name = each_key[23:].upper()
                                headers_dict[header_name] = response_parameters[each_key]
                    
                        resource_cors_map[each_resource["path"]] = {}
                    
                        for each_header in cors_headers_to_save:
                            each_header_upper = each_header.upper()
                        
                            if each_header_upper in headers_dict:
                                each_header_value = headers_dict[each_header_upper]
                            
                                # Strip single quotes off.
                                each_header_value = each_header_value[1:][:-1]
                            
                                resource_cors_map[each_resource["path"]][each_header] = each_header_value
        
        lambda_function_resource_name_map = {}
        
        for each_lambda_function_resource_name in lambda_function_resource_map.keys():
            invocations_needing_access = lambda_function_resource_map[each_lambda_function_resource_name]
            
            response = cloudformation_client.describe_stack_resource(
                StackName = stack_id,
                LogicalResourceId = each_lambda_function_resource_name
            )
            
            lambda_function_name = response["StackResourceDetail"]["PhysicalResourceId"]
            
            lambda_function_resource_name_map[each_lambda_function_resource_name] = lambda_function_name
            
            for each_invocation_dict in invocations_needing_access:
                
                statement_id = "apigateway-{}".format(
                    hashlib.md5(json.dumps(each_invocation_dict, sort_keys=True)).hexdigest()
                )
                
                source_arn = "arn:aws:execute-api:{aws_region}:{aws_account_id}:{api_id}/*/{http_method}{http_path}".format(
                    aws_region = stack_region,
                    aws_account_id = stack_account_id,
                    api_id = rest_api_id,
                    http_method = each_invocation_dict["method"].upper(),
                    http_path = each_invocation_dict["resource"]
                )
                
                print("Adding permission to execute {} to {}".format(
                    lambda_function_name,
                    source_arn
                ))
                
                try:
                    lambda_client.add_permission(
                        FunctionName = lambda_function_name,
                        StatementId = statement_id,
                        Action = "lambda:InvokeFunction",
                        Principal = "apigateway.amazonaws.com",
                        SourceArn = source_arn
                    )
                except botocore.exceptions.ClientError as e:
                    if e.response['Error']['Code'] == 'ResourceConflictException':
                        print("Already exists.")
                    else:
                        raise
        
        stage_patch_operations = []
        
        for each_lambda_function_resource_name in lambda_function_resource_name_map.keys():
            each_lambda_function_name = lambda_function_resource_name_map[each_lambda_function_resource_name]
            
            stage_patch_operations.append({
                "op": "replace",
                "path": "/variables/{}".format(each_lambda_function_resource_name),
                "value": each_lambda_function_name
            })
            
        if len(stage_patch_operations) > 0:
            print("Creating stage variables ({}) for Lambda function names.".format(len(stage_patch_operations)))
            
            apig_client.update_stage(
                restApiId = rest_api_id,
                stageName = stage_name,
                patchOperations = stage_patch_operations
            )
        
        print("Posting CORS header values to S3.")
        s3_client.put_object(
            Bucket = bucket_name,
            Key = cors_json_s3_key,
            Body = json.dumps(resource_cors_map, indent=4),
            ContentType = "application/json"
        )
        
        additional_stage_variables = resource_props.get("StageVariables", {})
        
        stage_patch_operations = []
        
        for each_key in additional_stage_variables.keys():
            each_value = additional_stage_variables[each_key]
            
            stage_patch_operations.append({
                "op": "replace",
                "path": "/variables/{}".format(each_key),
                "value": each_value
            })
        
        if len(stage_patch_operations) > 0:
            print("Creating additional stage variables ({}).".format(len(stage_patch_operations)))
            
            apig_client.update_stage(
                restApiId = rest_api_id,
                stageName = stage_name,
                patchOperations = stage_patch_operations
            )
        
        if stage_redeploy_required:
            print("Redeploying stage.")
            apig_client.create_deployment(
                restApiId = rest_api_id,
                stageName = stage_name
            )
        

    cfnresponse.send(event, context, cfnresponse.SUCCESS, {}, None)

    return {}