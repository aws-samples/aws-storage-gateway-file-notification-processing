#===================================================================================
# FILE: reconcile-iterator.py
#
# DESCRIPTION: Increments a ticker variable, that starts at 0, compares to a count
# variable and returns boolean variable if either match. Used to drive a defined 
# number of state iterations in the Step Functions state machine.
#
# NOTES: Part of an AWS CDK application. View the README.md file in this repository 
# for further information on the application architecture. 
#===================================================================================

import json

def lambda_handler(event, context):
    
    # Set variables based on values recieved from input payload into the Step
    # Functions state
    count = event['iterator']['Payload']['count']
    ticker = event['iterator']['Payload']['ticker']

    # Increment ticker
    ticker += 1

    # Return true if ticker and count are identical, or false otherwise
    return {
        'ticker': ticker,
        'count': count,
        'continue': ticker <= count,
        'statusCode': 200
    }
