#===================================================================================
# FILE: storage_gateway_event_processing.py
#
# DESCRIPTION: Stack definition for an AWS Storage Gateway file upload notification 
# processing CDK application. See NOTES below.
#
# NOTES: Part of an AWS CDK application. View the README.md file in this repository 
# for further information on the application architecture. 
#===================================================================================

from aws_cdk import (
    core,
    aws_s3 as s3,
    aws_iam as iam,
    aws_events as events,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_sqs as sqs,
    aws_events_targets as targets,
    aws_lambda_event_sources as sources,
    aws_logs as logs,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_ssm as ssm
)

class EventProcessing(core.Stack):
    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Define AWS account ID and region, from CloudFormation psuedo parameters, in order to generate 
        # ARN values. Allows for the formation of IAM policy statement with least privilege for 
        # the Amazon EventBridge default bus
        accountId = core.Aws.ACCOUNT_ID
        regionName = core.Aws.REGION

        # Amazon DynamoDB table to store file upload notification events. NOTE: removal policy set 
        # to destroy, hence this table will be deleted with the CDK stack
        fileUploadEventTable = dynamodb.Table(
            self,
            "fileUploadEventTable",
            partition_key=dynamodb.Attribute(name="setId", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode('PAY_PER_REQUEST'),
            sort_key=dynamodb.Attribute(name="objectKey", type=dynamodb.AttributeType.STRING),
            removal_policy=core.RemovalPolicy.DESTROY
        )
        
        # Amazon S3 bucket to store file uploads from AWS Storage Gateway. NOTE: removal policy set 
        # to destroy, hence this bucket should be emptied prior to destroying the CDK stack (buckets
        # cannot be emptied via the CDK/CloudFormation without using custom resources)
        fileUploadBucket = s3.Bucket(
            self,
            "fileUploadBucket",
            removal_policy=core.RemovalPolicy.DESTROY
        )
        self.fileUploadBucket = fileUploadBucket

        # Custom Amazon EventBridge Bus
        customEventBus = events.EventBus(
            self,
            "customEventBus"
        )

        # Define generic IAM statements that will be required by multiple resources
        customEventBusIamPolicyStatement = iam.PolicyStatement(
            actions=[
                "events:PutEvents"
            ],
            effect=iam.Effect('ALLOW'),
            resources=[customEventBus.event_bus_arn]
        )

        # "Check file upload type" AWS Lambda function with required IAM policy and role
        checkFileUploadTypeLambdaIamRole = iam.Role(
            self,
            "checkFileUploadTypeLambdaIamRole",
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com')    
        )
        checkFileUploadTypeLambdaIamPolicy = iam.Policy(
            self,
            "checkFileUploadTypeLambdaIamPolicy",
            statements=[
                customEventBusIamPolicyStatement
            ],
            roles=[checkFileUploadTypeLambdaIamRole]
        )
        checkFileUploadTypeLambda = _lambda.Function(
            self, 
            "checkFileUploadTypeLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.asset("lambda-code"),
            handler='check-file-notification-type.lambda_handler',
            environment={
                "eventBusName": customEventBus.event_bus_name,
                "manifestSuffixName": self.node.try_get_context("manifestSuffixName"),
                "jobDirSuffixName": self.node.try_get_context("jobDirSuffixName")
            },
            role=checkFileUploadTypeLambdaIamRole
        )
        checkFileUploadTypeLambdaIamPolicyStatementWriteLogs = iam.PolicyStatement(
            actions=[
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            effect=iam.Effect('ALLOW'),
            resources=[checkFileUploadTypeLambda.log_group.log_group_arn]           
        )
        checkFileUploadTypeLambdaIamPolicy.add_statements(checkFileUploadTypeLambdaIamPolicyStatementWriteLogs)

        # Amazon SQS queue
        fileUploadEventSqsQueue = sqs.Queue(
            self,
            "fileUploadEventSqsQueue"
        )

        # Add the Amazon SQS queue as the event source for the "check file upload type" AWS 
        # Lambda function
        checkFileUploadTypeLambda.add_event_source(sources.SqsEventSource(fileUploadEventSqsQueue))

        # Amazon EventBridge rule with an associated target that routes file upload notification 
        # events to the Amazon SQS queue
        
        fileNotificationPattern = events.EventPattern(
            source=["aws.storagegateway"],
            detail_type=["Storage Gateway Object Upload Event"]
        )
        fileNotificationRule = events.Rule(
            self,
            "fileNotificationRule",
            event_pattern=fileNotificationPattern
        )
        fileNotificationRule.add_target(targets.SqsQueue(fileUploadEventSqsQueue))

        # "File upload notification writer" AWS Lambda function with required IAM policy and role
        fileUploadEventWriterLambdaIamRole = iam.Role(
            self,
            "fileUploadEventWriterLambdaIamRole",
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com')
        )
        fileUploadEventWriterLambdaIamPolicy = iam.Policy(
            self,
            "fileUploadEventWriterLambdaIamPolicy",
            roles=[fileUploadEventWriterLambdaIamRole]
        )
        fileUploadEventWriterLambda = _lambda.Function(
            self,
            "fileUploadEventWriterLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.asset("lambda-code"),
            handler='file-upload-event-writer.lambda_handler',
            environment={
                "dynamoDbTableName": fileUploadEventTable.table_name
            },
            role=fileUploadEventWriterLambdaIamRole
        )
        fileUploadEventWriterLambdaIamPolicyStatementDynamoDb = iam.PolicyStatement(
            actions=[
                "dynamodb:PutItem"
            ],
            effect=iam.Effect('ALLOW'),
            resources=[
                fileUploadEventTable.table_arn
            ]
        )
        fileUploadEventWriterLambdaIamPolicyStatementLogs = iam.PolicyStatement(
            actions=[
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            effect=iam.Effect('ALLOW'),
            resources=[fileUploadEventWriterLambda.log_group.log_group_arn]            
        )
        fileUploadEventWriterLambdaIamPolicy.add_statements(fileUploadEventWriterLambdaIamPolicyStatementDynamoDb)
        fileUploadEventWriterLambdaIamPolicy.add_statements(fileUploadEventWriterLambdaIamPolicyStatementLogs)

        # Amazon CloudWatch log groups for events created by the "check file upload type" AWS 
        # Lambda function
        dataFileUploadEventLogGroup = logs.LogGroup(
            self,
            "dataFileUploadEventLogGroup",
            removal_policy=core.RemovalPolicy.DESTROY
        )
        manifestFileUploadEventLogGroup = logs.LogGroup(
            self,
            "manifestFileUploadEventLogGroup",
            removal_policy=core.RemovalPolicy.DESTROY
        )

        # Amazon EventBridge rules for the custom event bus to route "data" and "manifest" file upload 
        # events sent by the "check file upload type" AWS Lambda function to the relevant targets -  
        # the "file upload notification writer" AWS Lambda function and separate Amazon CloudWatch 
        # log groups 
        dataFileUploadEventPattern = events.EventPattern(
            source=["vault.application"],
            detail_type=["Data File Upload Event"]
        )
        dataFileUploadEventRule = events.Rule(
            self,
            "dataFileUploadEventRule",
            event_bus=customEventBus,
            event_pattern=dataFileUploadEventPattern
        )
        manifestFileUploadEventPattern = events.EventPattern(
            source=["vault.application"],
            detail_type=["Manifest File Upload Event"]
        )
        manifestFileUploadEventRule = events.Rule(
            self,
            "manifestFileUploadEventRule",
            event_bus=customEventBus,
            event_pattern=manifestFileUploadEventPattern
        )
        dataFileUploadEventRule.add_target(targets.LambdaFunction(fileUploadEventWriterLambda))
        dataFileUploadEventRule.add_target(targets.CloudWatchLogGroup(dataFileUploadEventLogGroup))
        manifestFileUploadEventRule.add_target(targets.LambdaFunction(fileUploadEventWriterLambda))
        manifestFileUploadEventRule.add_target(targets.CloudWatchLogGroup(manifestFileUploadEventLogGroup))
    
        # AWS Lambda function used by the Step Functions "reconcile file uploads" state machine 
        # that provides a simple iterator. Created with required IAM policy and role
        reconcileIteratorLambdaIamRole = iam.Role(
            self,
            "reconcileIteratorLambdaIamRole",
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com')
        )
        reconcileIteratorLambda = _lambda.Function(
            self,
            "reconcileIteratorLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.asset("lambda-code"),
            handler='reconcile-iterator.lambda_handler',
            role=reconcileIteratorLambdaIamRole
        )
        reconcileIteratorLambdaIamPolicyStatementWriteLogs = iam.PolicyStatement(
            actions=[
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            effect=iam.Effect('ALLOW'),
            resources=[reconcileIteratorLambda.log_group.log_group_arn]           
        )
        reconcileIteratorLambdaIamPolicy = iam.Policy(
            self,
            "reconcileIteratorLambdaIamPolicy",
            statements=[
                reconcileIteratorLambdaIamPolicyStatementWriteLogs
            ],
            roles=[reconcileIteratorLambdaIamRole]
        )

        # AWS Lambda function used by the Step Functions "reconcile file uploads" state machine that 
        # reconciles data between Amazon S3 and Amazon DynamoDB. Created with required IAM policy 
        # and role
        reconcileCheckLambdaIamRole = iam.Role(
            self,
            "reconcileCheckLambdaIamRole",
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com')            
        )
        reconcileCheckLambdaIamPolicy = iam.Policy(
            self,
            "reconcileCheckLambdaIamPolicy",
            roles=[reconcileCheckLambdaIamRole]
        )
        reconcileCheckLambda = _lambda.Function(
            self,
            "reconcileCheckLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.asset("lambda-code"),
            handler='reconcile-check.lambda_handler',
            environment={
                "dynamoDbTableName": fileUploadEventTable.table_name
            },
            role=reconcileCheckLambdaIamRole
        )
        reconcileCheckLambdaIamPolicyStatementDdb = iam.PolicyStatement(
            actions=[
                "dynamodb:Query"
            ],
            effect=iam.Effect('ALLOW'),
            resources=[
                fileUploadEventTable.table_arn
            ]            
        )
        reconcileCheckLambdaIamPolicyStatementS3 = iam.PolicyStatement(
            actions=[
                "s3:GetObject"
            ],
            effect=iam.Effect('ALLOW'),
            resources=[
                fileUploadBucket.bucket_arn + "/*"
            ]                 
        )
        reconcileCheckLambdaIamPolicyStatementWriteLogs = iam.PolicyStatement(
            actions=[
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            effect=iam.Effect('ALLOW'),
            resources=[reconcileCheckLambda.log_group.log_group_arn]   
        )
        reconcileCheckLambdaIamPolicy.add_statements(reconcileCheckLambdaIamPolicyStatementDdb)
        reconcileCheckLambdaIamPolicy.add_statements(reconcileCheckLambdaIamPolicyStatementS3)
        reconcileCheckLambdaIamPolicy.add_statements(reconcileCheckLambdaIamPolicyStatementWriteLogs)

        # AWS Lambda function used by the Step Functions "reconcile file uploads" state machine that 
        # notifies on the status of the reconciliation process (timeout or successful). Created 
        # with required IAM policy and role
        reconcileNotifyLambdaIamRole = iam.Role(
            self,
            "reconcileNotifyLambdaIamRole",
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com')
        )
        reconcileNotifyLambdaIamPolicy = iam.Policy(
            self,
            "reconcileNotifyLambdaIamPolicy",
            statements=[
                customEventBusIamPolicyStatement
            ],
            roles=[reconcileNotifyLambdaIamRole]
        )
        reconcileNotifyLambda = _lambda.Function(
            self,
            "reconcileNotifyLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.asset("lambda-code"),
            handler='reconcile-notify.lambda_handler',
            environment={
                "eventBusName": customEventBus.event_bus_name                
            },
            role=reconcileNotifyLambdaIamRole            
        )
        reconcileNotifyLambdaIamPolicyStatementWriteLogs = iam.PolicyStatement(
            actions=[
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            effect=iam.Effect('ALLOW'),
            resources=[reconcileNotifyLambda.log_group.log_group_arn]
        )
        reconcileNotifyLambdaIamPolicy.add_statements(reconcileNotifyLambdaIamPolicyStatementWriteLogs)

        # "Reconcile file uploads" Step Functions state machine
        passObjectState = {
            "count": int(self.node.try_get_context("reconcileCountIterations")),
            "ticker": 0
        }
        configureCountState = sfn.Pass(
            self,
            "configureCountState",
            result=sfn.Result.from_object(passObjectState),
            result_path="$.iterator.Payload"
        )
        iteratorState = tasks.LambdaInvoke(
            self,
            "iteratorState",
            lambda_function=reconcileIteratorLambda,
            result_path="$.iterator"
        )
        reconcileCheckState = tasks.LambdaInvoke(
            self,
            "reconcileCheckState",
            lambda_function=reconcileCheckLambda,
            result_path="$.reconcilecheck"
        )
        reconcileNotifyState = tasks.LambdaInvoke(
            self,
            "reconcileNotifyState",
            lambda_function=reconcileNotifyLambda
        )
        isCountReachedState = sfn.Choice(
            self,
            "isCountReachedState"
        )
        isReconcileCompleteState = sfn.Choice(
            self,
            "isReconcileCompleteState"
        )
        waitBetweenIterationsState = sfn.Wait(
            self,
            "waitBetweenIterationsState",
            time=sfn.WaitTime.duration(core.Duration.seconds(int(self.node.try_get_context("reconcileWaitIterations"))))
        )
        doneState = sfn.Pass(
            self,
            "doneState"
        )
        reconcileStateMachineDefinition = configureCountState \
            .next(iteratorState) \
            .next(isCountReachedState
                .when(sfn.Condition.boolean_equals("$.iterator.Payload.continue",True), reconcileCheckState \
                    .next(isReconcileCompleteState \
                        .when(sfn.Condition.boolean_equals("$.reconcilecheck.Payload.reconcileDone", True), reconcileNotifyState.next(doneState)) \
                        .otherwise(waitBetweenIterationsState \
                            .next(iteratorState)))) \
                .otherwise(reconcileNotifyState))
        reconcileStateMachine = sfn.StateMachine(
            self,
            "reconcileStateMachine",
            definition=reconcileStateMachineDefinition
        )
        
        # Add Step Functions "reconcile file uploads" state machine as another target for the 
        # "manifest" file upload Amazon EventBridge rule
        manifestFileUploadEventRule.add_target(targets.SfnStateMachine(reconcileStateMachine))

        # Amazon CloudWatch log groups for the notification events generated by the "reconcile file 
        # uploads" Step Functions state machine
        reconcileNotifySuccessfulLogGroup = logs.LogGroup(
            self,
            "reconcileNotifySuccessfulLogGroup",
            removal_policy=core.RemovalPolicy.DESTROY
        )
        reconcileNotifyTimeoutLogGroup = logs.LogGroup(
            self,
            "reconcileNotifyTimeoutLogGroup",
            removal_policy=core.RemovalPolicy.DESTROY
        )

        # Amazon EventBridge rules for the custom event bus to route reconciliation notification 
        # events generated by the "reconcile file uploads" Step Functions state machine to the 
        # relevant targets - Amazon CloudWatch log groups
        reconcileNotifySuccessfulEventPattern = events.EventPattern(
            source=["vault.application"],
            detail_type=["File Upload Reconciliation Successful"]
        )
        reconcileNotifySuccessfulEventRule = events.Rule(
            self,
            "reconcileNotifySuccessfulEventRule",
            event_bus=customEventBus,
            event_pattern=reconcileNotifySuccessfulEventPattern
        )
        reconcileNotifyTimeoutEventPattern = events.EventPattern(
            source=["vault.application"],
            detail_type=["File Upload Reconciliation Timeout"]
        )
        reconcileNotifyTimeoutEventRule = events.Rule(
            self,
            "reconcileNotifyTimeoutEventRule",
            event_bus=customEventBus,
            event_pattern=reconcileNotifyTimeoutEventPattern
        )
        reconcileNotifySuccessfulEventRule.add_target(targets.CloudWatchLogGroup(reconcileNotifySuccessfulLogGroup))
        reconcileNotifyTimeoutEventRule.add_target(targets.CloudWatchLogGroup(reconcileNotifyTimeoutLogGroup))

        # Stack CloudFormation output providing the file upload Amazon S3 bucket name
        fileUploadBucketName = core.CfnOutput(
            self,
            "fileUploadBucketName",
            value=fileUploadBucket.bucket_name,
            description="Use this Amazon S3 bucket name when creating \
            a File Gateway file share. Empty this bucket before destroying \
            this stack."
        )

        # Create SSM parameters for the Amazon S3 bucket storing file uploads from AWS
        # Storage Gateway
        fileUploadBucketNameSsmParm = ssm.StringParameter(
            self,
            "fileUploadBucketNameSsmParm",
            string_value=fileUploadBucket.bucket_name,
            parameter_name="fileUploadBucketName"
        )
        self.fileUploadBucketNameSsmParm = fileUploadBucketNameSsmParm
        