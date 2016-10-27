import boto3

def get_public_api_base(event):
    
    # https://forums.aws.amazon.com/thread.jspa?threadID=241370
    
    host_header_value = event["request-params"]["header"]["Host"]
    
    if host_header_value.endswith(".amazonaws.com"):
        # Assume this is the default deployment URL.
        return "https://{}/{}".format(
            host_header_value,
            event["stage"]
        )
    
    # The host header indicates this is invoked through a custom domain name.
    # Look up the base path mapping based on our stage.
    # Note that this will be imperfect because a stage can have multiple base path mappings.
    
    response_iterator = boto3.client("apigateway").get_paginator("get_base_path_mappings").paginate(
        domainName = host_header_value
    )
    
    own_mapping = None
    
    for each_response in response_iterator:
        for each_item in each_response.get("items"):
            if each_item["restApiId"] == event["api-id"] and each_item.get("stage", "") in ["", event["stage"]]:
                if own_mapping is not None:
                    raise Exception("Ambiguous base path mapping. Can't determine base path of API.")
                own_mapping = each_item
    
    if own_mapping is None:
        raise Exception("Unable to determine API's public URL.")
    
    base_path = own_mapping["basePath"]
    
    if own_mapping.get("stage", "") == "":
        base_path += "/" + event["stage"]
    
    return "https://{}/{}".format(
        host_header_value,
        base_path
    )