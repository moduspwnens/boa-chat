"""CognitoUserPoolCustomMessageFunction

Used with a Cognito User Pool to customize an e-mail verification message.

"""

from __future__ import print_function

import os
import json

email_template_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "email-verify-template.html"
)

def lambda_handler(event, context):
    print('Event: {}'.format(json.dumps(event)))
    
    event["response"]["emailSubject"] = "Confirm your e-mail address"
    event["response"]["emailMessage"] = "Custom: Your confirmation code is {}".format(
        event["request"]["codeParameter"]
    )
    
    intro_message = ""
    
    if event["triggerSource"] == "CustomMessage_SignUp":
        intro_message = "Thank you for registering."
        
    elif event["triggerSource"] == "CustomMessage_UpdateUserAttribute":
        intro_message = "This message is sent to confirm your e-mail address change."
    
    confirmation_link = "{}/#/email/verify/register/{}".format(
        os.environ["WEB_INTERFACE_PUBLIC_ENDPOINT"],
        event["userName"]
    )
    
    with open(email_template_path) as f:
        event["response"]["emailMessage"] = f.read().format(
            intro_message = intro_message,
            confirmation_code = event["request"]["codeParameter"],
            confirmation_link = html_escape(confirmation_link),
            app_name = html_escape(os.environ["PROJECT_TITLE"])
        )
    
    print("Returning event: {}".format(json.dumps(event)))
    
    return event

#https://wiki.python.org/moin/EscapingHtml
html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }

def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c,c) for c in text)