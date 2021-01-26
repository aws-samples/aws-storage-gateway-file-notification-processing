#===================================================================================
# FILE: reconcile-check.py
#
# DESCRIPTION: Reconciles the contents of a DynamoDB table, for a specific logical
# dataset, with the contents of a "manifest" file on S3 for the same logical dataset.
# Returns boolean variable if both these sources of data are identical, or not.
#
# NOTES: Part of an AWS CDK application. View the README.md file in this repository 
# for further information on the application architecture. 
#===================================================================================

import json
import boto3
import collections
import os

dynamoDbClient = boto3.client('dynamodb')
s3 = boto3.resource('s3')

def lambda_handler(event, context):

    # Set variables based on values recieved from input payload into the Step
    # Functions state
    setId=event['detail']['set-id']
    objectKey=event['detail']['object-key']
    bucketName=event['detail']['bucket-name']

    # Get the S3 key names stored in DynamoDB for the logical dataset
    response = dynamoDbClient.query(
        TableName=os.environ.get('dynamoDbTableName'),
        ExpressionAttributeValues={
            ':setId': {
                'S':setId,
            },
        },
        KeyConditionExpression='setId = :setId',
        ProjectionExpression='objectKey',
        )
    
    # Create a list from the key names
    keyNameList=[]
    for value in response['Items']:
        keyNameList.append(value['objectKey']['S'])
    
    # Get the manifest file for the logical dataset from S3 and create
    # a list from the contents
    manifestFile = s3.Object(bucketName, objectKey)
    manifestFileStr = manifestFile.get()['Body'].read().decode('utf-8')
    manifestList = manifestFileStr.splitlines()
    
    # Compare the list of S3 key names in DynamoDB with the file names in
    # the manifest file. Return True if identical, False if not
    keyNameList.sort()
    manifestList.sort()
    
    print(keyNameList)
    print(manifestList)
    
    return {
        'reconcileDone': keyNameList == manifestList,
        'statusCode': 200
    }