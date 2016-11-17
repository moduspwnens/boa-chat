"""CognitoIdentityPoolRoleLinkerFunction

Links pre-created IAM roles to a pre-created Cognito Identity Pool.

"""

from __future__ import print_function

import json
import cfnresponse
import boto3
import botocore

cognito_identity_client = boto3.client("cognito-identity")

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    request_type = event.get("RequestType")
    
    resource_properties = event["ResourceProperties"]
    
    identity_pool_id = resource_properties["IdentityPoolId"]
    
    response_data = {}
    
    if request_type in ["Create", "Update"]:
        
        authenticated_user_role = resource_properties["UserRoles"]["AuthenticatedUserRole"]
        unauthenticated_user_role = resource_properties["UserRoles"]["UnauthenticatedUserRole"]
        
        cognito_identity_client.set_identity_pool_roles(
            IdentityPoolId = identity_pool_id,
            Roles = {
                "authenticated": authenticated_user_role,
                "unauthenticated": unauthenticated_user_role
            }
        )
        
    elif request_type == "Delete":
        # Would need a new set of roles to replace the old ones.
        pass
    
    cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, None)

    return {}