# AWS CDK application workshop to process AWS Storage Gateway (File Gateway) file upload notifications

© 2021 Amazon Web Services, Inc. and its affiliates. All rights reserved. This sample code is made available under the MIT-0 license. See the LICENSE file.

Feedback: Contact atieka@amazon.co.uk, djsearle@amazon.co.uk.

---

# Module 6 - Observe the event processing flow
To observe the event processing flow in action, for this example data vaulting operation, you can inspect the logs/objects/items/invocations created within the multiple resources deployed by the `EventProcessingStack`:

Viewing the following resources in the order listed demonstrates how the processing flow executed: 

* **Amazon S3 Bucket:** Objects created in the Amazon S3 bucket, uploaded by the File Gateway.
* **Amazon CloudWatch Logs:** Logs created to record "data" and "manifest" file upload event types.
* **Amazon DynamoDB Table:** Items created to record the receipt of upload events.
* **AWS Step Functions state machine:** State machine execution that reconciles "manifest" file contents against the file upload events recieved.
* **Amazon CloudWatch Logs:** File upload reconciliation events emitted by the Step Functions state machine.

Below are some AWS console screenshots illustrating the information logged/written to these resource types. Vist these same console pages in your account to view the corresponding information for your example data vaulting operation:

* **Amazon S3 Bucket:** [Amazon S3 console link](https://console.aws.amazon.com/s3). Files and directories written to `/mnt/vaultdata` uploaded to Amazon S3 by the File Gateway for this example data vaulting operation. The relevant Amazon S3 bucket name will begin with `eventprocessingstack-fileuploadbucket`:

    ![Amazon S3 file upload bucket](images/screenshots/s3-uploaded-files.png)

* **CloudWatch Logs "data" file Log group:** [CloudWatch Logs console link](https://console.aws.amazon.com/cloudwatch). File upload notification events for "data" files. You'll notice the logical dataset ID `set-id` is ascertained from the name of the logical dataset directory created by the data vaulting script in [**Module 5.3**](MODULE5.md#53-vault-the-sample-data). It follows the scheme described in [**Module 1**](MODULE1.md). The relevant CloudWatch Logs log group name will begin with `EventProcessingStack-dataFileUpload`:

    ![Amazon CloudWatch data file upload event Log](images/screenshots/cloudwatch-data-file-upload-event-log.png)

* **DynamoDB Table:** [DynamoDB console link](https://console.aws.amazon.com/dynamodb). Relevant metadata from the file upload notifications are written to this table, an item will exist for every upload notification. The relevant DynamoDB table name will begin with `EventProcessingStack-fileUploadEventTable`:

    ![Amazon DynamoDB table](images/screenshots/dynamodb-table.png)

* **Step Functions state machine:** [Step Functions console link](https://console.aws.amazon.com/states). A successfully executed file upload reconciliation state machine - NOTE: The state `waitBetweenIterationsState` may be coloured white (instead of green). This simply means the state machine did not need to iterate (and wait) in order to reconcile upload events with the contents of the "manifest" file - i.e. after uploading the "manifest" file, the File Gateway completed all remaining "data" file uploads within the waiting time period set by the `reconcileWaitIterations` CDK context key contained in the `cdk.context.json` file (for a reminder on this CDK context key see [**Module 1**](MODULE1.md)). The relevant state machine name will begin with `reconcileStateMachine`:

    ![AWS Step Functions reconciliation state machine](images/screenshots/step-functions-state-machine.png)

* **CloudWatch Logs "reconcile notification" Log group:** [CloudWatch Logs console link](https://console.aws.amazon.com/cloudwatch). A successful file upload reconciliation event is emitted by the Step Functions state machine - this is the final stage in the event processing flow for a particular logical dataset. The relevant CloudWatch Logs log group name will begin with `EventProcessingStack-reconcileNotifySuccessful`:

    ![Amazon CloudWatch reconcile notify event log](images/screenshots/cloudwatch-reconcile-notify-event-log.png)

The structure of the "reconcile notification" event, which contains metadata regarding the logical dataset ID and manifest file, is as follows:

```
{
    "version": "0",
    "id": "[ID]",
    "detail-type": "File Upload Reconciliation Successful",
    "source": "vault.application",
    "account": "[ACCOUNT ID]",
    "time": "[YYYY-MM-DDTHH:MM:SSZ]",
    "region": "[REGION]",
    "resources": [],
    "detail": {
        "set-id": "[LOGICAL DATASET ID]",
        "event-time": [EPOCH TIME],
        "bucket-name": "[BUCKET NAME]",
        "object-key": "[MANIFEST FILE OBJECT]",
        "object-size": [SIZE BYTES]
    }
}
```

Since the "reconcile notification" event was sent to the EventBridge custom event bus, this solution can be extended/customised by adding additional targets in the EventBridge rule to allow for other applications/processes to consume the notification and perform further downstream processing on the logical dataset.

The File Gateway implements a write-back cache and asynchronously uploads data to Amazon S3. It optimizes cache usage and the order of file uploads. It may also perform temporary partial uploads during the process of fully uploading a file (the partial copy can be seen momentarily in the Amazon S3 bucket at a smaller size than the original). Hence, you may observe a small delay and/or non-sequential uploads when comparing objects appearing in the Amazon S3 bucket with the arrival of corresponding Amazon CloudWatch Logs.

Since File Upload notifications are **only** generated by the File Gateway when files have been **completely** uploaded to Amazon S3, it is in these scenarios that the File upload notification feature becomes a powerful mechanism to co-ordinate downstream processing. This example data vaulting operation is a good demonstration of real-world scenarios where a File Gateway is often managing hundreds of GBs of uploads to Amazon S3 for hundreds/thousands of files copied by multiple clients.

Move onto [Module 7 - Cleanup](MODULE7.md) or return to the [main page](README.md).