#!/bin/bash
#===================================================================================
# FILE: activate-gateway.sh
#
# USAGE: activate-gateway.sh
#       -t timezone e.g. GMT+0:00, GMT+3:00, GMT-5:00
#       [-h print usage syntax]IP address
#
# DESCRIPTION: Obtains activation key from newly provisioned AWS Storage Gateway
# and activates as a File Gateway.
#
# NOTES: Part of an AWS CDK application. View the README.md file in this repository 
# for further information on the application architecture. 
#===================================================================================

PATH=$PATH
varFile="vars.sh"
validTimezone=0
dateFormat="+%H:%M:%S"

function printUsage {
    echo -e "Usage: $0
    -t timezone e.g. GMT+0:00, GMT+3:00, GMT-5:00
    [-h print usage syntax]
    "
}

function getVpcEndpointId {
    export vpcEndpointId=`aws ssm get-parameters \
    --names "dataVaultingStackVpcEndpointId" \
    --query "Parameters[*].Value" | \
    grep "\"" | tr -d '"| '`
    timeLog "VPC Endpoint ID is: ${vpcEndpointId}"
}

function getVpcEndpointDns {
    export vpcEndpointDns=`aws ec2 describe-vpc-endpoints \
    --vpc-endpoint-ids ${vpcEndpointId} \
    --query "VpcEndpoints[*].DnsEntries[*].DnsName" | \
    grep vpce | head -1 | tr -d '"| |,'`
    timeLog "VPC Endpoint DNS name is: ${vpcEndpointDns}"
}

function getActivationKey {
    export activationKey=`curl "http://192.168.1.10/?gatewayType=FILE_S3&activationRegion=${region}&vpcEndpoint=${vpcEndpointDns}&no_redirect" 2>/dev/null`
    echo "Activation key is: ${activationKey}"
}

function activateStorageGateway {
    export gatewayArn=`aws storagegateway activate-gateway \
    --gateway-name "cdk-app" \
    --gateway-timezone ${timezone} \
    --activation-key ${activationKey} \
    --gateway-region ${region} \
    --gateway-type "FILE_S3" \
    --endpoint-url https://${vpcEndpointDns} \
    --query "GatewayARN" | \
    grep "\"" | tr -d '"| '`
    timeLog "Activated Gateway ARN: $gatewayArn"
}

function checkTimezoneFormats {
    END=12
    for ((x=1;x<=END;x++))
    do
        if [ $timezone == "GMT" ]
        then
            validTimezone=1
            timeLog "INFO: Timezone set to $timezone"
            break
        else
            timeZonePlus="GMT+"`expr 0 + $x`":00"
            timeZoneMinus="GMT-"`expr 13 - $x`":00"
            if [ $timeZonePlus == $timezone -o $timeZoneMinus == $timezone ]
            then
                timeLog "INFO: Timezone set to $timezone"
                validTimezone=1
                echo $timezone
            else
                validTimezone=0
            fi
        fi
    done
    if [ $validTimezone = 0 ]
    then
        timeLog "ERROR: Invalid timezone format"
        printUsage
        exit 1
    fi
}

function getOtherVars {
    export fileUploadBucketName=`aws ssm get-parameters \
    --names "fileUploadBucketName" \
    --query "Parameters[*].Value" | \
    grep "\"" | tr -d '"| '`
    export cdkApplicationScriptsBucketName=`aws ssm get-parameters \
    --names "cdkApplicationScriptsBucketName" \
    --query "Parameters[*].Value" | \
    grep "\"" | tr -d '"| '`
}

function writeVars {
    echo "gatewayArn=${gatewayArn}" >> ${varFile}
    echo "fileUploadBucketName=${fileUploadBucketName}" >> ${varFile}
    echo "cdkApplicationScriptsBucketName=${cdkApplicationScriptsBucketName}" >> ${varFile}
}

function timeLog {
    echo -n "`date ${dateFormat}` - "
    echo $1
}


function checkRegionConfig {
    if [ ! -e /home/`whoami`/.aws/config ]
    then
        timeLog "ERROR: Cannot find region in AWS CLI configuration file"
        timeLog "ERROR: Set this first by running aws configure"
        exit 1
    else
        region=`grep region /home/\`whoami\`/.aws/config | awk '{print $3}'`
    fi

    if [ -z $region ]
    then
        timeLog "ERROR: Cannot find region in AWS CLI configuration file"
        timeLog "ERROR: Set this first by running aws configure"
        exit 1
    else
        timeLog "INFO: AWS CLI region set to $region"
    fi
}

function runMain {
    echo "##############################################################################"
    echo "#    THIS SCRIPT WILL OBTAIN THE ACTIVATION KEY FROM THE STORAGE GATEWAY     #"
    echo "#            AND THEN ACTIVATE THE GATEWAY USING THE VPC ENDPOINT            #"
    echo "##############################################################################"
    echo ""
    timeLog "INFO: Checking AWS region configuration is set"
    checkRegionConfig
    echo ""
    timeLog "INFO: Checking timezone format"
    sleep 2
    checkTimezoneFormats
    echo ""
    timeLog "INFO: Getting value for the VPC Endpoint ID"
    sleep 2
    getVpcEndpointId
    echo ""
    timeLog "INFO: Getting value for the VPC Endpoint DNS name"
    sleep 2
    getVpcEndpointDns
    echo ""
    timeLog "INFO: Getting activation key from Storage Gateway"
    sleep 2
    getActivationKey
    echo ""
    timeLog "INFO: Activating Storage Gateway"
    sleep 2
    activateStorageGateway
    echo ""
    timeLog "INFO: Writing variable values to vars.sh"
    getOtherVars
    writeVars
    echo ""
    echo "COMPLETED"
    echo "#########"
}

while getopts ":r:t:h" scriptOptions; do
case ${scriptOptions} in
    t  )
        timezone=$OPTARG
        timezoneSet=1
        ;;    
    :  )
        timeLog "ERROR:"
        printUsage
        exit 1
        ;;
    h  )
        printUsage
        exit 0
        ;; 
    \? )
        timeLog "ERROR: Unknown option"
        printUsage
        exit 1
        ;;
esac
done

runMain