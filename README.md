# boa-chat
A scalable, cheap, easy-to-deploy web chat platform built on AWS. 

## Demo

Coming soon!

## Quick deploy

Coming soon!

## Features



## Design


#### Serverless architecture
The application is built on a microservice architecture with only services that cost virtually nothing when idle and charge based on usage. Most usage is also covered by [the free tier](https://aws.amazon.com/s/dm/optimization/server-side-test/free-tier/free_np/).

#### Seamless scalability
Only services with no architectural scaling limits are used, and only in ways that do not introduce issues with scaling.

#### AWS agnostic client
A strong focus was also placed on keeping the client (web-based front end) agnostic to AWS. Because it requires no AWS API knowledge or libraries, the entire backend could be implemented without AWS and the front end would continue to work with only a change in the URL of the backend API.

#### Services utilized

 * API Gateway
 * Lambda
 * Step Functions
 * Simple Storage Service (S3)
 * Simple Queue Service (SQS)
 * Simple Notification Service (SNS)
 * Simple Email Service (SES)
 * CloudWatch Logs
 * CloudWatch Metrics
 * Cognito User Pool
 * Cognito Identity Pool
 * CloudFormation
 * CodeBuild
 * CodeCommit
 * CodePipeline
 

## Build and deploy from source

It only takes a few clicks. Just log into your AWS account (with appropriate permissions) and click this button:

[![Launch Stack](/launch-stack-button.png?raw=true "Launch Stack")](https://console.aws.amazon.com/cloudformation/home#/stacks/new?stackName=boa-chat-ci&templateURL=https://s3.amazonaws.com/bennlinger-public-site/boa-chat/0.1/continuous-integration.yaml)

Simply click "Next" until you get to the **Review** page, then check the box for *I acknowledge that AWS CloudFormation might create IAM resources.* and click **Create**.

You'll be waiting primarily for:
 * Initial Docker image creation (makes subsequent builds faster) - 18 minutes
 * Code pipeline to perform build and start deployment - 8 minutes
 * CloudFormation deployment of application stack - 5 minutes

After the second stack is created and reaches a **CREATE_COMPLETE** state, it's ready to go! Simply select the second stack, click the *Outputs* tab, and click the link next to the one called **WebChatApiHome**.

This application has no region restrictions, although it does require [Step Functions](https://aws.amazon.com/step-functions/) which are only available in US East (Virginia), US West (Oregon), and EU (Ireland).
