#===================================================================================
# FILE: check-file-notification-type.py
#
# DESCRIPTION: Processes SQS message event payload to determine if a "data" or
# "manifest" file upload event was recieved. Sends an event to EventBridge specifying
# the type of file upload along with relevant metadata.
#
# NOTES: Part of an AWS CDK application. View the README.md file in this repository 
# for further information on the application architecture. 
#===================================================================================

import json
import boto3
import os
from dateutil import parser

eventBusClient = boto3.client('events')

def lambda_handler(event, context):
    
    # Set variables based on values recieved from SQS message
    for record in event['Records']:
        payLoad = json.loads(record["body"])
        objectKey = payLoad['detail']["object-key"]
        objectSize = int(payLoad['detail']["object-size"])
        bucketName = payLoad['detail']["bucket-name"]
        epochTime = int((parser.isoparse(payLoad['time'])).timestamp())
        setIdStr = objectKey.split('/', 1)[0]
        
        # Parse object key for required directory suffix name and determine if object 
        # is a "data" or "manifest" file
        if setIdStr.endswith(os.environ.get('jobDirSuffixName')):
            setId = setIdStr.split('-', 1)[0]
            if objectKey.endswith(setId + os.environ.get('manifestSuffixName')):
                putUploadEvent("Manifest", setId, epochTime, bucketName, objectKey, objectSize)
            else:
                putUploadEvent("Data", setId, epochTime, bucketName, objectKey, objectSize)

def putUploadEvent(uploadType, setId, epochTime, bucketName, objectKey, objectSize):
    # Create EventBridge event payload for either a "data" or "manifest" file notification
    # event and put to the custom EventBridge bus
    Entries=[
        {
            "DetailType": ""+ uploadType +" File Upload Event",
            "Source":"vault.application",
            "Detail":"{\"set-id\":\""+ setId +"\",\"event-time\":"+ str(epochTime) +",\"bucket-name\":\""+ bucketName +"\",\"object-key\":\""+ objectKey +"\",\"object-size\":"+ str(objectSize) +"}",
            "EventBusName" : os.environ.get('eventBusName')
        }
        ]
    eventBusClient.put_events(Entries=[Entries[0]])
                
    return {
        'statusCode': 200
    }