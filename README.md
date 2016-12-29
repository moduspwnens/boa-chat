# boa-chat
A scalable, cheap, easy-to-deploy web chat platform built on AWS. 

## Demo

Coming soon!

## Quick deploy

Coming soon! For now, use the [Build and deploy from source method](#build-and-deploy-from-source). It's very easy--just requires an additional ~25 minutes.

This application has no region restrictions, although it does require [Step Functions](https://aws.amazon.com/step-functions/). These are [only available](https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/) in US East (Virginia), US West (Oregon), and EU (Ireland) at the time of writing.

## Features

### Platform

 * Users can create their own chat rooms
 * Each chat room gets its own private but shareable URL
 * Other users can join the chat room by opening the URL in their browser
 * Each user is authenticated by his/her e-mail address and the password set during registration

### Detail

 * REST API with web-based user interface
 * User registration
 * E-mail address verification
 * Per-user request throttling, rate limiting, and request tracking
 * Chat room message history logs stored durably on S3
 * All authenticated API requests are cryptographically signed, encrypted, and utilize timestamps for replay protection
 * API credentials are always temporary and last only one hour
 * User avatars via [Gravatar](gravatar.com)


## Design

#### Serverless architecture
The application is built on a microservice architecture with only services that cost virtually nothing when idle and charge based on usage. Most usage is also covered by [the free tier](https://aws.amazon.com/s/dm/optimization/server-side-test/free-tier/free_np/).

#### Seamless scalability
Only services with no architectural scaling limits are used, and only in ways that do not introduce issues with scaling.

#### Easy CloudFormation-based deployment
No need to install anything. Just launch the stack by clicking the button here. You don't need the AWS CLI, Python, pip, npm, or anything else. If you're reading this from a web browser, you've got all you need.

#### AWS agnostic client
A strong focus was also placed on keeping the client (web-based front end) agnostic to AWS. Because it requires no AWS API knowledge or libraries, the entire backend could be implemented without AWS and the front end would continue to work with only a change in the URL of the backend API.

#### Security focused
 * No IAM users or permanent access keys are created at any time
 * No IAM roles or policies authorize creating or modifying any IAM resources†
 * No IAM roles or policies authorize modifying Lambda function code†
 * All IAM resources (roles, policies) are created **only** at deploy-time by CloudFormation
 * All IAM policies are restricted to access only the resources required to the extent possible

The end result is that everything the resources are allowed to do is statically defined. A concerned administrator could review the CloudFormation template and source code prior to deployment or the IAM policies applied and function code after deployment. The application resources have no way of modifying them.

The infrastructure creates no long-term credentials or secrets, so there are no keys that can potentially be lost or compromised.

† Except for the role used by the continuous integration stack, and assumable only by CloudFormation, to launch the application's own stack. It's not included unless you build and deploy from source.

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
 * EC2 Container Registry (ECR)

#### Tools / frameworks / languages utilized

 * Back end
   * Python 2.7
     * [boto3](https://github.com/boto/boto3)
   * [Docker](https://www.docker.com/)
   * [OpenAPI / Swagger](https://github.com/OAI/OpenAPI-Specification)
 
 * Front end
   * HTML
   * CSS / LESS
   * JavaScript

## Build and deploy from source

It only takes a few clicks. Just log into your AWS account (with appropriate permissions) and click this button:

[![Launch Stack](/launch-stack-button.png?raw=true "Launch Stack")](https://console.aws.amazon.com/cloudformation/home#/stacks/new?stackName=boa-chat-ci&templateURL=https://s3.amazonaws.com/bennlinger-public-site/boa-chat/0.1/continuous-integration.yaml)

Simply click "Next" until you get to the **Review** page, then check the box for *I acknowledge that AWS CloudFormation might create IAM resources.* and click **Create**.

You'll be waiting primarily for:
 * Initial Docker image creation (makes subsequent builds faster) - 18 minutes
 * Code pipeline to perform build and start deployment - 8 minutes
 * CloudFormation deployment of application stack - 5 minutes

After the second stack is created and reaches a **CREATE_COMPLETE** state, it's ready to go! Simply select the second stack, click the *Outputs* tab, and click the link next to the one called **WebChatApiHome**.


