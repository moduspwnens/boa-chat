import json

def get_response_headers(event, context):
    return {
        "Content-Type": "application/json"
    }