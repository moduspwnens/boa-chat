import os
import json
import boto3

s3_client = boto3.client('s3')
env_var_name = "SHARED_BUCKET"
cors_json_s3_key = "api-cors.json"

cached_cors_config = None

def _get_cors_configuration():
    global cached_cors_config
    
    if cached_cors_config is not None:
        return cached_cors_config
    
    if env_var_name not in os.environ:
        print("WARNING: S3 bucket storing CORS headers not specified in environment variables ({}). Can't add CORS headers.".format(
            env_var_name
        ))
        return {}
    
    s3_bucket_name = os.environ[env_var_name]
    
    print("Loading CORS config from s3://{}/{}".format(
        s3_bucket_name,
        cors_json_s3_key
    ))
    
    try:
        cached_cors_config = json.loads(s3_client.get_object(Bucket = s3_bucket_name, Key = cors_json_s3_key)["Body"].read())
    except Exception as e:
        print("An error occurred loading CORS config from S3.")
    

def get_response_headers(event, context):
    
    cors_config = _get_cors_configuration()
    
    resource_cors_config = cors_config.get(event["resource"], {})
    
    return_headers = {
        "Content-Type": "application/json"
    }
    
    for each_key in resource_cors_config.keys():
        return_headers[each_key] = resource_cors_config[each_key]
    
    
    
    if len(resource_cors_config) > 0:
        cors_origin_string = event.get("stageVariables", {}).get("CorsOrigins")
        if cors_origin_string is not None:
            return_headers["Access-Control-Allow-Origin"] = cors_origin_string
    
    return return_headers

if env_var_name not in os.environ:
    print("WARNING: S3 bucket storing CORS headers not specified in environment variables ({}). Can't add CORS headers.".format(
        env_var_name
    ))
else:
    _get_cors_configuration()