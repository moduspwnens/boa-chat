# boa-chat
A scalable, cheap, easy-to-deploy web chat platform built on AWS.

## Build and deploy from source

It only takes a few clicks. Just log into your AWS account (with appropriate permissions) and click this button:

[![Launch Stack](/launch-stack-button.png?raw=true "Launch Stack")](https://console.aws.amazon.com/cloudformation/home#/stacks/new?stackName=boa-chat-ci&templateURL=https://s3.amazonaws.com/bennlinger-public-site/boa-chat/0.1/continuous-integration.yaml)

Simply click "Next" until you get to the **Review** page, then check the box for *I acknowledge that AWS CloudFormation might create IAM resources.* and click **Create**.

You'll be waiting primarily for:
 * Initial Docker image creation (makes subsequent builds faster) - 18 minutes
 * Code pipeline to perform build and start deployment - 8 minutes
 * CloudFormation deployment of application - 5 minutes

After the second stack is created and reaches a **CREATE_COMPLETE** state, it's ready to go! Simply select the second stack, click the *Outputs* tab, and click the link next to the one called **WebChatApiHome**.

This application has no region restrictions, although it does require [Step Functions](https://aws.amazon.com/step-functions/) which are only available in US East (Virginia), US West (Oregon), and EU (Ireland).

