"""UserResourceCleanupFunction

Clears out user-specific resources on stack deletion.

"""

from __future__ import print_function

import json
import boto3
import botocore
import cfnresponse

cognito_identity_client = boto3.client("cognito-identity")
cognito_sync_client = boto3.client("cognito-sync")
apig_client = boto3.client("apigateway")

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    resource_props = event["ResourceProperties"]
    
    identity_pool_id = resource_props["CognitoIdentityPoolId"]
    user_profile_dataset_name = resource_props["CognitoIdentityUserProfileDatasetName"]

    request_type = event.get("RequestType")
    
    if request_type == "Delete":
        for each_identity_list in list_identity_pool_identities(identity_pool_id):
            
            identity_ids_to_delete = []
            
            for each_identity in each_identity_list:
                each_identity_id = each_identity["IdentityId"]
                
                response = cognito_sync_client.list_records(
                    IdentityPoolId = identity_pool_id,
                    IdentityId = each_identity_id,
                    DatasetName = user_profile_dataset_name
                )
                
                api_key_id = None
                
                for each_record in response.get("Records", []):
                    if each_record["Key"] == "api-key-id":
                        api_key_id = each_record["Value"]
                        break
                
                if api_key_id is not None:
                    print("Deleting API key ({}) for {}.".format(
                        api_key_id,
                        each_identity_id
                    ))
                    try:
                        apig_client.delete_api_key(
                            apiKey = api_key_id
                        )
                    except botocore.exceptions.ClientError as e:
                        if e.response["Error"]["Code"] != "NotFoundException":
                            raise
                
                print("Adding {} to identity deletion list.".format(each_identity_id))
                identity_ids_to_delete.append(each_identity_id)
            
            cognito_identity_client.delete_identities(
                IdentityIdsToDelete = identity_ids_to_delete
            )
            
            print("Deleted {} identities.".format(len(identity_ids_to_delete)))
                
    
    cfnresponse.send(event, context, cfnresponse.SUCCESS, {}, None)

    return {}

def list_identity_pool_identities(identity_pool_id):
    first_request_made = False
    next_token = None
    
    while (not first_request_made) or next_token is not None:
        
        request_kwargs = {
            "IdentityPoolId": identity_pool_id,
            "MaxResults": 60
        }
        
        if next_token is not None:
            request_kwargs["NextToken"] = next_token
        
        response = cognito_identity_client.list_identities(**request_kwargs)
        
        first_request_made = True
        next_token = response.get("NextToken")
        yield response["Identities"]