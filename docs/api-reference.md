# API Reference

This document provides detailed information about the Python API of the AWS Inventory Scanner.

## Core Modules

### scan_aws

The main module that orchestrates the scanning process.

#### Functions

##### `get_all_resource_arns(additional_services=None, specific_region=None, verbose=False)`

Scans AWS resources and returns a list of ARNs.

**Parameters:**
- `additional_services` (list, optional): Additional AWS services to scan beyond the default set.
- `specific_region` (str, optional): Specific AWS region to scan. If not provided, scans all regions.
- `verbose` (bool, optional): Whether to enable verbose logging.

**Returns:**
- List of resource ARNs (strings).

**Example:**
```python
from aws_inventory_scan.scan_aws import get_all_resource_arns

# Scan default services in all regions
arns = get_all_resource_arns()

# Scan specific services in a specific region
arns = get_all_resource_arns(
    additional_services=["apigateway", "kms"],
    specific_region="us-west-2",
    verbose=True
)
```

##### `get_account_id()`

Gets the current AWS account ID.

**Returns:**
- AWS account ID (string).

##### `get_all_regions()`

Gets all available AWS regions.

**Returns:**
- List of region names (strings).

### config

Module for managing configuration.

#### Functions

##### `get_config()`

Gets the current configuration.

**Returns:**
- Configuration dictionary.

##### `load_config()`

Loads configuration from file or uses defaults.

**Returns:**
- Configuration dictionary.

##### `create_default_config(path=None)`

Creates a default configuration file.

**Parameters:**
- `path` (str, optional): Path to save the configuration file. If None, uses the first path in CONFIG_PATHS.

**Returns:**
- True if successful, False otherwise.

##### `get_aws_config()`

Gets AWS-specific configuration.

**Returns:**
- AWS configuration dictionary.

##### `get_output_config()`

Gets output-specific configuration.

**Returns:**
- Output configuration dictionary.

##### `get_logging_config()`

Gets logging-specific configuration.

**Returns:**
- Logging configuration dictionary.

##### `get_scan_config()`

Gets scan-specific configuration.

**Returns:**
- Scan configuration dictionary.

### error_handlers

Module for handling AWS API errors.

#### Classes

##### `AWSErrorHandler`

Class to handle AWS API errors with appropriate retry logic and logging.

**Methods:**
- `__init__(service_name, region, verbose=False)`: Initialize with service and region context.
- `handle_error(error, resource_type=None)`: Handle AWS API errors with appropriate logging and classification.

#### Functions

##### `aws_api_call_with_retry(api_function, service_name, region, max_retries=5, initial_backoff=1, verbose=False, **kwargs)`

Execute an AWS API call with exponential backoff retry logic for throttling errors.

**Parameters:**
- `api_function`: The AWS API function to call.
- `service_name`: Name of the AWS service.
- `region`: AWS region.
- `max_retries` (int, optional): Maximum number of retries.
- `initial_backoff` (int, optional): Initial backoff time in seconds.
- `verbose` (bool, optional): Whether to log verbose details.
- `**kwargs`: Arguments to pass to the API function.

**Returns:**
- The API response or None if all retries failed.

##### `safe_api_call(client, method_name, service_name, region, verbose=False, **kwargs)`

Safely call an AWS API method with error handling.

**Parameters:**
- `client`: boto3 client.
- `method_name`: Name of the client method to call.
- `service_name`: Name of the AWS service.
- `region`: AWS region.
- `verbose` (bool, optional): Whether to log verbose details.
- `**kwargs`: Arguments to pass to the API method.

**Returns:**
- The API response or None if the call failed.

## Service Collectors

### services.ec2

EC2 resource collector.

#### Functions

##### `collect_resources(client, region, account_id, resource_arns, verbose=False)`

Collect EC2 resources in a region.

**Parameters:**
- `client`: boto3 EC2 client.
- `region`: AWS region.
- `account_id`: AWS account ID.
- `resource_arns`: List to append ARNs to.
- `verbose` (bool, optional): Whether to enable verbose logging.

### services.s3

S3 resource collector.

#### Functions

##### `collect_resources(client, region, account_id, resource_arns, verbose=False)`

Collect S3 resources.

**Parameters:**
- `client`: boto3 S3 client.
- `region`: AWS region.
- `account_id`: AWS account ID.
- `resource_arns`: List to append ARNs to.
- `verbose` (bool, optional): Whether to enable verbose logging.

### services.iam

IAM resource collector.

#### Functions

##### `collect_resources(client, region, account_id, resource_arns, verbose=False)`

Collect IAM resources (global service).

**Parameters:**
- `client`: boto3 IAM client.
- `region`: AWS region.
- `account_id`: AWS account ID.
- `resource_arns`: List to append ARNs to.
- `verbose` (bool, optional): Whether to enable verbose logging.
