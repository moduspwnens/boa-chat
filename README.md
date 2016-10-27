# aws-serverless-web-chat
A scalable, cheap, easy-to-deploy web chat platform.

Still in development.

## How to use

Make sure you have Python 2.7 and [pip installed](https://pip.pypa.io/en/stable/installing/).

```
# Ensure your AWS credentials are set. Use the AWS CLI docs for example setup.
# http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html

# Install boa-nimbus.
pip install git+git://github.com/moduspwnens/boa-nimbus.git

# Clone this repo.
git clone https://github.com/moduspwnens/aws-serverless-web-chat.git

# Change working directory to repository root.
cd aws-serverless-web-chat

# Package and upload Lambda function.
boa-nimbus deploy --stack-name webchat-lambda-src
```

After the command completes successfully: 

 * Go to [CloudFormation in the AWS web console](https://console.aws.amazon.com/cloudformation/home).
 * Click the **Create Stack** button and choose to upload the **serverless-web-chat.yaml** template from this directory. 
 * Click through the wizard to launch the stack.

Wait until the stack reaches the **CREATE_COMPLETE** status, select it and click the **Outputs** tab. There's only one, and that's the URL to the base of the API.