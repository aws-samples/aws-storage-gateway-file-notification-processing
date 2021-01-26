#===================================================================================
# FILE: file-upload-event-writer.py
#
# DESCRIPTION: Processes EventBridge event payload to write metadata for file upload
# notifications to a DynamoDB table.
#
# NOTES: Part of an AWS CDK application. View the README.md file in this repository 
# for further information on the application architecture. 
#===================================================================================

import json
import boto3
import os

dynamoDbClient = boto3.client('dynamodb')

def lambda_handler(event, context):

    # Set variables based on values recieved from EventBridge event
    setId=event['detail']['set-id']
    eventTime=event['detail']['event-time']
    bucketName=event['detail']['bucket-name']
    objectKey=event['detail']['object-key']
    objectSize=event['detail']['object-size']
    
    # Write metadata to the DynamoDB table
    dynamoDbClient.put_item(
        TableName=os.environ.get('dynamoDbTableName'),
        Item={
            'setId': {
                'S':setId,
            },
            'objectKey': {
                'S':objectKey,
            },
            'bucketName': {
                'S':bucketName,
            },
            'objectSize': {
                'N':str(objectSize),
            },
            'eventTime': {
                'N':str(eventTime),
            },
        },
        )
    
    return {
        'statusCode': 200
    }
