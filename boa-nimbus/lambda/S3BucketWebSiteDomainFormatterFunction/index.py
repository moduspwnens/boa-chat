"""S3BucketWebSiteDomainFormatterFunction

Used as a CloudFormation custom resource to return the domain of a URL.

"""

from __future__ import print_function

import json
import urlparse
import cfnresponse

handler_object = None
def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    request_type = event.get("RequestType")
    
    response_data = {}
    
    if request_type in ["Create", "Update"]:
        response_data["WebsiteDomain"] = get_domain_from_url(event["ResourceProperties"]["WebsiteUrl"])
    
    cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, None)

    return {}

def get_domain_from_url(website_url):
    parsed_url = urlparse.urlparse(website_url)
    return parsed_url.netloc.split(":")[0]