# AWS CDK application workshop to process AWS Storage Gateway (File Gateway) file upload notifications

© 2021 Amazon Web Services, Inc. and its affiliates. All rights reserved. This sample code is made available under the MIT-0 license. See the LICENSE file.

Feedback: Contact atieka@amazon.co.uk, djsearle@amazon.co.uk.

---

# Module 7 - Remove CDK application resources
All resources created by this CDK application can be removed by destoying the stacks. Prior to performing this, the Amazon S3 buckets created must be emptied. We'll also logically delete the Storage Gateway (the physical EC2 Storage Gateway instance will be removed when destroying the `DataVaultingStack`). **NOTE:** Only empty the Amazon S3 buckets when you have completed this workshop and no longer require the objects within them. The File Gateway has IAM permissions that **only** allow it to remove objects from the Amazon S3 buckets created by this workshop:

1. Go back to your File Gateway client terminal login. If this has timed out, repeat steps **1-3** in [**Module 4.1**](MODULE4.md#41-log-onto-the-file-gateway-client).

2. Source the values we retrieved earlier for the Amazon S3 bucket names and File Gateway ARN (when executing the File Gateway activation script in [**Module 4.2**](MODULE4.md#42-activate-the-file-gateway)). The following command also prints the variable values to the screen, to confirm they have been sourced successfully:
    ```console
    ssm-user@FileGatewayClient>$ source ./vars.sh && \
    echo "" && \
    echo "Storage Gateway ARN: $gatewayArn" && \
    echo "Amazon S3 file upload bucket name: $fileUploadBucketName" && \
    echo "Amazon S3 CDK application scripts bucket name: $cdkApplicationScriptsBucketName" 
    ```

3. Logically delete the Storage Gateway: 
    ```console
    ssm-user@FileGatewayClient>$ aws storagegateway delete-gateway --gateway-arn $gatewayArn
    ```

    Below is a screenshot illustrating an example delete command:

    ![AWS Storage Gateway CLI delete](images/screenshots/file-gateway-aws-cli-delete.png)

4. Empty the Amazon S3 buckets:
    ```console
    ssm-user@FileGatewayClient>$ aws s3 rm s3://$fileUploadBucketName --recursive
    ssm-user@FileGatewayClient>$ aws s3 rm s3://$cdkApplicationScriptsBucketName --recursive
    ```

    Below is a screenshot illustrating an example delete command on the Amazon S3 CDK application scripts bucket:

    ![Amazon S3 CDK application scripts empty bucket](images/screenshots/s3-cdk-app-scripts-bucket-empty.png)

5. You can now destroy the CDK application stacks:
    ```console
    user@cdk-client>$ cdk destroy DataVaultingStack
    user@cdk-client>$ cdk destroy EventProcessingStack
    ```

You've now completed this workshop! Return to the [main page](README.md).