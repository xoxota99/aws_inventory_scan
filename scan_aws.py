#!/usr/bin/env python3

import boto3
import json
from botocore.exceptions import ClientError
import argparse
import concurrent.futures

default_region = 'us-east-1'

def get_all_regions():
    """Get all available AWS regions."""
    ec2_client = boto3.client('ec2', region_name=default_region)  # Specify a default region
    regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
    return regions

def get_account_id():
    """Get the current AWS account ID."""
    sts_client = boto3.client('sts', region_name=default_region)  # Specify the region explicitly
    return sts_client.get_caller_identity()["Account"]

def collect_resources_for_service(service_name, region, account_id, resource_arns):
    """Collect resources for a specific service in a region."""
    try:
        # Create a boto3 client for the service in the specified region
        client = boto3.client(service_name, region_name=region)

        # Different services have different list/describe methods
        if service_name == 'ec2':
            # EC2 instances
            response = client.describe_instances()
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instance_id = instance['InstanceId']
                    arn = f"arn:aws:ec2:{region}:{account_id}:instance/{instance_id}"
                    resource_arns.append(arn)

            # EC2 volumes
            response = client.describe_volumes()
            for volume in response.get('Volumes', []):
                volume_id = volume['VolumeId']
                arn = f"arn:aws:ec2:{region}:{account_id}:volume/{volume_id}"
                resource_arns.append(arn)

            # EC2 security groups
            response = client.describe_security_groups()
            for sg in response.get('SecurityGroups', []):
                sg_id = sg['GroupId']
                arn = f"arn:aws:ec2:{region}:{account_id}:security-group/{sg_id}"
                resource_arns.append(arn)

        elif service_name == 's3':
            # S3 buckets (global service but listing here)
            response = client.list_buckets()
            for bucket in response.get('Buckets', []):
                bucket_name = bucket['Name']
                arn = f"arn:aws:s3:::{bucket_name}"
                resource_arns.append(arn)

        elif service_name == 'lambda':
            # Lambda functions
            response = client.list_functions()
            for function in response.get('Functions', []):
                arn = function['FunctionArn']
                resource_arns.append(arn)

        elif service_name == 'dynamodb':
            # DynamoDB tables
            response = client.list_tables()
            for table_name in response.get('TableNames', []):
                arn = f"arn:aws:dynamodb:{region}:{account_id}:table/{table_name}"
                resource_arns.append(arn)

        elif service_name == 'rds':
            # RDS instances
            response = client.describe_db_instances()
            for instance in response.get('DBInstances', []):
                arn = instance['DBInstanceArn']
                resource_arns.append(arn)

        elif service_name == 'iam':
            # IAM roles (global service)
            if region == default_region:  # Only check in one region to avoid duplicates
                response = client.list_roles()
                for role in response.get('Roles', []):
                    arn = role['Arn']
                    resource_arns.append(arn)

                # IAM users
                response = client.list_users()
                for user in response.get('Users', []):
                    arn = user['Arn']
                    resource_arns.append(arn)

        elif service_name == 'cloudformation':
            # CloudFormation stacks
            response = client.list_stacks()
            for stack in response.get('StackSummaries', []):
                arn = stack['StackId']
                resource_arns.append(arn)

        elif service_name == 'sqs':
            # SQS queues
            response = client.list_queues()
            for queue_url in response.get('QueueUrls', []):
                queue_attrs = client.get_queue_attributes(
                    QueueUrl=queue_url,
                    AttributeNames=['QueueArn']
                )
                arn = queue_attrs['Attributes']['QueueArn']
                resource_arns.append(arn)

        elif service_name == 'sns':
            # SNS topics
            response = client.list_topics()
            for topic in response.get('Topics', []):
                arn = topic['TopicArn']
                resource_arns.append(arn)

    except ClientError as e:
        if 'AccessDenied' in str(e) or 'UnauthorizedOperation' in str(e):
            print(f"Access denied for service {service_name} in region {region}")
        elif 'OptInRequired' in str(e):
            print(f"Region {region} requires opt-in for service {service_name}")
        elif 'InvalidClientTokenId' in str(e):
            print(f"Invalid credentials for service {service_name} in region {region}")
        else:
            print(f"Error with service {service_name} in region {region}: {e}")
    except Exception as e:
        print(f"General error with service {service_name} in region {region}: {e}")

def get_all_resource_arns(additional_services=None, specific_region=None):
    """Get ARNs for all resources across supported services and regions."""
    account_id = get_account_id()
    # Use specific region if provided, otherwise get all regions
    regions = [specific_region] if specific_region else get_all_regions()

    # List of services to check
    default_services = [
        # Default services to scan
        'ec2', 's3', 'lambda', 'dynamodb', 'rds', 'iam',
        'cloudformation', 'sqs', 'sns',
    ]

    resource_arns = []

    # Use ThreadPoolExecutor to parallelize API calls
    services = default_services.copy()

    # Add any additional services specified by the user
    if additional_services:
        services.extend([s for s in additional_services if s not in services])

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []

        # Global services only need to be checked once
        global_services = ['iam', 's3']

        for service in services:
            if service in global_services:
                futures.append(
                    executor.submit(
                        collect_resources_for_service,
                        service,
                        default_region,  # Use a default region for global services
                        account_id,
                        resource_arns
                    )
                )
            else:
                for region in regions:
                    futures.append(
                        executor.submit(
                            collect_resources_for_service,
                            service,
                            region,
                            account_id,
                            resource_arns
                        )
                    )

        # Wait for all futures to complete
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error in thread: {e}")

    return resource_arns

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='List all AWS resource ARNs under the currently logged-in account.')
    parser.add_argument('--services', '-s', nargs='+', help='Additional AWS services to scan (e.g., "apigateway" "kms" "secretsmanager")')
    parser.add_argument('--output', '-o', default='aws_resource_arns.json', help='Output file path (default: aws_resource_arns.json)')
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
    # Pass additional services to the function
    resource_arns = get_all_resource_arns(additional_services, args.region)

    # Print the results
    print(f"\nFound {len(resource_arns)} resources:")
    for arn in sorted(resource_arns):
        print(arn)

    # Optionally save to a file
    with open(output_file, 'w') as f:
        json.dump(resource_arns, f, indent=2)

    print(f"\nResource ARNs have been saved to {output_file}")

if __name__ == "__main__":
    main()