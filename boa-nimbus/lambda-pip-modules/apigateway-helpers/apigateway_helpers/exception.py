import json

class APIGatewayException(Exception):

    def __init__(self, message, http_status_code = 500):

        # Encode this exception as a JSON object so it can be decoded by API Gateway.
        new_message_object = {
            "http-status": http_status_code,
            "message": message
        }
        
        self.http_status_code = http_status_code
        self.http_status_message = message
        
        new_message = json.dumps(new_message_object, separators=(",", ":"))
        Exception.__init__(self, new_message)