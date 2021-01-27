# AWS CDK application workshop to process AWS Storage Gateway (File Gateway) file upload notifications

© 2021 Amazon Web Services, Inc. and its affiliates. All rights reserved. This sample code is made available under the MIT-0 license. See the LICENSE file.

Feedback: Contact atieka@amazon.co.uk, djsearle@amazon.co.uk.

---

# Workshop scenario
This is a workshop that deploys a CDK application based on the file notification event processing solution described in [this blog](https://aws.amazon.com/blogs/storage/processing-file-upload-notifications-from-aws-storage-gateway-on-amazon-s3/).

Many customers use AWS Storage Gateway (File Gateway) to upload individual files to Amazon Simple Storage Service. Together, these files often constitute a larger logical set of data that should be grouped for downstream processing. A common example is when data is vaulted from source systems. This CDK application is designed for such a use-case and leverages the [File Upload Notification](https://docs.aws.amazon.com/storagegateway/latest/userguide/monitoring-file-gateway.html#get-file-upload-notification) feature of File Gateway to implement an event processing flow. NOTE: This application is not a fully fledged data vaulting solution, but can be used as a component within a larger implementation - e.g. to process file upload events for object archives making their way to a final vault location on AWS.

# Topics covered
* Overview of the example data vaulting use-case
* Setting up and deploying resources using the AWS Cloud Development Kit
* Activating and configuring a Storage Gateway (File Gateway)
* Generating and copying sample data from a File Gateway client
* Using Storage Gateway (File Gateway) to vault data to Amazon S3
* Observing the event processing flow in action

# Pre-requisites
* An AWS account
* Ability to run the AWS CLI on your machine
* Internet browser (Chrome or Firefox recommended)

# Costs
This workshop will cost approximately $3-4 in AWS service charges and require 1 hour to complete. Once you have finished, destroy the deployed CDK application stacks in order to prevent further charges (see [**Module 7**](modules/MODULE7.md)).

# Workshop modules
* [Module 1](modules/MODULE1.md) - Overview of the architecture and solution components
* [Module 2](modules/MODULE2.md) - CDK pre-requisites and preparation
* [Module 3](modules/MODULE3.md) - Deploy the CDK application stacks
* [Module 4](modules/MODULE4.md) - Activate and configure the File Gateway
* [Module 5](modules/MODULE5.md) - Execute an example data vaulting operation
* [Module 6](modules/MODULE6.md) - Observe the event processing flow
* [Module 7](modules/MODULE7.md) - Cleanup

Go to [Module 1](modules/MODULE1.md) to get started now.