#!/usr/bin/env python3

import boto3
import json
from botocore.exceptions import ClientError
import argparse
import concurrent.futures
import os
import importlib.util
import time
# Load service-specific collectors
SERVICE_COLLECTORS = {}

# Default region for global services
default_region = 'us-east-1'

# Define global services that should only be queried once
global_services = ['iam', 's3', 'route53', 'cloudfront', 'organizations',
                  'waf', 'shield', 'budgets', 'ce', 'chatbot', 'health']

# Import service mappings from separate module
def import_service_mappings():
    """Import service mappings from service_mappings.py"""
    if verbose:
        print(f"DEBUG: import service mappings")

    from service_mappings import SERVICE_MAPPINGS
    return SERVICE_MAPPINGS

def get_all_regions():
    """Get all available AWS regions."""
    ec2_client = boto3.client('ec2', region_name=default_region)  # Specify a default region
    regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
    return regions

def get_account_id():
    """Get the current AWS account ID."""
    try:
        sts_client = boto3.client('sts', region_name=default_region)  # Specify the region explicitly
        return sts_client.get_caller_identity()["Account"]
    except ClientError as e:
        if 'ExpiredToken' in str(e) or 'InvalidClientTokenId' in str(e) or 'AccessDenied' in str(e):
            print("Error: AWS authentication failed. Please check your credentials and try again.")
            print("Make sure you have valid AWS credentials configured via AWS CLI, environment variables, or IAM role.")
            print(f"Specific error: {str(e)}")
            exit(1)
        else:
            print(f"Unexpected error when authenticating: {str(e)}")
            exit(1)

# Generic service resource collection function
def get_service_resources(client, service_name, region, account_id, verbose=False):
    """Get resources for a specific service using appropriate API calls."""
    resources = []

    # Dictionary mapping services to their list/describe methods and ARN formats
    service_mappings = import_service_mappings()

    # Check if we have a mapping for this service
    if service_name in service_mappings:
        mapping = service_mappings[service_name]
        
        # Skip if this is a global service and we're not in the default region
        if service_name in global_services and region != default_region:
            return resources

        if verbose:
            print(f"DEBUG: Processing {service_name} in {region} using method {mapping['method']}")
            start_time = time.time()
        method_name = mapping['method']
        response_key = mapping['key']

        try:
            # Get the method from the client
            method = getattr(client, method_name)

            # Call the method (with minimal parameters)
            if service_name == 'ce':
                # Special handling for Cost Explorer which requires time range
                from datetime import datetime, timedelta
                end = datetime.now()
                start = end - timedelta(days=30)
                response = method(
                    TimePeriod={
                        'Start': start.strftime('%Y-%m-%d'),
                        'End': end.strftime('%Y-%m-%d')
                    },
                    Granularity='MONTHLY',
                    Metrics=['UnblendedCost']
                )
            elif service_name == 'cloudwatch':
                # Just get a sample of metrics
                response = method(Namespace='AWS/EC2')
            elif service_name == 'health':
                # Health service requires filter
                response = method(filter={})
            elif service_name == 'textract':
                if verbose:
                    print(f"DEBUG: Skipping textract as it requires a document ID")
                # Textract requires a document ID which we don't have
                return []
            else:
                if verbose:
                    print(f"DEBUG: Calling {method_name} for {service_name} in {region}")
                    call_start = time.time()
                # Standard method call
                response = method()

            # Extract resources based on the mapping
            if 'direct_arn' in mapping and mapping['direct_arn']:
                # The response itself is the ARN
                if response_key in response:
                    if verbose:
                        print(f"DEBUG: Found direct ARN for {service_name}")

                    resources.append(response[response_key])
            else:
                # Navigate to the correct response key, handling nested keys with dots
                items = response
                for key_part in response_key.split('.'):
                    if key_part in items:
                        items = items[key_part]
                    else:
                        items = []
                        break

                # Process the items
                if 'id_list' in mapping and mapping['id_list']:
                    # Response is a list of IDs
                    if verbose:
                        print(f"DEBUG: Processing ID list with {len(items)} items for {service_name}")
                    for item_id in items:
                        arn = mapping['arn_format'].format(
                            region=region,
                            account_id=account_id,
                            id=item_id
                        )
                        resources.append(arn)
                elif 'arn_list' in mapping and mapping['arn_list']:
                    # Response is a list of ARNs
                    if verbose:
                        print(f"DEBUG: Processing ARN list with {len(items)} items for {service_name}")
                    resources.extend(items)
                else:
                    # Response is a list of objects
                    if verbose:
                        print(f"DEBUG: Processing object list with {len(items)} items for {service_name}")
                    for item in items:
                        if 'arn_attr' in mapping:
                            # Extract ARN directly from the item
                            if mapping['arn_attr'] in item:
                                resources.append(item[mapping['arn_attr']])
                        elif 'id_attr' in mapping and 'arn_format' in mapping:
                            # Construct ARN from ID and format
                            if mapping['id_attr'] in item:
                                item_id = item[mapping['id_attr']]
                                arn = mapping['arn_format'].format(
                                    region=region,
                                    account_id=account_id,
                                    id=item_id
                                )
                                resources.append(arn)

            if verbose:
                elapsed = time.time() - start_time
                print(f"DEBUG: Completed {service_name} in {region} in {elapsed:.2f}s, found {len(resources)} resources")


        except Exception as e:
            # Just log the error and continue
            print(f"Error getting resources for {service_name} in {region}: {str(e)}")
            if verbose:
                print(f"DEBUG: Exception details: {type(e).__name__}")

    return resources

# Import service-specific collection modules
def import_service_collectors(verbose=False):
    """Import service-specific collector functions from the services directory"""
    collectors = {}
    services_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'services')

    # Create services directory if it doesn't exist
    if not os.path.exists(services_dir):
        os.makedirs(services_dir)
        # Create __init__.py to make it a proper package
        with open(os.path.join(services_dir, '__init__.py'), 'w') as f:
            f.write('# AWS Service collectors package\n')

    # Look for all Python files in the services directory
    for filename in os.listdir(services_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            
            module_name = filename[:-3]  # Remove .py extension
            module_path = os.path.join(services_dir, filename)

            # Import the module
            spec = importlib.util.spec_from_file_location(f"services.{module_name}", module_path)
            if spec and spec.loader:
                if verbose:
                    print(f"DEBUG: importing module {filename}")
                    
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Check if the module has a collect_resources function
                if hasattr(module, 'collect_resources'):
                    collectors[module_name] = module.collect_resources

    return collectors

# Service collector dispatcher
def collect_service_resources(service_name, region, account_id, resource_arns, verbose=False):
    """Dispatch to the appropriate service collector function"""
    # Skip if this is a global service and we're not in the default region
    if service_name in global_services and region != default_region:
        return

    # Create a boto3 client for the service in the specified region
    client = boto3.client(service_name, region_name=region)

    # Use service-specific collector if available
    if service_name in SERVICE_COLLECTORS:
        SERVICE_COLLECTORS[service_name](client, region, account_id, resource_arns, verbose)
    else:
        # Use the generic service resource collector for other services
        resources = get_service_resources(client, service_name, region, account_id, verbose)
        resource_arns.extend(resources)

def collect_resources_for_service(service_name, region, account_id, resource_arns, verbose=False):
    """Collect resources for a specific service in a region."""
    try:
        # Skip if this is a global service and we're not in the default region
        if service_name in global_services and region != default_region:
            return

        # Use the service collector dispatcher
        collect_service_resources(service_name, region, account_id, resource_arns, verbose)
        return

        # # The code below is kept for reference but will not be executed
        # # as we're now using the service collector dispatcher

        # # Create a boto3 client for the service in the specified region
        # client = boto3.client(service_name, region_name=region)

        # # Different services have different list/describe methods
        # if service_name == 'ec2':
        #     if verbose:
        #         print(f"DEBUG: Starting EC2 resource collection in {region}")
        #         start_time = time.time()

        #     # EC2 instances
        #     response = client.describe_instances()
        #     for reservation in response.get('Reservations', []):
        #         for instance in reservation.get('Instances', []):
        #             instance_id = instance['InstanceId']
        #             arn = f"arn:aws:ec2:{region}:{account_id}:instance/{instance_id}"
        #             resource_arns.append(arn)

        #     if verbose:
        #         print(f"DEBUG: Collected EC2 instances in {region}, now collecting volumes")

        #     # EC2 volumes
        #     response = client.describe_volumes()
        #     for volume in response.get('Volumes', []):
        #         volume_id = volume['VolumeId']
        #         arn = f"arn:aws:ec2:{region}:{account_id}:volume/{volume_id}"
        #         resource_arns.append(arn)

        #     if verbose:
        #         print(f"DEBUG: Collected EC2 volumes in {region}, now collecting security groups")

        #     # EC2 security groups
        #     response = client.describe_security_groups()
        #     for sg in response.get('SecurityGroups', []):
        #         sg_id = sg['GroupId']
        #         arn = f"arn:aws:ec2:{region}:{account_id}:security-group/{sg_id}"
        #         resource_arns.append(arn)

        #     if verbose:
        #         print(f"DEBUG: Collected EC2 security groups in {region}, now collecting Elastic IPs")

        #     # EC2 Elastic IP Addresses
        #     response = client.describe_addresses()
        #     for eip in response.get('Addresses', []):
        #         allocation_id = eip.get('AllocationId')
        #         if allocation_id:
        #             arn = f"arn:aws:ec2:{region}:{account_id}:elastic-ip/{allocation_id}"
        #             resource_arns.append(arn)

        #     if verbose:
        #         print(f"DEBUG: Collected EC2 Elastic IPs in {region}, now collecting VPCs")

        #     # EC2 VPC resources
        #     # VPCs
        #     response = client.describe_vpcs()
        #     for vpc in response.get('Vpcs', []):
        #         vpc_id = vpc['VpcId']
        #         arn = f"arn:aws:ec2:{region}:{account_id}:vpc/{vpc_id}"
        #         resource_arns.append(arn)

        #     if verbose:
        #         print(f"DEBUG: Collected EC2 VPCs in {region}, now collecting subnets")

        #     # Subnets
        #     response = client.describe_subnets()
        #     for subnet in response.get('Subnets', []):
        #         subnet_id = subnet['SubnetId']
        #         arn = f"arn:aws:ec2:{region}:{account_id}:subnet/{subnet_id}"
        #         resource_arns.append(arn)

        #     if verbose:
        #         print(f"DEBUG: Collected EC2 subnets in {region}, now collecting route tables")

        #     # Route Tables
        #     response = client.describe_route_tables()
        #     for rt in response.get('RouteTables', []):
        #         rt_id = rt['RouteTableId']
        #         arn = f"arn:aws:ec2:{region}:{account_id}:route-table/{rt_id}"
        #         resource_arns.append(arn)

        #     if verbose:
        #         print(f"DEBUG: Collected EC2 route tables in {region}, now collecting NACLs")

        #     # Network ACLs
        #     response = client.describe_network_acls()
        #     for nacl in response.get('NetworkAcls', []):
        #         nacl_id = nacl['NetworkAclId']
        #         arn = f"arn:aws:ec2:{region}:{account_id}:network-acl/{nacl_id}"
        #         resource_arns.append(arn)

        #     if verbose:
        #         print(f"DEBUG: Collected EC2 NACLs in {region}, now collecting internet gateways")

        #     # Internet Gateways
        #     response = client.describe_internet_gateways()
        #     for igw in response.get('InternetGateways', []):
        #         igw_id = igw['InternetGatewayId']
        #         arn = f"arn:aws:ec2:{region}:{account_id}:internet-gateway/{igw_id}"
        #         resource_arns.append(arn)

        #     if verbose:
        #         print(f"DEBUG: Collected EC2 internet gateways in {region}, now collecting NAT gateways")

        #     # NAT Gateways
        #     response = client.describe_nat_gateways()
        #     for nat in response.get('NatGateways', []):
        #         nat_id = nat['NatGatewayId']
        #         arn = f"arn:aws:ec2:{region}:{account_id}:nat-gateway/{nat_id}"
        #         resource_arns.append(arn)

        #     if verbose:
        #         print(f"DEBUG: Collected EC2 NAT gateways in {region}, now collecting network interfaces")

        #     # Elastic Network Interfaces
        #     response = client.describe_network_interfaces()
        #     for eni in response.get('NetworkInterfaces', []):
        #         eni_id = eni['NetworkInterfaceId']
        #         arn = f"arn:aws:ec2:{region}:{account_id}:network-interface/{eni_id}"
        #         resource_arns.append(arn)

        #     if verbose:
        #         print(f"DEBUG: Collected EC2 network interfaces in {region}, now collecting transit gateways")

        #     # Transit Gateways
        #     try:
        #         response = client.describe_transit_gateways()
        #         for tgw in response.get('TransitGateways', []):
        #             arn = tgw.get('TransitGatewayArn')
        #             if arn:
        #                 resource_arns.append(arn)
        #     except Exception as e:
        #         if verbose:
        #             print(f"DEBUG: Error getting transit gateways in {region}: {str(e)}")
        #         else:
        #             print(f"Error getting transit gateways: {str(e)}")

        #     if verbose:
        #         elapsed = time.time() - start_time
        #         print(f"DEBUG: Completed EC2 resource collection in {region} in {elapsed:.2f}s")

        # elif service_name == 's3':
        #     # S3 buckets (global service but listing here)
        #     response = client.list_buckets()
        #     bucket_count = len(response.get('Buckets', []))
        #     for bucket in response.get('Buckets', []):
        #         bucket_name = bucket['Name']
        #         arn = f"arn:aws:s3:::{bucket_name}"
        #         resource_arns.append(arn)

        #         # List objects in buckets (with pagination)
        #         try:
        #             if verbose:
        #                 print(f"DEBUG: Getting location for bucket {bucket_name}")
        #             # Only list objects in buckets that are in the current region or global
        #             bucket_region = client.get_bucket_location(Bucket=bucket_name)
        #             location_constraint = bucket_region.get('LocationConstraint', '')

        #             # Handle the special case where None means us-east-1
        #             if location_constraint is None:
        #                 location_constraint = 'us-east-1'

        #             if location_constraint == region or location_constraint == '':
        #                 if verbose:
        #                     print(f"DEBUG: Listing objects in bucket {bucket_name} (region: {location_constraint})")
        #                 # Only list top-level objects to avoid excessive API calls
        #                 paginator = client.get_paginator('list_objects_v2')
        #                 for page in paginator.paginate(Bucket=bucket_name, MaxKeys=100, Delimiter='/'):
        #                     for obj in page.get('Contents', []):
        #                         arn = f"arn:aws:s3:::{bucket_name}/{obj['Key']}"
        #                         resource_arns.append(arn)
        #         except Exception as e:
        #             if verbose:
        #                 print(f"DEBUG: Error listing objects in bucket {bucket_name}: {str(e)}")
        #             else:
        #                 print(f"Error listing objects in bucket {bucket_name}: {str(e)}")

        #     if verbose:
        #         print(f"DEBUG: Processed {bucket_count} S3 buckets")

        # elif service_name == 'iam':
        #     # IAM roles (global service)
        #     if region == default_region:  # Only check in one region to avoid duplicates
        #         response = client.list_roles()
        #         for role in response.get('Roles', []):
        #             arn = role['Arn']
        #             resource_arns.append(arn)

        #         # IAM users
        #         response = client.list_users()
        #         for user in response.get('Users', []):
        #             arn = user['Arn']
        #             resource_arns.append(arn)

        #         if verbose:
        #             print(f"DEBUG: Collected IAM roles and users, now collecting policies")

        #         # IAM policies
        #         response = client.list_policies(Scope='Local')
        #         for policy in response.get('Policies', []):
        #             arn = policy['Arn']
        #             resource_arns.append(arn)

        #         # IAM groups
        #         response = client.list_groups()
        #         for group in response.get('Groups', []):
        #             arn = group['Arn']
        #             resource_arns.append(arn)

        #         if verbose:
        #             print(f"DEBUG: Collected IAM groups, now collecting instance profiles")

        #         # IAM instance profiles
        #         response = client.list_instance_profiles()
        #         for profile in response.get('InstanceProfiles', []):
        #             arn = profile['Arn']
        #             resource_arns.append(arn)

        #         # IAM SAML providers
        #         response = client.list_saml_providers()
        #         for provider in response.get('SAMLProviderList', []):
        #             arn = provider['Arn']
        #             resource_arns.append(arn)

        #         if verbose:
        #             print(f"DEBUG: Collected IAM SAML providers, now collecting server certificates")

        #         # IAM server certificates
        #         try:
        #             response = client.list_server_certificates()
        #             for cert in response.get('ServerCertificateMetadataList', []):
        #                 arn = cert['Arn']
        #                 resource_arns.append(arn)
        #         except Exception as e:
        #             if verbose:
        #                 print(f"DEBUG: Error listing server certificates: {str(e)}")
        #             else:
        #                 print(f"Error listing server certificates: {str(e)}")

        # elif service_name == 'sqs':
        #     # SQS queues
        #     response = client.list_queues()
        #     for queue_url in response.get('QueueUrls', []):
        #         queue_attrs = client.get_queue_attributes(
        #             QueueUrl=queue_url,
        #             AttributeNames=['QueueArn']
        #         )
        #         arn = queue_attrs['Attributes']['QueueArn']
        #         resource_arns.append(arn)

        #     if verbose:
        #         print(f"DEBUG: Collected {len(response.get('QueueUrls', []))} SQS queues in {region}")

        # elif service_name == 'cloudwatch':
        #     if verbose:
        #         print(f"DEBUG: Starting CloudWatch resource collection in {region}")
        #         start_time = time.time()

        #     # CloudWatch Alarms
        #     paginator = client.get_paginator('describe_alarms')
        #     for page in paginator.paginate():
        #         for alarm in page.get('MetricAlarms', []):
        #             alarm_name = alarm['AlarmName']
        #             arn = f"arn:aws:cloudwatch:{region}:{account_id}:alarm:{alarm_name}"
        #             resource_arns.append(arn)
        #         for alarm in page.get('CompositeAlarms', []):
        #             alarm_name = alarm['AlarmName']
        #             arn = f"arn:aws:cloudwatch:{region}:{account_id}:alarm:{alarm_name}"
        #             resource_arns.append(arn)

        #     if verbose:
        #         print(f"DEBUG: Collected CloudWatch alarms in {region}, now collecting dashboards")

        #     # CloudWatch Dashboards
        #     response = client.list_dashboards()
        #     for dashboard in response.get('DashboardEntries', []):
        #         arn = dashboard['DashboardArn']
        #         resource_arns.append(arn)

        #     if verbose:
        #         elapsed = time.time() - start_time
        #         print(f"DEBUG: Completed CloudWatch resource collection in {region} in {elapsed:.2f}s")

        # elif service_name == 'logs':
        #     # CloudWatch Log Groups
        #     paginator = client.get_paginator('describe_log_groups')
        #     for page in paginator.paginate():
        #         for log_group in page.get('logGroups', []):
        #             arn = log_group.get('arn')
        #             if not arn:  # If ARN is not directly provided, construct it
        #                 log_group_name = log_group['logGroupName']
        #                 arn = f"arn:aws:logs:{region}:{account_id}:log-group:{log_group_name}"
        #             resource_arns.append(arn)

        #     if verbose:
        #         print(f"DEBUG: Collected CloudWatch Log Groups in {region}")

        #             # Note: We could also add log streams here if needed

        # elif service_name == 'route53':
        #     # Route53 is a global service, only run in the default region
        #     if region == default_region:
        #         if verbose:
        #             print(f"DEBUG: Starting Route53 resource collection")
        #             start_time = time.time()
        #         paginator = client.get_paginator('list_hosted_zones')
        #         for page in paginator.paginate():
        #             for zone in page.get('HostedZones', []):
        #                 zone_id = zone['Id']
        #                 arn = f"arn:aws:route53:::{zone_id}"
        #                 resource_arns.append(arn)

        #                 # Get record sets for each zone
        #                 try:
        #                     if verbose:
        #                         print(f"DEBUG: Getting record sets for zone {zone_id}")
        #                     # Extract the ID without the /hostedzone/ prefix
        #                     clean_zone_id = zone_id.split('/')[-1]
        #                     record_paginator = client.get_paginator('list_resource_record_sets')
        #                     for record_page in record_paginator.paginate(HostedZoneId=clean_zone_id):
        #                         for record in record_page.get('ResourceRecordSets', []):
        #                             record_name = record['Name']
        #                             record_type = record['Type']
        #                             # Route53 record ARNs don't officially exist, but we can create a pseudo-ARN
        #                             arn = f"arn:aws:route53:::{zone_id}/record/{record_name}/{record_type}"
        #                             resource_arns.append(arn)
        #                 except Exception as e:
        #                     if verbose:
        #                         print(f"DEBUG: Error getting record sets for zone {zone_id}: {str(e)}")
        #                     else:
        #                         print(f"Error getting record sets for zone {zone_id}: {str(e)}")

        #         # Get health checks
        #         paginator = client.get_paginator('list_health_checks')
        #         for page in paginator.paginate():
        #             for health_check in page.get('HealthChecks', []):
        #                 health_check_id = health_check['Id']
        #                 arn = f"arn:aws:route53:::healthcheck/{health_check_id}"
        #                 resource_arns.append(arn)

        #         if verbose:
        #             elapsed = time.time() - start_time
        #             print(f"DEBUG: Completed Route53 resource collection in {elapsed:.2f}s")

        # elif service_name == 'ecs':
        #     # ECS Clusters
        #     if verbose:
        #         print(f"DEBUG: Starting ECS resource collection in {region}")
        #         start_time = time.time()
        #     paginator = client.get_paginator('list_clusters')
        #     cluster_arns = []
        #     for page in paginator.paginate():
        #         cluster_arns.extend(page.get('clusterArns', []))

        #     for cluster_arn in cluster_arns:
        #         resource_arns.append(cluster_arn)

        #         # Get services for each cluster
        #         try:
        #             if verbose:
        #                 print(f"DEBUG: Getting services for cluster {cluster_arn}")
        #             service_paginator = client.get_paginator('list_services')
        #             for service_page in service_paginator.paginate(cluster=cluster_arn):
        #                 for service_arn in service_page.get('serviceArns', []):
        #                     resource_arns.append(service_arn)
                            
        #         except Exception as e:
        #             if verbose:
        #                 print(f"DEBUG: Error getting task definitions: {str(e)}")
        #             else:
        #                 print(f"Error getting services for cluster {cluster_arn}: {str(e)}")

        #         # Get task definitions
        #         try:
        #             task_def_paginator = client.get_paginator('list_task_definitions')
        #             for task_def_page in task_def_paginator.paginate():
        #                 for task_def_arn in task_def_page.get('taskDefinitionArns', []):
        #                     resource_arns.append(task_def_arn)
        #         except Exception as e:
        #             print(f"Error getting task definitions: {str(e)}")

        #         # Get tasks for each cluster
        #         try:
        #             task_paginator = client.get_paginator('list_tasks')
        #             for task_page in task_paginator.paginate(cluster=cluster_arn):
        #                 for task_arn in task_page.get('taskArns', []):
        #                     resource_arns.append(task_arn)
        #         except Exception as e:
        #             print(f"Error getting tasks for cluster {cluster_arn}: {str(e)}")
        #             if verbose:
        #                 print(f"DEBUG: Error getting tasks for cluster {cluster_arn}: {str(e)}")
        #             else:
        #                 print(f"Error getting tasks for cluster {cluster_arn}: {str(e)}")

        #     if verbose:
        #         elapsed = time.time() - start_time
        #         print(f"DEBUG: Completed ECS resource collection in {region} in {elapsed:.2f}s")

        # elif service_name == 'kms':
        #     # KMS Keys
        #     if verbose:
        #         print(f"DEBUG: Starting KMS resource collection in {region}")
        #     paginator = client.get_paginator('list_keys')
        #     for page in paginator.paginate():
        #         for key in page.get('Keys', []):
        #             key_id = key['KeyId']
        #             key_arn = key['KeyArn']
        #             resource_arns.append(key_arn)

        #             # Get aliases for each key
        #             try:
        #                 if verbose:
        #                     print(f"DEBUG: Getting aliases for key {key_id}")
        #                 alias_response = client.list_aliases(KeyId=key_id)
        #                 for alias in alias_response.get('Aliases', []):
        #                     alias_arn = alias['AliasArn']
        #                     resource_arns.append(alias_arn)
        #             except Exception as e:
        #                 if verbose:
        #                     print(f"DEBUG: Error getting aliases for key {key_id}: {str(e)}")
        #                 else:
        #                     print(f"Error getting aliases for key {key_id}: {str(e)}")

        #     if verbose:
        #         print(f"DEBUG: Completed KMS resource collection in {region}")

        # else:
        #     # Use the generic service resource collector for other services
        #     if verbose:
        #         print(f"DEBUG: Using generic collector for {service_name} in {region}")
        #     resources = get_service_resources(client, service_name, region, account_id, verbose)
        #     resource_arns.extend(resources)

    except ClientError as e:
        if 'AccessDenied' in str(e) or 'UnauthorizedOperation' in str(e):
            print(f"Access denied for service {service_name} in region {region}")
        elif 'OptInRequired' in str(e):
            print(f"Region {region} requires opt-in for service {service_name}")
        elif 'InvalidClientTokenId' in str(e):
            print(f"Invalid credentials for service {service_name} in region {region}")
        else:
            print(f"Error with service {service_name} in region {region}: {str(e)}")
            if verbose:
                print(f"DEBUG: Full exception details for {service_name} in {region}: {type(e).__name__}: {str(e)}")
    except Exception as e:
        print(f"General error with service {service_name} in region {region}: {str(e)}")
        if verbose:
            print(f"DEBUG: Full exception details for {service_name} in {region}: {type(e).__name__}: {str(e)}")

def get_all_resource_arns(additional_services=None, specific_region=None, verbose=False):
    """Get ARNs for all resources across supported services and regions."""
    account_id = get_account_id()
    # Use specific region if provided, otherwise get all regions
    regions = [specific_region] if specific_region else get_all_regions()

    # List of services to check
    default_services = [
        # Default services to scan
        'ec2', 's3', 'lambda', 'dynamodb', 'rds', 'iam',
        'cloudformation', 'sqs', 'sns',
        'kinesisanalytics', 'kinesisanalyticsv2', 'cloudwatch', 'logs', 'route53', 'ecs', 'kms',
    ]

    resource_arns = []

    # Use ThreadPoolExecutor to parallelize API calls
    services = default_services.copy()

    # Add any additional services specified by the user
    if additional_services:
        services.extend([s for s in additional_services if s not in services])

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []

        for service in services:
            if service in global_services:
                futures.append(
                    executor.submit(
                        collect_resources_for_service,
                        service,
                        default_region,  # Use a default region for global services
                        account_id,
                        resource_arns,
                        verbose
                    )
                )
            else:
                for region in regions:  #in each region
                    futures.append(
                        executor.submit(
                            collect_resources_for_service,
                            service,
                            region,
                            account_id,
                            resource_arns,
                            verbose
                        )
                    )

        # Wait for all futures to complete
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error in thread: {str(e)}")
                if verbose:
                    import traceback
                    print(f"DEBUG: Thread exception details: {traceback.format_exc()}")

    return resource_arns

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='List all AWS resource ARNs under the currently logged-in account.')
    parser.add_argument('--services', '-s', nargs='+', help='Additional AWS services to scan (e.g., "apigateway" "kms" "secretsmanager")')
    parser.add_argument('--output', '-o', default='aws_resource_arns.json', help='Output file path (default: aws_resource_arns.json)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose debug output')
    parser.add_argument('--region', '-r', help='Specific AWS region to scan (default: scan all regions)')

    args = parser.parse_args()

    additional_services = args.services
    output_file = args.output

    if additional_services:
        print(f"Including additional services: {', '.join(additional_services)}")

    if args.region:
        print(f"Scanning only region: {args.region}")
        print("Scanning all available regions")

    print("Collecting AWS resource ARNs. This may take a while...")
    if(args.verbose):
        print("VERBOSE=TRUE")
        
    # load service collectors
    SERVICE_COLLECTORS.update(import_service_collectors(args.verbose))
    
    # Pass additional services to the function
    resource_arns = get_all_resource_arns(additional_services, args.region, args.verbose)

    # Print the results
    print(f"\nFound {len(resource_arns)} resources:")
    # for arn in sorted(resource_arns):
    #     print(arn)

    # Optionally save to a file
    with open(output_file, 'w') as f:
        json.dump(resource_arns, f, indent=2)

    print(f"\nResource ARNs have been saved to {output_file}")

if __name__ == "__main__":
    main()