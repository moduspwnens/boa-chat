"""ApiGatewayLambdaCorsEnvSetterFunction

Sets the necessary environment variables so that CORS headers can be returned 
with Lambda responses for API Gateway.

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
        
        paginator = apig_client.get_paginator("get_resources")
        response_iterator = paginator.paginate(
            restApiId = rest_api_id
        )
        
        resource_list = []
        
        for each_response in response_iterator:
            resource_list.extend(each_response["items"])
        
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
                    print(lambda_arn)
        

    cfnresponse.send(event, context, cfnresponse.SUCCESS, {}, None)

    return {}