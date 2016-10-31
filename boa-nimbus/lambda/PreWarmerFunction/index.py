"""PreWarmerFunction

Warms the Lambda functions as passed in via its own event.

Used with a timed CloudWatch event rule to allow an arbitrary number of 
functions to be prewarmed by a single event rule.

Default AWS limits allow a maximum of 10 CloudWatch event rules, each of 
which with a maximum of 5 targets.

"""

from __future__ import print_function

import json
import traceback
import boto3

lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    print('Event: {}'.format(json.dumps(event)))
    
    for each_function_arn in event['function-arns']:
        
        try:
            lambda_client.invoke(
                FunctionName = each_function_arn,
                InvocationType = 'Event',
                Payload = json.dumps(event['payload'])
            )
            print('Invoked {} successfully.'.format(each_function_arn))
        except Exception as e:
            print(traceback.format_exc())
            print('Error invoking {}.'.format(each_function_arn))

    return {}