#!/bin/bash
#===================================================================================
# FILE: vault-data-example.sh
#
# USAGE: vault-data-example.sh
#        -s source directory
#        -t target directory
#        [-h print usage syntax]
#
# DESCRIPTION: Simple script that copies files and directories from a source
# directory to a target directory and generates a "manifest" file that lists the
# directories and files copied, including the manifest file.
#
# NOTES: Part of an AWS CDK application. View the README.md file in this repository 
# for further information on the application architecture. 
#===================================================================================

PATH=$PATH
vaultSetId=`head /dev/urandom | LC_CTYPE=C tr -dc A-Za-z0-9 | head -c 16 ; echo ''`
srcDirSet=0
tgtDirSet=0
vaultJobSuffix="-vaultjob"
manifestSuffix=".manifest"
copyMonitorSleep=1
spinnerArray=("-", "\\", "|", "/")
dateFormat="+%H:%M:%S"

function printUsage {
	echo -e "Usage: $0
	-s source directory
	-t target directory
	[-h print usage syntax]
	"
}

while getopts ":s:t:h" scriptOptions; do
case ${scriptOptions} in
	s  )
		srcDir=$OPTARG
		srcDirSet=1
		;;
	t  )
		tgtDirRoot=$OPTARG
		tgtDir="${tgtDirRoot}/${vaultSetId}${vaultJobSuffix}"
		tgtDirSet=1
		;;
	h  )
		printUsage
		exit 0
		;;
	:  )
		timeLog "ERROR: Specify all required options"
		printUsage
		exit 1
		;;
	\? )
		timeLog "ERROR: Unknown option"
		printUsage
		exit 1
		;;
esac
done

function checkArgs {
	if [ $srcDirSet -eq 1 -a $tgtDirSet -eq 1 ]
	then
		:
	else
		timeLog "ERROR: Specify all required options"
		printUsage
		exit 1
	fi
	if [ ! -d $srcDir ]
	then
		timeLog "ERROR: Source directory $srcDir does not exist"
		exit 1
	fi
	if [ `echo "${tgtDirRoot: -1}" | grep "/"` ]
	then
		tgtDirRoot="${tgtDirRoot%?}"
		tgtDir="${tgtDirRoot}/${vaultSetId}${vaultJobSuffix}"
	fi
}

function vaultData {
	timeLog "INFO: Logical dataset ID is ${vaultSetId}"
	timeLog "INFO: Logical dataset target directory name is ${tgtDir}"
	timeLog "INFO: Copying from $srcDir to $tgtDir"

	# Make root of target directory if it doesn't exist
	if [ ! -d $tgtDirRoot ]
	then
		mkdir ${tgtDirRoot}
	fi

	# Make target directory
	mkdir ${tgtDir}

	# Copy files using xargs for parallel execution
	( ls ${srcDir} | xargs -n1 -P5 -I% cp -rp ${srcDir}/% ${tgtDir}/ & )
	timeLog "INFO: Monitoring copy operation"
	spinnerSymbolNum=0
	while true
	do
		spinnerSymbol=`echo ${spinnerArray[$spinnerSymbolNum]} | tr -d ','`
		sizeCopiedMb=`du -sm ${tgtDir} | awk '{print $1}'`
		sizeCopiedGb=`echo 'scale=2; '$sizeCopiedMb' / 1024' | bc -l`
		processCount=`ps -ef | grep "xargs -n1 -P5 -I% cp -rp ${srcDir}" | grep -v grep | wc -l | awk '{print $1}'`
		if [ $processCount -eq 0 ]
		then
			break
		else
			timeLogSpin "INFO: Copy still in progress ${sizeCopiedGb}GB done [${spinnerSymbol}] \r"
		fi
		if [ $spinnerSymbolNum -eq 3 ]
		then
			spinnerSymbolNum=0
		else
			spinnerSymbolNum=`expr $spinnerSymbolNum + 1`
		fi
		sleep $copyMonitorSleep
	done
	sizeCopied=`du -sh ${tgtDir} | awk '{print $1}'`
	timeLogSpin "INFO: Copy operation has now completed - $sizeCopied copied"
}

function generateManifest {
	# Define manifest file location
	manifestFile="${tgtDir}/${vaultSetId}${manifestSuffix}"
	
	timeLog "INFO: Manifest file is ${vaultSetId}${manifestSuffix}"
	timeLog "INFO: Generating list of directories and files"

	# Generate manifest file in expected format
	cd ${tgtDirRoot}
	find ${vaultSetId}${vaultJobSuffix} -type d >> ${manifestFile}
	find ${vaultSetId}${vaultJobSuffix} -type f >> ${manifestFile}
	timeLog "INFO: Created manifest file"
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
	echo "#  THIS SCRIPT WILL COPY FILES AND DIRECTORIES FROM A SOURCE DIRECTORY TO A  #"
	echo "#     TARGET DIRECTORY AND GENERATE A MANIFEST FILE LISTING COPIED ITEMS     #"
	echo "##############################################################################"
	checkArgs
	echo ""
	echo "STARTING COPY"
	echo "#############"
	vaultData
	echo ""
	echo ""
	echo "CREATING MANIFEST"
	echo "#################"
	generateManifest
	echo ""
	echo "COMPLETED"
	echo "#########"
	timeLog "INFO: Done"
}

runMain