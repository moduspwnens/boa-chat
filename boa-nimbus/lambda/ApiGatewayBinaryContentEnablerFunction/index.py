"""ApiGatewayBinaryContentEnablerFunction

AWS CloudFormation Custom Resource for adding binary support configuration 
to API Gateway.

"""

from __future__ import print_function

import json
import boto3
import cfnresponse

apig_client = boto3.client('apigateway')

def lambda_handler(event, context):
    print('Event: {}'.format(json.dumps(event)))
    
    request_type = event.get("RequestType")
    
    resource_properties = event["ResourceProperties"]

    if request_type in ["Create", "Update"]:
        
        rest_api_id = resource_properties["RestApi"]
        
        apig_client.update_rest_api(
            restApiId = rest_api_id,
            patchOperations = [
                {
                    "op": "add",
                    "path": "/binaryMediaTypes/*~1*",
                }
            ]
        )
        
        paginator = apig_client.get_paginator("get_resources")
        response_iterator = paginator.paginate(
            restApiId = rest_api_id
        )
        
        resource_list = []
        
        for each_response in response_iterator:
            resource_list.extend(each_response["items"])
        
        integrations_to_update = []
        integration_responses_to_update = []
        
        for each_resource in resource_list:
            
            for each_method in each_resource.get("resourceMethods", {}).keys():
                response = apig_client.get_method(
                    restApiId = rest_api_id,
                    resourceId = each_resource["id"],
                    httpMethod = each_method
                )
                
                method_integration = response.get("methodIntegration", {})
                
                should_do_updates = False
                
                should_do_updates = method_integration.get("type") == "AWS" and ":lambda:" in method_integration.get("uri")
                
                should_do_updates = should_do_updates or method_integration.get("type") == "MOCK"
                
                if should_do_updates:
                    
                    integrations_to_update.append(
                        {
                            "resourceId": each_resource["id"],
                            "httpMethod": each_method
                        }
                    )
                    
                    for each_status_code in response.get("methodResponses", {}).keys():
                        
                        integration_responses_to_update.append(
                            {
                                "resourceId": each_resource["id"],
                                "httpMethod": each_method,
                                "statusCode": each_status_code
                            }
                        )
        
        for each_integration in integrations_to_update:
            
            update_integration_kwargs = each_integration.copy()
            update_integration_kwargs["restApiId"] = rest_api_id
            update_integration_kwargs["patchOperations"] = [
                {
                    "op": "replace",
                    "path": "/contentHandling",
                    "value": "CONVERT_TO_TEXT"
                }
            ]
            
            apig_client.update_integration(**update_integration_kwargs)
        
        for each_integration_response in integration_responses_to_update:
            
            update_integration_response_kwargs = each_integration_response.copy()
            update_integration_response_kwargs["restApiId"] = rest_api_id
            update_integration_response_kwargs["patchOperations"] = [
                {
                    "op": "replace",
                    "path": "/contentHandling",
                    "value": "CONVERT_TO_TEXT"
                }
            ]
            
            apig_client.update_integration_response(**update_integration_response_kwargs)

    cfnresponse.send(event, context, cfnresponse.SUCCESS, {}, None)

    return {}