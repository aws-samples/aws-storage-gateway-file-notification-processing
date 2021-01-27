# AWS CDK application workshop to process AWS Storage Gateway (File Gateway) file upload notifications

© 2021 Amazon Web Services, Inc. and its affiliates. All rights reserved. This sample code is made available under the MIT-0 license. See the LICENSE file.

Feedback: Contact atieka@amazon.co.uk, djsearle@amazon.co.uk.

---

# Module 2 - CDK pre-requisites and preparation
Follow the steps below to ensure pre-requisites are in place, before deploying the CDK application stacks to the configured AWS account and region environment. The following should be performed on the machine where you are executing the CDK CLI commands. This machine will be referred to as the "CDK client" and all commands in this Module are executed on it.

## 2.1 Pre-requisites
* Python 3.6 or later, with pip and virtualenv
* AWS CDK (`sudo npm install -g aws-cdk`)
* AWS CLI configured using `aws configure`
* An AWS CLI role/user with required permissions for the resources created

## 2.2 Download the CDK application code
Clone or download this repository on your CDK client and navigate to the directory created.

## 2.3 Set account and region values
Edit the `cdk.context.json` file and add appropriate values for the `"stacksAccountId"` and `"stacksRegion"` context keys. Both stacks in this application will be deployed into the same AWS account and region specified by these values.

## 2.4 Create the Python environment and install dependencies
```console
user@cdk-client>$ python3 -m venv .venv
user@cdk-client>$ source .venv/bin/activate (Linux or Mac)
user@cdk-client>% .venv\Scripts\activate.bat (Windows)
user@cdk-client>$ pip install -r requirements.txt
```

You can list the CDK context key values by executing the following command. The keys specific to this application are explained at the beginning of [**Module 1**](MODULE1.md):
```console
user@cdk-client>$ cdk context
┌────┬─────────────────────────────────────────────┬────────────────┐
│ #  │ Key                                         │ Value          │
├────┼─────────────────────────────────────────────┼────────────────┤
│ 1  │ @aws-cdk/aws-ecr-assets:dockerIgnoreSupport │ true           │
├────┼─────────────────────────────────────────────┼────────────────┤
│ 2  │ @aws-cdk/core:enableStackNameDuplicates     │ "true"         │
├────┼─────────────────────────────────────────────┼────────────────┤
│ 3  │ @aws-cdk/core:stackRelativeExports          │ "true"         │
├────┼─────────────────────────────────────────────┼────────────────┤
│ 4  │ aws-cdk:enableDiffNoFail                    │ "true"         │
├────┼─────────────────────────────────────────────┼────────────────┤
│ 5  │ jobDirSuffixName                            │ "-vaultjob"    │
├────┼─────────────────────────────────────────────┼────────────────┤
│ 6  │ manifestSuffixName                          │ ".manifest"    │
├────┼─────────────────────────────────────────────┼────────────────┤
│ 7  │ reconcileCountIterations                    │ "960"          │
├────┼─────────────────────────────────────────────┼────────────────┤
│ 8  │ reconcileWaitIterations                     │ "30"           │
├────┼─────────────────────────────────────────────┼────────────────┤
│ 9  │ stacksAccountId                             │ "ACCOUNT ID"   │
├────┼─────────────────────────────────────────────┼────────────────┤
│ 10 │ stacksRegion                                │ "AWS REGION"   │
└────┴─────────────────────────────────────────────┴────────────────┘
Run cdk context --reset KEY_OR_NUMBER to remove a context key. It will be refreshed on the next CDK synthesis run.
user@cdk-client>$ 
```

## 2.5 Bootstrap the CDK environment
Since we will be using [CDK Assets](https://docs.aws.amazon.com/de_de/cdk/latest/guide/assets.html) to deploy the `DataVaultingStack`, we need to bootstrap the CDK environment. Execute the following to do this:
```console
user@cdk-client>$ cdk bootstrap
```

## 2.6 List the stacks in this CDK application
Execute the following to list the CDK application stacks. NOTE: The `DataVaultingStack` performs an EC2 AMI lookup in order to select the latest Storage Gateway AMI - this value will be cached in `cdk.context.json` when the first stack is synthesized (next step) and AMI lookups will no longer be performed until/unless the [cached values are reset/removed](https://docs.aws.amazon.com/cdk/latest/guide/context.html). The cached AMI value can be used for the remainder of this workshop:
```console
user@cdk-client>$ cdk ls
Searching for AMI in [stacksAccountId]:[stacksRegion]
DataVaultingStack
EventProcessingStack
user@cdk-client>$ 
```

## 2.7 Synthesize the AWS CloudFormation templates for the CDK stacks
```console
user@cdk-client>$ cdk synth
Searching for AMI in [stacksAccountId]:[stacksRegion]
Successfully synthesized to [DIRECTORY PATH]/cdk.out
Supply a stack id (DataVaultingStack, EventProcessingStack) to display its template.
user@cdk-client>$ 
```

We're now ready to deploy the stacks.

Move onto [Module 3 - Deploy the CDK application stacks](MODULE3.md) or return to the [main page](README.md).