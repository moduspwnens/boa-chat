"""CorsOriginCombinerFunction

Returns an appropriate value for an API Gateway header mapping for the 
Access-Control-Allowed-Origin header.

"""

from __future__ import print_function

import json
import cfnresponse

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))

    request_type = event.get("RequestType")
    resource_properties = event["ResourceProperties"]
    
    response_data = {}
    
    if request_type in ["Create", "Update"]:
        cors_entries = []
        cors_entries.append(resource_properties["BucketWebsiteUrl"])
        
        if len(resource_properties["AdditionalCorsOrigins"]) > 0:
            for each_additional_origin in resource_properties["AdditionalCorsOrigins"]:
                if len(each_additional_origin) > 0:
                    cors_entries.append(each_additional_origin)
        
        cors_entries_string = None
        
        if "*" in cors_entries:
            cors_entries_string = "*"
        else:
            cors_entries_string = ",".join(cors_entries)
        
        response_data["CorsOriginList"] = cors_entries_string
        response_data["ApiGatewayCorsOriginHeaderValue"] = cors_entries_string
        response_data["ApiGatewayCorsOriginHeaderMapping"] = "'{}'".format(cors_entries_string)

    cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, None)

    return {}