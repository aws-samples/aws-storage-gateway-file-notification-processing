# AWS CDK application workshop to process AWS Storage Gateway (File Gateway) file upload notifications

© 2021 Amazon Web Services, Inc. and its affiliates. All rights reserved. This sample code is made available under the MIT-0 license. See the LICENSE file.

Feedback: Contact atieka@amazon.co.uk, djsearle@amazon.co.uk.

---

# Module 1 - Solution components and architecture
For data vaulted via a File Gateway, the CDK application components work with the following principles:
* **Logical Datasets:** A group of files and directories stored in a uniquely named folder on a File Gateway file share. These files represent a single logical dataset to be vaulted to Amazon S3 and treated as a single entity for the purposes of downstream processing. The files are copied from a source location that mounts the File Gateway file share using NFS or SMB.
* **Logical Dataset IDs:** A unique string that identifies a specific logical dataset. This is used as part of the name for the root directory containing a single logical dataset created on a File Gateway file share. The Dataset ID allows the event processing flow to distinguish between different vaulted datasets and reconcile within them accordingly.
* **Data Files:** All files that constitute part of a logical dataset. These are written within a root logical dataset folder on a File Gateway file share. File upload notification events generated for data files are written, by the processing flow, to an Amazon DynamoDB table. Directories are treated as file objects for the purposes of uploads to Amazon S3 via File Gateway.
* **Manifest Files:** A file, one per logical dataset, that contains a manifest listing all data files that constitute that specific logical dataset. This is generated as part of the data vaulting operation for a logical dataset and is used by the processing flow to compare against data file upload events written to a DynamoDB table. Once both of these data sources are identical, it signifies the File Gateway has completed uploading all files to Amazon S3 that constitute that logical dataset and the data vaulting operation has completed.

The processing flow implemented by this CDK application contains the following mandatory, but configurable, parameters. These can be modified by editing the corresponding CDK context values in `cdk.context.json`:
* **Vault folder directory suffix name:** Context key name: `jobDirSuffixName`. The directory suffix name of the root folder containing a logical dataset copied to File Gateway. This is used by the processing flow to identify what directories being created on a File Gateway should be processed. Directories created that do not end in this suffix will be ignored. Default: `-vaultjob`. Do not modify this value for the workshop - can be modified if using your own data vaulting scripts.
* **Manifest file suffix name:** Context key name: `manifestSuffixName`. The suffix name for the logical dataset manifest file. This is used by the processing flow to identify what file should be read to ascertain the list of files constituting the logical dataset and used to reconcile against file upload notification events received. Default: `.manifest`. Do not modify this value for the workshop - can be modified if using your own data vaulting scripts.
* **Number of iterations in State Machine:** Context key name: `reconcileCountIterations`. The number of attempts the file upload reconciliation state machine will make to reconcile the contents of the logical dataset manifest file with the file upload notification events received. Due to the asynchronous nature in which File Gateway uploads files to Amazon S3, a manifest file may be uploaded prior to all data files in that logical dataset. This is especially the case for large datasets. Hence, iterating over the file upload reconciliation process is required. Default: `960`.
* **Wait time in State Machine:** Context key name: `reconcileWaitIterations`. The time, in seconds, to wait between each iteration of the file upload reconciliation state machine. Default: `30`. The total time the state machine will continue to attempt file upload reconciliation is a product of this parameter and the number of iterations in the state machine. At default values this works out to 8 hours.
* **AWS account ID:** Context key name: `stacksAccountId`. The AWS account ID/number to deploy the CDK application stacks into.
* **AWS region:** Context key name: `stacksRegion`. The AWS region to deploy the CDK application stacks into.

An example logical dataset directory structure:
```
[LOGICAL DATASET ID]-vaultjob (root logical dataset directory)
[LOGICAL DATASET ID]-vaultjob/[DATA FILE][..] (data files at top level)
[LOGICAL DATASET ID]-vaultjob/[DIRECTORY][..]/[DATA FILE][..] (data files at n levels)
[LOGICAL DATASET ID]-vaultjob/[LOGICAL DATASET ID].manifest (recursive list of all files and dirs)
```

## 1.1 CDK application architecture
The following diagram illustrates the architecture for the processing flow implemented by this CDK application. It details the individual execution stages for each of the two file types uploaded ("data" and "manifest" files). For a higher resolution image, view [`notification-processing-cdk-app-arch-high-res.png`](/images/arch/notification-processing-cdk-app-arch-high-res.png) within the `images/arch` folder of this repository:

![Event Processing Flow Logical Architecture](/images/arch/notification-processing-cdk-app-arch.png)

## 1.2 Example event processing flow execution timeline
The diagram [`notification-processing-example-data-vaulting-timeline.png`](/images/arch/notification-processing-example-data-vaulting-timeline.png) within the `images/arch` folder of this repository illustrates the timeline and execution steps implemented by this CDK application for the processing of File Gateway upload notifications (NOTE: this is a large, high resolution, image). It details an example scenario for a data vaulting operation and how each CDK resource created is executed, and in what order, during the event processing flow. NOTE: The "time" dimension in this diagram is not scaled or linear - it is meant as an indicative representation of the order in which resources are used in the example scenario illustrated.

## 1.3 CDK application stacks
This CDK application contains two stacks (listed in the order deployed in this workshop):
* **EventProcessingStack:**
Deploys the event processing architecture illustrated in **section 1.1** above, intended to be used with a Storage Gateway (File Gateway) configured to generate file upload notifications. More information on deploying this stack is provided in [**Module 3.1**](/modules/MODULE3.md#31-event-processing-stack). NOTE: This stack does not create the File Gateway or File Gateway client. These are created as part of the `DataVaultingStack`.

* **DataVaultingStack:**
Deploys a "minimal" VPC with two EC2 instances - a Storage Gateway (File Gateway) appliance and a File Gateway client. This stack is used to demonstrate an example data vaulting operation using a File Gateway appliance, triggering the event processing flow created by the `EventProcessingStack` above. The resources created by this stack are intended for temporary demonstration purposes and are used to illustrate a potential real-world use-case for the event processing flow. More information on deploying this stack is provided in [**Module 3.2**](/modules/MODULE3.md#32-data-vaulting-stack).

Move onto [Module 2 - CDK pre-requisites and preparation](/modules/MODULE2.md) or return to the [main page](README.md).