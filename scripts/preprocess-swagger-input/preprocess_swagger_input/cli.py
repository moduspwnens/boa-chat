#!/usr/bin/env python

from __future__ import print_function

import json
import click
import yaml

@click.group()
def cli():
    pass

@click.command()
@click.option('--input-swagger-file', help='Path to input Swagger file.', required=True, type=click.File('rb'))
@click.option('--output-swagger-file', help='Path to output Swagger file (will be overwritten).', required=True, type=click.File('wb'))
@click.option('--aws-region', help='AWS region.', default='aws-region')
@click.option('--aws-account-id', help='AWS account ID.', default='000000000000')
def process(input_swagger_file, output_swagger_file, aws_region, aws_account_id):
    
    input_template = yaml.load(input_swagger_file.read())
    
    tasks_performed_list = []
    
    if "x-boa-cors-enable" in input_template:
        for each_path in input_template.get("paths", {}).keys():
            enable_cors_for_path_by_default(input_template, tasks_performed_list, each_path, aws_region, aws_account_id)
    
    clear_root_custom_properties(input_template)
    
    if len(tasks_performed_list) == 0:
        click.echo('No tasks performed.', err=True)
    else:
        click.echo('Performed task(s):')
        for each_task in tasks_performed_list:
            click.echo(' * {}'.format(each_task))
    
    yaml.dump(input_template, output_swagger_file)

cli.add_command(process)

def enable_cors_for_path_by_default(input_template, tasks_performed_list, each_path, aws_region, aws_account_id):
    
    methods_list = input_template["paths"][each_path].keys()
    
    cors_methods_list = []
    
    if 'options' in methods_list:
        print('Skipping adding CORS for method(s) of {} due to existing OPTIONS method.'.format(
            each_path
        ))
    
    response_mapping_headers = ["Access-Control-Allow-Origin", "Access-Control-Allow-Headers", "Access-Control-Allow-Methods"]
    
    if "x-boa-cors-max-age" in input_template:
        response_mapping_headers.append("Access-Control-Max-Age")
    
    cors_headers_list = []
    if "x-boa-cors-headers" in input_template:
        cors_headers_list.extend(input_template["x-boa-cors-headers"].split(","))
    
    for each_method in methods_list:
        cors_methods_list.append(each_method.upper())
        
        for each_security_dict in input_template["paths"][each_path][each_method].get("security", []):
            first_key_name = each_security_dict.keys()[0]
            
            each_definition = input_template["securityDefinitions"][first_key_name]
            if each_definition.get("type") == "apiKey":
                if each_definition["name"] not in cors_headers_list:
                    cors_headers_list.append(each_definition["name"])
            
            if each_definition.get("x-amazon-apigateway-authtype") == "awsSigv4":
                headers_to_add = ["x-amz-date", "x-amz-security-token"]
                for each_header in headers_to_add:
                    if each_header not in cors_headers_list:
                        cors_headers_list.append(each_header)
            
            
    
    if "OPTIONS" not in cors_methods_list:
        cors_methods_list.append("OPTIONS")
    
    cors_allow_origin_string = "stageVariables.CorsOrigins"
    
    for each_method in methods_list:
        each_method_def = input_template["paths"][each_path][each_method]
        responses_dict = each_method_def.get("responses", {})
        
        if "responses" not in each_method_def:
            each_method_def["responses"] = responses_dict
        
        response_keys = responses_dict.keys()
        
        add_cors_response_headers = False
        
        static_body_mapping = each_method_def.get("x-boa-static-body-mapping")
        lambda_resource_name = each_method_def.get("x-boa-lambda-resource-name")
        
        add_cors_response_headers = static_body_mapping is not None
        
        for each_response_key in response_keys:
            each_response_headers = responses_dict.get("headers", {})
            
            if add_cors_response_headers:
                for each_cors_header in response_mapping_headers:
                    each_response_headers[each_cors_header] = {
                        "type": "string"
                    }
            
                each_response_headers["Content-Type"] = {
                    "type": "string"
                }
            
            each_method_def["responses"][each_response_key]["headers"] = each_response_headers
        
        apig_integration_def = {
            "responses": {}
        }
        
        apig_responses_def = apig_integration_def["responses"]
        
        
        
        if static_body_mapping is not None:
            apig_integration_def["type"] = "mock"
            apig_integration_def["passthroughBehavior"] = "WHEN_NO_MATCH"
            apig_integration_def["requestTemplates"] = {
                "application/json": json.dumps({"statusCode": 200})
            }
            
        elif lambda_resource_name is not None:
            apig_integration_def["type"] = "aws_proxy"
            apig_integration_def["passthroughBehavior"] = "NEVER"
            apig_integration_def["httpMethod"] = "POST"
            
            apig_integration_def["uri"] = "arn:aws:apigateway:{aws_region}:lambda:path/2015-03-31/functions/arn:aws:lambda:{aws_region}:{aws_account_id}:function:{function_name}/invocations".format(
                aws_account_id = aws_account_id,
                aws_region = aws_region,
                function_name = "${stageVariables.%s}" % lambda_resource_name
            )
            
        
        for each_response_key in response_keys:
            
            apig_integration_response_key = ""
            if str(each_response_key) == "200":
                apig_integration_response_key = "default"
            else:
                apig_integration_response_key = str(each_response_key)
            
            each_response_dict = {
                "statusCode": each_response_key
            }
            
            if static_body_mapping is not None and apig_integration_response_key == "default":
                each_response_dict["responseTemplates"] = {
                    "application/json": static_body_mapping
                }
                
            response_parameters = {}
            
            if add_cors_response_headers:
                response_parameters["method.response.header.Access-Control-Allow-Methods"] = "'{}'".format(
                    ",".join(cors_methods_list).upper()
                )
                response_parameters["method.response.header.Access-Control-Allow-Headers"] = "'{}'".format(
                    ",".join(cors_headers_list)
                )
                response_parameters["method.response.header.Access-Control-Allow-Origin"] = cors_allow_origin_string
                response_parameters["method.response.header.Content-Type"] = "'{}'".format(
                    "application/json"
                )
                
                if "x-boa-cors-max-age" in input_template:
                    response_parameters["method.response.header.Access-Control-Max-Age"] = "'{}'".format(
                        input_template["x-boa-cors-max-age"]
                    )
                
                for each_cors_header in response_mapping_headers:
                    each_method_def["responses"][each_response_key]["headers"][each_cors_header] = {
                        "type": "string"
                    }
            
            each_response_dict["responseParameters"] = response_parameters
                
            apig_responses_def[apig_integration_response_key] = each_response_dict
        
        each_method_def["x-amazon-apigateway-integration"] = apig_integration_def
        
        # Clear custom keys from output.
        for each_key in ["x-boa-static-body-mapping", "x-boa-lambda-resource-name"]:
            if each_key in each_method_def:
                del each_method_def[each_key]
    
    options_method_def = {
        "produces": [
            "application/json"
        ],
        "responses": {
            "200": {
                "description": "200 response",
                "headers": {},
                "schema": {
                    "$ref": "#/definitions/Empty"
                }
            }
        },
        "x-amazon-apigateway-integration": {
            "responses": {
                "default": {
                    "statusCode": "200",
                    "responseParameters": {}
                }
            },
            "requestTemplates": {
                "application/json": json.dumps({"statusCode": 200})
            },
            "passthroughBehavior": "WHEN_NO_MATCH",
            "type": "mock"
        }
    }
    
    for each_cors_header in response_mapping_headers:
        options_method_def["responses"]["200"]["headers"][each_cors_header] = {
            "type": "string"
        }
    
    options_method_def["responses"]["200"]["headers"]["Content-Type"] = {
        "type": "string"
    }
    
    response_parameters = options_method_def["x-amazon-apigateway-integration"]["responses"]["default"]["responseParameters"]
    
    response_parameters["method.response.header.Access-Control-Allow-Methods"] = "'{}'".format(
        ",".join(cors_methods_list).upper()
    )
    response_parameters["method.response.header.Access-Control-Allow-Headers"] = "'{}'".format(
        ",".join(cors_headers_list)
    )
    response_parameters["method.response.header.Access-Control-Allow-Origin"] = cors_allow_origin_string
    response_parameters["method.response.header.Content-Type"] = "'{}'".format(
        "application/json"
    )
    
    if "x-boa-cors-max-age" in input_template:
        response_parameters["method.response.header.Access-Control-Max-Age"] = "'{}'".format(
            input_template["x-boa-cors-max-age"]
        )
    
    
    input_template["paths"][each_path]["options"] = options_method_def
    
    tasks_performed_list.append(
        "Enabled CORS for {}".format(
            each_path
        )
    )

def clear_root_custom_properties(input_template):
    for each_key in input_template.keys():
        if each_key.startswith("x-boa-"):
            del input_template[each_key]