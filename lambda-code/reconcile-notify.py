#===================================================================================
# FILE: reconcile-notify.py
#
# DESCRIPTION: Sends an event to an EventBridge custom bus based on whether the file
# upload reconciliation task in the Step Function state machine was successful or
# timed out (i.e. reached maximum number of iterations). The event sent contains 
# relevant metadata.
#
# NOTES: Part of an AWS CDK application. View the README.md file in this repository 
# for further information on the application architecture. 
#===================================================================================

import json
import boto3
import os

eventBusClient = boto3.client('events')

def lambda_handler(event, context):

    # Set variables based on values recieved from input payload into the Step
    # Functions state
    setId=event['detail']['set-id']
    epochTime=event['detail']['event-time']
    bucketName=event['detail']['bucket-name']
    objectKey=event['detail']['object-key']
    objectSize=event['detail']['object-size']
    reconcileDone=event['reconcilecheck']['Payload']['reconcileDone']

    # Check if reconciliation task was successful or timed out, based on
    # boolean variable set by previous task state in state machine
    if reconcileDone == True:
        notifyStatus='Successful'
    else:
        notifyStatus='Timeout'

    # Create EventBridge event payload stipulating success or timeout and 
    # put to the custom EventBridge bus
    Entries=[
        {
            "DetailType": "File Upload Reconciliation "+ notifyStatus +"",
            "Source":"vault.application",
            "Detail":"{\"set-id\":\""+ setId +"\",\"event-time\":"+ str(epochTime) +",\"bucket-name\":\""+ bucketName +"\",\"object-key\":\""+ objectKey +"\",\"object-size\":"+ str(objectSize) +"}",
            "EventBusName" : os.environ.get('eventBusName')
        }
        ]
    eventBusClient.put_events(Entries=[Entries[0]])
    
    return {
        'statusCode': 200
    }
