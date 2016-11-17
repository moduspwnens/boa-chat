import base64
import hmac
import hashlib

def generate_cognito_sign_up_secret_hash(username, client_id, client_secret):
    return base64.b64encode(
        hmac.new(
            str(client_secret), 
            msg = "{}{}".format(
                username,
                client_id
            ).decode("utf-8"), 
            digestmod = hashlib.sha256
        ).digest()
    ).decode()