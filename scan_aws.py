#!/usr/bin/env python3

# This file is part of aws_inventory_scan.
#
# aws_inventory_scan is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# aws_inventory_scan is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with aws_inventory_scan. If not, see <https://www.gnu.org/licenses/>.

import boto3
import json
from botocore.exceptions import ClientError
import argparse
import concurrent.futures
import logging
import sys
import random
import os
import importlib.util
import time
from logging_config import configure_logging, get_logger

# Load service-specific collectors
SERVICE_COLLECTORS = {}

# Default region for global services
default_region = 'us-east-1'

# Define global services that should only be queried once
global_services = ['iam', 's3', 'route53', 'cloudfront', 'organizations',
                  'waf', 'shield', 'budgets', 'ce', 'chatbot', 'health']

# Configure logging
logger = None  # Will be initialized in main()

# Import service mappings from separate module
def import_service_mappings():
    """Import service mappings from service_mappings.py"""

    from service_mappings import SERVICE_MAPPINGS
    return SERVICE_MAPPINGS

def setup_logging(verbose=False):
    """Set up logging configuration using the logging_config module."""
    return configure_logging(verbose)

def log_error(service_name, region, error, verbose=False):
    """Centralized error logging function."""
    error_type = type(error).__name__
    error_message = str(error)

    if isinstance(error, ClientError):
        error_code = error.response.get('Error', {}).get('Code', 'Unknown')
        if error_code in ['AccessDenied', 'UnauthorizedOperation']:
            logger.warning(f"Access denied for service {service_name} in region {region}: {error_message}")
        elif error_code == 'OptInRequired':
            logger.info(f"Region {region} requires opt-in for service {service_name}")
        elif error_code == 'InvalidClientTokenId':
            logger.error(f"Invalid credentials for service {service_name} in region {region}")
        elif error_code in ['Throttling', 'RequestLimitExceeded', 'TooManyRequestsException']:
            logger.warning(f"Request throttled for service {service_name} in region {region}: {error_message}")
        else:
            logger.error(f"AWS API error with service {service_name} in region {region}: {error_code} - {error_message}")
    else:
        logger.error(f"General error with service {service_name} in region {region}: {error_type} - {error_message}")

    if verbose:
        import traceback
        logger.debug(f"Full exception details for {service_name} in {region}:\n{traceback.format_exc()}")

def is_throttling_error(error):
    """Check if the error is a throttling-related error."""
    return isinstance(error, ClientError) and error.response.get('Error', {}).get('Code', '') in ['Throttling', 'RequestLimitExceeded', 'TooManyRequestsException']

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
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code in ['ExpiredToken', 'InvalidClientTokenId', 'AccessDenied']:
            logger.error("AWS authentication failed. Please check your credentials and try again.")
            logger.error("Make sure you have valid AWS credentials configured via AWS CLI, environment variables, or IAM role.")
            logger.error(f"Specific error: {str(e)}")
        else:
            logger.error(f"Unexpected error when authenticating: {str(e)}")
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
            logger.debug(f"Processing {service_name} in {region} using method {mapping['method']}")
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
                    logger.debug(f"Skipping textract as it requires a document ID")
                # Textract requires a document ID which we don't have
                return []
            else:
                if verbose:
                    logger.debug(f"Calling {method_name} for {service_name} in {region}")
                    call_start = time.time()
                # Standard method call
                response = aws_api_call_with_retry(method)

            # Extract resources based on the mapping
            if 'direct_arn' in mapping and mapping['direct_arn']:
                # The response itself is the ARN
                if response_key in response:
                    if verbose:
                        logger.debug(f"Found direct ARN for {service_name}")

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
                        logger.debug(f"Processing ID list with {len(items)} items for {service_name}")
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
                        logger.debug(f"Processing ARN list with {len(items)} items for {service_name}")
                    resources.extend(items)
                else:
                    # Response is a list of objects
                    if verbose:
                        logger.debug(f"Processing object list with {len(items)} items for {service_name}")
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
                logger.debug(f"Completed {service_name} in {region} in {elapsed:.2f}s, found {len(resources)} resources")


        except Exception as e:
            # Just log the error and continue
            log_error(service_name, region, e, verbose)

    return resources

def aws_api_call_with_retry(api_function, max_retries=5, initial_backoff=1, **kwargs):
    """
    Execute an AWS API call with exponential backoff retry logic for throttling errors.

    Args:
        api_function: The AWS API function to call
        max_retries: Maximum number of retries
        initial_backoff: Initial backoff time in seconds
        **kwargs: Arguments to pass to the API function

    Returns:
        The API response
    """
    retries = 0
    while True:
        try:
            return api_function(**kwargs)
        except Exception as e:
            if is_throttling_error(e) and retries < max_retries:
                # Calculate exponential backoff with jitter
                backoff = min(initial_backoff * (2 ** retries) + random.uniform(0, 1), 60)
                retries += 1
                logger.warning(f"Request throttled. Retrying in {backoff:.2f} seconds... (Attempt {retries}/{max_retries})")
                time.sleep(backoff)
            else:
                # If it's not a throttling error or we've exceeded max retries, re-raise
                raise

def collect_resources_with_error_handling(client, service_name, method_name, key_path, region, account_id, resource_arns, verbose=False):
    """Generic function to collect resources with proper error handling."""
    try:
        method = getattr(client, method_name)
        response = aws_api_call_with_retry(method)

        # Navigate to the correct response key, handling nested keys with dots
        items = response
        for key_part in key_path.split('.'):
            if key_part in items:
                items = items[key_part]
            else:
                items = []
                break

        return items
    except Exception as e:
        log_error(service_name, region, e, verbose)
        return []
    
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
                    logger.debug(f"importing module {filename}")
                    
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
                logger.debug(f"Full exception details for {service_name} in {region}: {type(e).__name__}: {str(e)}")

    except Exception as e:
        print(f"General error with service {service_name} in region {region}: {str(e)}")
        if verbose:
            logger.debug(f"Full exception details for {service_name} in {region}: {type(e).__name__}: {str(e)}")

def get_all_resource_arns(additional_services=None, specific_region=None, verbose=False):

    global logger
    if logger is None:
        logger = get_logger()

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
                    logger.debug(f"Thread exception details: {traceback.format_exc()}")

    return resource_arns

def main():
    global logger

    # Initialize logging first thing
    logger = setup_logging(False)  # Will be updated with verbose flag later

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
        
    # Update logger with verbose setting if needed
    if args.verbose:
        logger = setup_logging(args.verbose)

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
    logging.basicConfig(level=logging.INFO)  # Default basic config before proper setup
    main()