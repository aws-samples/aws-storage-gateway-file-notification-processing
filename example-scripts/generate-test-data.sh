#!/bin/bash
#===================================================================================
# FILE: generate-test-data.sh
#
# USAGE: generate-test-data.sh
#        -s total data size to create in GB
#        -b file creation batch size
#        -t target directory
#        [-l file size lower limit in MB]
#        [-u file size upper limit in MB]
#        [-h print usage syntax]
#
# DESCRIPTION: Script that generates a random number of files given a total data 
# size to be generated as an input option. This script will batch the creation of 
# files into simultaneous, parallel, executions based on a batch size input option.
# Lower and upper file size limits can be specified for the files generated, which
# will influence how many files are created for a given total data size. Without 
# these limits specified, defaults are used depending on the total data size
# specified (larger file sizes for larger data sizes).
#
# NOTES: Part of an AWS CDK application. View the README.md file in this repository 
# for further information on the application architecture. 
#===================================================================================

PATH=$PATH
totalSizeSet=0
batchSizeSet=0
tgtDirSet=0
fileSizeLowSet=0
fileSizeHighSet=0
startingSizeCountMb=0
batchCount=0
batchNum=1
batchSleep=1
dirCount=$((10 + RANDOM%(1+50-10)))
dirArray=()
fileArray=()
spinnerArray=("-", "\\", "|", "/")
dateFormat="+%H:%M:%S"

function setFileSizeRanges {
    if [ $totalSizeGb -le 100 ]
    then
        fileSizeLow=10
        fileSizeHigh=1000
        timeLog "INFO: Defaulting to $fileSizeLow MB and $fileSizeHigh MB for lower and higher file size limits"
    elif [ $totalSizeGb -ge 101 -a $totalSizeGb -le 200 ]
    then
        fileSizeLow=20
        fileSizeHigh=2000
        timeLog "INFO: Defaulting to $fileSizeLow MB and $fileSizeHigh MB for lower and higher file size limits"
    elif [ $totalSizeGb -ge 201 -a $totalSizeGb -le 300 ]
    then
        fileSizeLow=30
        fileSizeHigh=3000
        timeLog "INFO: Defaulting to $fileSizeLow MB and $fileSizeHigh MB for lower and higher file size limits"
    elif [ $totalSizeGb -ge 301 -a $totalSizeGb -le 400 ]
    then
        fileSizeLow=40
        fileSizeHigh=4000
        timeLog "INFO: Defaulting to $fileSizeLow MB and $fileSizeHigh MB for lower and higher file size limits"
    elif [ $totalSizeGb -ge 401 ]
    then
        fileSizeLow=50
        fileSizeHigh=5000
        timeLog "INFO: Defaulting to $fileSizeLow MB and $fileSizeHigh MB for lower and higher file size limits"
    fi
}

function generateDirArray {
    timeLog "INFO: Generating directory names"
    for ((x=0;x<=$dirCount;x++))
    do
        dirName="dir-"`head /dev/urandom | LC_CTYPE=C tr -dc A-Za-z0-9 | head -c 12 ; echo ''`
        dirArray[$x]=$dirName
    done
    dirArrayLength=`expr "${#dirArray[@]}" - 1`
    timeLog "INFO: Done - ${#dirArray[@]} directories to be created"
}

function generateFileArray {
    timeLog "INFO: Generating file names"
    while [ $startingSizeCountMb -le $totalSizeMb ]
    do
        fileSize=$((RANDOM * (${fileSizeHigh}-${fileSizeLow+1}) / 32768 + ${fileSizeLow}))
        fileSizeBytes=`expr $fileSize \* 1024 \* 1024`
        startingSizeCountMb=`expr $fileSize + $startingSizeCountMb`
        randomDirNo=$((0 + RANDOM%(1+$dirArrayLength-0)))
        fileName="file-"`head /dev/urandom | LC_CTYPE=C tr -dc A-Za-z0-9 | head -c 8 ; echo ''`
        fileArray+=(${dirArray[$randomDirNo]}"/"$fileName":"$fileSizeBytes)
    done
    fileArrayLength=`expr "${#fileArray[@]}" - 1`
    timeLog "INFO: Done - ${#fileArray[@]} files to be created"
}

function createDirs {
    timeLog "INFO: Starting to create directories"
    formattedDirArray="${dirArray[@]%,}"
    for x in ${formattedDirArray[@]}
    do
        mkdir $tgtDir/$x
    done
    timeLog "INFO: Done"
}

function createFiles {
    timeLog "INFO: Starting to create files"
    createdFileCount=0
    fileRemainderCount=0
    totalFileCount=${#fileArray[@]}
    formattedFileArray="${fileArray[@]%,}"
    timeLog "INFO: Initiating file creation for batch $batchNum"
    for x in ${formattedFileArray[@]}
    do
        if [ $batchCount -eq $batchSize ]
        then
            timeLog "INFO: Monitoring for batch completion"
            spinnerSymbolNum=0
            while true
            do
                spinnerSymbol=`echo ${spinnerArray[$spinnerSymbolNum]} | tr -d ','`
                processCount=`ps -ef | grep "openssl rand " | grep -v grep | wc -l | awk '{print $1}'`
                if [ $processCount -eq 0 ]
                then
                    break
                else
                    timeLogSpin "INFO: Batch $batchNum creation still in progress [${spinnerSymbol}] \r"
                fi
                if [ $spinnerSymbolNum -eq 3 ]
                then
                    spinnerSymbolNum=0
                else
                    spinnerSymbolNum=`expr $spinnerSymbolNum + 1`
                fi
                sleep $batchSleep
            done
            timeLog "INFO: Batch $batchNum complete - created $createdFileCount files out of a total ${#fileArray[@]}"
            echo ""
            batchCount=0
            batchNum=`expr $batchNum + 1`
            if [ $fileRemainderCount -lt $batchSize ]
            then
                timeLog "INFO: Initiating final batch $batchNum"
            else
                timeLog "INFO: Initiating file creation for batch $batchNum"
            fi
        fi
        createdFileName=`echo $x | awk -F ":" '{print $1}'`
        createdFileSize=`echo $x | awk -F ":" '{print $2}'`
        ( openssl rand $createdFileSize > $tgtDir/$createdFileName & )
        createdFileCount=`expr $createdFileCount + 1`
        fileRemainderCount=`expr $totalFileCount - $createdFileCount`
        batchCount=`expr $batchCount + 1`       
    done
    timeLog "INFO: Monitoring for final batch completion"
    spinnerSymbolNum=0
    while true
    do
        spinnerSymbol=`echo ${spinnerArray[$spinnerSymbolNum]} | tr -d ','`
        processCount=`ps -ef | grep "openssl rand " | grep -v grep | wc -l | awk '{print $1}'`
        if [ $processCount -eq 0 ]
        then
            break
        else
            timeLogSpin "INFO: Batch $batchNum creation still in progress [${spinnerSymbol}] \r"
        fi
        if [ $spinnerSymbolNum -eq 3 ]
        then
            spinnerSymbolNum=0
        else
            spinnerSymbolNum=`expr $spinnerSymbolNum + 1`
        fi
        sleep $batchSleep
    done
    timeLogSpin "INFO: Final batch completed                                               "
    echo ""
    echo ""
    echo "COMPLETED"
    echo "#########"
    timeLog "INFO: Done creating a total of ${#fileArray[@]} files                         "
    timeLog "INFO: Checking amount of data and files created                               "
    writtenDataSize=`du -sh ${tgtDir} | awk '{print $1}'`
    writtenFiles=`ls -lR ${tgtDir} | grep "file-" | wc -l`
    timeLog "INFO: Created a total of ${writtenDataSize} of data and $writtenFiles files           "
    echo ""
}

function printUsage {
    echo -e "Usage: $0
    -s total data size to create in GB
    -b file creation batch size
    -t target directory
    [-l file size lower limit in MB]
    [-u file size upper limit in MB]
    [-h print usage syntax]
    "
}

while getopts ":s:b:t:l:u:h" scriptOptions; do
case ${scriptOptions} in
    s  )
        if ! [[ $OPTARG =~ ^-?[0-9]+$ ]]
        then
            timeLog "ERROR: Specify total data size as an integer"
            exit 1
        else
            totalSizeGb=$OPTARG
            totalSizeSet=1
        fi
        ;;
    b  )
        if ! [[ $OPTARG =~ ^-?[0-9]+$ ]]
        then
            timeLog "ERROR: Specify file creation batch size as an integer"
            exit 1
        else
            batchSize=$OPTARG
            batchSizeSet=1
        fi
        ;;
    l  )
        if ! [[ $OPTARG =~ ^-?[0-9]+$ ]]
        then
            timeLog "ERROR: Specify file size lower limit as an integer"
            exit 1
        else
            fileSizeLow=$OPTARG
            fileSizeLowSet=1
        fi
        ;;
    u  )
        if ! [[ $OPTARG =~ ^-?[0-9]+$ ]]
        then
            timeLog "ERROR: Specify file size higher limit as an integer"
            exit 1
        else
            fileSizeHigh=$OPTARG
            fileSizeHighSet=1
        fi
        ;;
    t  )
        tgtDir=$OPTARG
        tgtDirSet=1
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

function checkArgs {
    if ! command -v openssl &> /dev/null
    then
        timeLog "ERROR: openssl was not found"
        exit 1
    fi
    if [ $totalSizeSet -eq 1 -a $batchSizeSet -eq 1 -a $tgtDirSet -eq 1 ]
    then
        :
    else
        timeLog "ERROR: Specify all required options"
        printUsage
        exit 1
    fi
    if [ $fileSizeLowSet -eq 1 -a $fileSizeHighSet -eq 1 ]
    then
        if [ $fileSizeHigh -lt $fileSizeLow ]
        then
            timeLog "ERROR: File size lower limit should be less than higher file size limit"
            exit 1
        else
            timeLog "INFO: Using $fileSizeLow MB and $fileSizeHigh MB for lower and higher file size limits"
        fi
    else
        setFileSizeRanges
        fileSizeLowSet=1
        fileSizeHighSet=1
    fi
    if [ ! -d $tgtDir ]
    then
        timeLog "INFO: Making target directory $tgtDir"
        mkdir $tgtDir
        if [ $? -ne 0 ]
        then
            timeLog "ERROR: Cannot make target directory"
            exit 1
        fi
    else
        timeLog "INFO: Creating files in $tgtDir"
    fi
}

function timeLog {
    echo -n "`date ${dateFormat}` - "
    echo $1
}

function timeLogSpin {
    echo -ne " `date ${dateFormat}` - $1 \r"
}

function runMain {
    echo "##############################################################################"
    echo "# THIS SCRIPT WILL CREATE A RANDOM NUMBER OF FILES CONTAINING RANDOM CONTENT #"
    echo "#                    UP TO THE TOTAL DATA SIZE SPECIFIED                     #"
    echo "##############################################################################"
    echo ""
    checkArgs
    totalSizeMb=`expr $totalSizeGb \* 1024`
    timeLog "INFO: Creating files that will sum to a total data size of $totalSizeGb GB"
    echo ""
    echo "GENERATING DIRECTORY AND FILE STRUCTURES"
    echo "########################################"
    generateDirArray
    generateFileArray
    echo ""
    echo "CREATING DIRECTORIES"
    echo "####################"
    createDirs
    echo ""
    echo "CREATING FILES"
    echo "##############"
    createFiles
}

runMain