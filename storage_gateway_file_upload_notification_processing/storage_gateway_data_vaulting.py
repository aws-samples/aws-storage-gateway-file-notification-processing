#===================================================================================
# FILE: storage_gateway_data_vaulting.py
#
# DESCRIPTION: Stack definition for a simple VPC with two EC2 instances - a Storage
# Gateway (File Gateway) and a File Gateway client. Created to demonstrate an example
# data vaulting operation and corresponding File Gateway file upload notification 
# processing.
#
# NOTES: Part of an AWS CDK application. View the README.md file in this repository 
# for further information on the application architecture. 
#===================================================================================

from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_ssm as ssm
)

class DataVaulting(core.Stack):
    def __init__(self, scope: core.Construct, construct_id: str, fileUploadBucket, fileUploadBucketNameSsmParm, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Define AWS account ID and region
        accountId = core.Aws.ACCOUNT_ID
        regionName = core.Aws.REGION

        # Create the VPC with x3 subnets, all Isolated (Private with no route to a
        #  NAT GW). Single-AZ
        dataVaultingVpc = ec2.Vpc(
            self,
            "dataVaultingVpc",
            cidr="192.168.0.0/16",
            max_azs=1,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="dataVaultingSgwFileGatewayClientInstanceSubnet",
                    cidr_mask=24,
                    subnet_type=ec2.SubnetType.ISOLATED
                ),
                ec2.SubnetConfiguration(
                    name="dataVaultingSgwFileGatewayInstanceSubnet",
                    cidr_mask=24,
                    subnet_type=ec2.SubnetType.ISOLATED
                ),
                ec2.SubnetConfiguration(
                    name="dataVaultingVpcEndpointSubnet",
                    cidr_mask=24,
                    subnet_type=ec2.SubnetType.ISOLATED
                )
            ]
        )

        # Create Security Groups for the VPC Endpoints - Storage Gateway VPC Endpoint
        # requires a number of additional ports, hence has a dedicated Security Group
        dataVaultingVpcEndpointsSecurityGroup = ec2.SecurityGroup(
            self,
            "dataVaultingVpcEndpointsSecurityGroup",
            security_group_name="VPC Endpoints - allow port 443 from VPC CIDR",
            vpc=dataVaultingVpc
        )
        dataVaultingSgwVpcEndpointSecurityGroup = ec2.SecurityGroup(
            self,
            "dataVaultingSgwVpcEndpointSecurityGroup",
            security_group_name="Storage Gateway VPC endpoint - allow required ports from File Gateway subnet",
            vpc=dataVaultingVpc
        )
        dataVaultingSgwVpcEndpointPorts = [1026, 1027, 1028, 1031, 2222]
        for x in dataVaultingSgwVpcEndpointPorts:
            dataVaultingSgwVpcEndpointSecurityGroup.add_ingress_rule(ec2.Peer.ipv4('192.168.1.0/24'),ec2.Port.tcp(x))
        
        # Create Security Groups for each of the EC2 instances - File Gateway client and
        # File Gateway. The former has no inbound rules, the latter only Ports 80 and
        # 2049 from the File Gateway client
        sgwFileGatewayClientSecurityGroup = ec2.SecurityGroup(
            self,
            "sgwFileGatewayClientSecurityGroup",
            security_group_name="File Gateway Client Security Group",
            vpc=dataVaultingVpc
        )
        sgwFileGatewaySecurityGroup = ec2.SecurityGroup(
            self,
            "sgwFileGatewaySecurityGroup",
            security_group_name="File Gateway Security Group",
            vpc=dataVaultingVpc
        )
        sgwFileGatewaySecurityGroup.add_ingress_rule(
            sgwFileGatewayClientSecurityGroup,
            ec2.Port.tcp(80),
            'Allow getting activation key from File Gateway client'
        )
        sgwFileGatewaySecurityGroup.add_ingress_rule(
            sgwFileGatewayClientSecurityGroup,
            ec2.Port.tcp(2049),
            'Allow NFS from File Gateway client'
        )

        # Create the VPC Endpoints - a Gateway Endpoint for S3 and Interface Endpoints
        # for SSM, EC2 and Storage Gateway. Place Interface Endpoints a dedicated subnet
        dataVaultingS3GatewayEndpoint = ec2.GatewayVpcEndpoint(
            self,
            "dataVaultingS3GatewayEndpoint",
            vpc=dataVaultingVpc,
            service=ec2.GatewayVpcEndpointAwsService.S3
        )
        dataVaultingSgwInterfaceEndpoint = ec2.InterfaceVpcEndpoint(
            self,
            "dataVaultingSgwInterfaceEndpoint",
            vpc=dataVaultingVpc,
            subnets=ec2.SubnetSelection(subnet_group_name='dataVaultingVpcEndpointSubnet'),
            security_groups=[dataVaultingSgwVpcEndpointSecurityGroup],
            service=ec2.InterfaceVpcEndpointAwsService.STORAGE_GATEWAY,
            private_dns_enabled=True
        )
        dataVaultingSsmInterfaceEndpoint = ec2.InterfaceVpcEndpoint(
            self,
            "dataVaultingSsmInterfaceEndpoint",
            vpc=dataVaultingVpc,
            subnets=ec2.SubnetSelection(subnet_group_name='dataVaultingVpcEndpointSubnet'),
            security_groups=[dataVaultingVpcEndpointsSecurityGroup],
            service=ec2.InterfaceVpcEndpointAwsService.SSM,
            private_dns_enabled=True
        )
        dataVaultingEc2InterfaceEndpoint = ec2.InterfaceVpcEndpoint(
            self,
            "dataVaultingEc2InterfaceEndpoint",
            vpc=dataVaultingVpc,
            subnets=ec2.SubnetSelection(subnet_group_name='dataVaultingVpcEndpointSubnet'),
            security_groups=[dataVaultingVpcEndpointsSecurityGroup],
            service=ec2.InterfaceVpcEndpointAwsService.EC2,
            private_dns_enabled=True
        )
        dataVaultingSsmMessagesInterfaceEndpoint = ec2.InterfaceVpcEndpoint(
            self,
            "dataVaultingSsmMessagesInterfaceEndpoint",
            vpc=dataVaultingVpc,
            subnets=ec2.SubnetSelection(subnet_group_name='dataVaultingVpcEndpointSubnet'),
            security_groups=[dataVaultingVpcEndpointsSecurityGroup],
            service=ec2.InterfaceVpcEndpointAwsService.SSM_MESSAGES,
            private_dns_enabled=True
        )
        dataVaultingEc2MessagesInterfaceEndpoint = ec2.InterfaceVpcEndpoint(
            self,
            "dataVaultingEc2MessagesInterfaceEndpoint",
            vpc=dataVaultingVpc,
            subnets=ec2.SubnetSelection(subnet_group_name='dataVaultingVpcEndpointSubnet'),
            security_groups=[dataVaultingVpcEndpointsSecurityGroup],
            service=ec2.InterfaceVpcEndpointAwsService.EC2_MESSAGES,
            private_dns_enabled=True
        )

        # Create Amazon S3 bucket to hold CDK application scripts and define for deployment
        cdkAppScriptsBucket = s3.Bucket(
            self,
            "cdkAppScriptsBucket",
            removal_policy=core.RemovalPolicy.DESTROY
        )
        cdkAppScriptsBucketDeployment = s3_deployment.BucketDeployment(
            self,
            "cdkAppScriptsBucketDeployment",
            destination_bucket=cdkAppScriptsBucket,
            sources=[
                s3_deployment.Source.asset('example-scripts')
            ]
        )

        # Create SSM parameters for the Storage Gateway VPC Endpoint ID and the Amazon S3 bucket
        # containing the CDK application scripts
        dataVaultingSgwInterfaceEndpointIdSsmParm = ssm.StringParameter(
            self,
            "dataVaultingSgwInterfaceEndpointIdSsmParm",
            string_value=dataVaultingSgwInterfaceEndpoint.vpc_endpoint_id,
            parameter_name="dataVaultingStackVpcEndpointId"
        )
        cdkAppScriptsBucketNameSsmParm = ssm.StringParameter(
            self,
            "cdkAppScriptsBucketSsmParm",
            string_value=cdkAppScriptsBucket.bucket_name,
            parameter_name="cdkApplicationScriptsBucketName"
        )

        # Create an IO1 EBS block device type that will be used by both the File Gateway
        # and File Gateway client
        ebsBlockDeviceVolume = ec2.BlockDeviceVolume.ebs(
            volume_size=150,
            delete_on_termination=True,
            iops=2000,
            volume_type=ec2.EbsDeviceVolumeType.IO1
        )

        # File Gateway client EC2 instance is built from the latest Amazon Linux 2 AMI.
        # Mount an EBS volume on the instance, created from the EBS block device volume
        # configuration already defined above
        sgwFileGatewayClientAmi = ec2.MachineImage.latest_amazon_linux(
            generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
            edition=ec2.AmazonLinuxEdition.STANDARD,
            virtualization=ec2.AmazonLinuxVirt.HVM,
            storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE
        )
        sgwFileGatewayClientEbsBlockDevice = ec2.BlockDevice(
            device_name="/dev/sdf",
            volume=ebsBlockDeviceVolume
        )

        # IAM role for the File Gateway client - permissions for SSM API (to provide 
        # shell terminal/console access), Storage Gateway API (to activate the File
        # Gateway from inside the VPC) and EC2 API (to describe VPC Endpoints)
        sgwFileGatewayClientIamRole = iam.Role(
            self,
            "sgwFileGatewayClientIamRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com")
        )
        sgwFileGatewayClientIamRole.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEC2RoleforSSM"))
        sgwFileGatewayClientIamPolicyStatementStorageGateway = iam.PolicyStatement(
            actions=[
                "storagegateway:ActivateGateway",
                "storagegateway:DeleteGateway"
            ],
            effect=iam.Effect('ALLOW'),
            resources=["*"]
        )
        sgwFileGatewayClientIamPolicyStatementVpc = iam.PolicyStatement(
            actions=[
                "ec2:DescribeVpcEndpoints"
            ],
            effect=iam.Effect('ALLOW'),
            resources=["*"]
        )
        sgwFileGatewayClientIamPolicyStatementS3 = iam.PolicyStatement(
            actions=[
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            effect=iam.Effect('ALLOW'),
            resources=[
                cdkAppScriptsBucket.bucket_arn + "/*",
                fileUploadBucket.bucket_arn + "/*"
            ]
        )
        sgwFileGatewayClientIamPolicyStatementSsm = iam.PolicyStatement(
            actions=[
                "ssm:GetParameter"
            ],
            effect=iam.Effect('ALLOW'),
            resources=[
                dataVaultingSgwInterfaceEndpointIdSsmParm.parameter_arn,
                cdkAppScriptsBucketNameSsmParm.parameter_arn,
                fileUploadBucketNameSsmParm.parameter_arn
            ]
        )
        sgwFileGateClientIamPolicy = iam.Policy(
            self,
            "sgwFileGateClientIamPolicy",
            statements=[
                sgwFileGatewayClientIamPolicyStatementStorageGateway,
                sgwFileGatewayClientIamPolicyStatementVpc,
                sgwFileGatewayClientIamPolicyStatementS3,
                sgwFileGatewayClientIamPolicyStatementSsm
            ],
            roles=[sgwFileGatewayClientIamRole]
        )

        # File Gateway client user data - setup and downloads required for the CDK
        # application walkthrough/demonstration
        sgwFileGatewayClientUserData = ec2.UserData.for_linux()
        sgwFileGatewayClientUserData.add_commands('mkfs -t xfs /dev/sdf;mkdir /mnt/sourcedata; \
            mount -t xfs /dev/sdf /mnt/sourcedata; \
            echo "PS1=\`whoami\`\\@\\"FileGatewayClient>$ \\"" >> /etc/bashrc;mkdir /mnt/vaultdata; \
            mkdir /var/local/cdkapp-scripts;cd /var/local/cdkapp-scripts; \
            aws s3 cp s3://' + cdkAppScriptsBucket.bucket_name + ' . --recursive --region ' + regionName + '; \
            chmod -R 777 /var/local/cdkapp-scripts')

        # Create the File Gateway client EC2 instance
        sgwFileGatewayClientInstance = ec2.Instance(
            self,
            "sgwFileGatewayClientInstance",
            instance_type=ec2.InstanceType("c5.4xlarge"),
            instance_name="CDK App - File Gateway Client",
            machine_image=sgwFileGatewayClientAmi,
            vpc=dataVaultingVpc,
            vpc_subnets=ec2.SubnetSelection(subnet_group_name='dataVaultingSgwFileGatewayClientInstanceSubnet'),
            security_group=sgwFileGatewayClientSecurityGroup,
            private_ip_address="192.168.0.10",
            block_devices=[sgwFileGatewayClientEbsBlockDevice],
            role=sgwFileGatewayClientIamRole,
            user_data=sgwFileGatewayClientUserData
        )

        # File Gateway EC2 instance is built from the latest Storage Gateway AMI
        # Mount an EBS volume on the instance, created from the EBS block device volume
        # configuration already defined above     
        sgwFileGatewayAmi = ec2.MachineImage.lookup(
            name="aws-storage-gateway*"
        )
        sgwFileGatewayEbsBlockDevice = ec2.BlockDevice(
            device_name="/dev/sdf",
            volume=ebsBlockDeviceVolume
        )

        # Create the File Gateway EC2 instance
        sgwFileGatewayInstance = ec2.Instance(
            self,
            "sgwFileGatewayInstance",
            instance_type=ec2.InstanceType("c5.4xlarge"),
            instance_name="CDK App - File Gateway",
            machine_image=sgwFileGatewayAmi,
            vpc=dataVaultingVpc,
            vpc_subnets=ec2.SubnetSelection(subnet_group_name='dataVaultingSgwFileGatewayInstanceSubnet'),
            security_group=sgwFileGatewaySecurityGroup,
            private_ip_address="192.168.1.10",
            block_devices=[sgwFileGatewayEbsBlockDevice]
        )
        
        # Stack CloudFormation output providing CDK application scripts S3 bucket name
        cdkAppScriptsBucketCfnOutput = core.CfnOutput(
            self,
            "cdkAppScriptsBucketCfnOutput",
            value=cdkAppScriptsBucket.bucket_name,
            description="Bucket containing the CDK application scripts required for \
            the workshop in the CDK repository. Empty this bucket \
            before destroying this stack."
        )