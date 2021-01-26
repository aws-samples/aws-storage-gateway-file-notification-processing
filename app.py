#!/usr/bin/env python3
import sys
from aws_cdk import core
from storage_gateway_file_upload_notification_processing.storage_gateway_event_processing import EventProcessing
from storage_gateway_file_upload_notification_processing.storage_gateway_data_vaulting import DataVaulting

app = core.App()

account=app.node.try_get_context("stacksAccountId")
region=app.node.try_get_context("stacksRegion")

if account == "":
    print("ERROR: Please specify stacksAccountId value in cdk.context.json")
    sys.exit()
if region == "":
    print("ERROR: Please specify stacksRegion value in cdk.context.json")
    sys.exit()

env = core.Environment(
    region=region,
    account=account
 )

EventProcessingStack = EventProcessing(app, "EventProcessingStack", env=env)
DataVaultingStack= DataVaulting(app, "DataVaultingStack", fileUploadBucket=EventProcessingStack.fileUploadBucket, \
fileUploadBucketNameSsmParm=EventProcessingStack.fileUploadBucketNameSsmParm ,env=env)

app.synth()