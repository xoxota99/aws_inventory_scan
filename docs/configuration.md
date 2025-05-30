# Configuration

The AWS Inventory Scanner can be configured using a JSON configuration file. This document explains the available configuration options and how to use them.

## Configuration File Locations

The tool looks for configuration files in the following locations (in order of precedence):

1. Custom path specified with the `--config` option
2. `./aws_inventory_scan.json` (current directory)
3. `~/.aws_inventory_scan.json` (user's home directory)
4. `/etc/aws_inventory_scan.json` (system-wide configuration)

## Creating a Configuration File

You can create a default configuration file using the CLI:

```bash
aws-inventory-scan config create
```

This creates `aws_inventory_scan.json` in the current directory with default settings.

To create the configuration file in a specific location:

```bash
aws-inventory-scan config create --path ~/.aws_inventory_scan.json
```

## Configuration Structure

The configuration file is structured into sections:

```json
{
  "aws": {
    // AWS-specific settings
  },
  "output": {
    // Output settings
  },
  "logging": {
    // Logging settings
  },
  "scan": {
    // Scan settings
  }
}
```

## AWS Settings

```json
"aws": {
  "default_region": "us-east-1",
  "global_services": [
    "iam", "s3", "route53", "cloudfront", "organizations",
    "waf", "shield", "budgets", "ce", "chatbot", "health"
  ],
  "default_services": [
    "ec2", "s3", "lambda", "dynamodb", "rds", "iam",
    "cloudformation", "sqs", "sns",
    "kinesisanalytics", "kinesisanalyticsv2", "cloudwatch", "logs", 
    "route53", "ecs", "kms"
  ],
  "max_threads": 5,
  "max_retries": 5,
  "initial_backoff": 1,
  "max_backoff": 60
}
```

- `default_region`: The default region to use for global services
- `global_services`: List of services that are global (not region-specific)
- `default_services`: List of services to scan by default
- `max_threads`: Maximum number of concurrent threads for API calls
- `max_retries`: Maximum number of retries for throttled API calls
- `initial_backoff`: Initial backoff time in seconds for retries
- `max_backoff`: Maximum backoff time in seconds for retries

## Output Settings

```json
"output": {
  "default_output_file": "aws_resource_arns.json",
  "output_format": "json",
  "pretty_print": true
}
```

- `default_output_file`: Default file path for saving results
- `output_format`: Format for output (currently only "json" is supported)
- `pretty_print`: Whether to format JSON output with indentation

## Logging Settings

```json
"logging": {
  "log_level": "INFO",
  "log_file": "",
  "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
}
```

- `log_level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `log_file`: Path to log file (empty string means log to console only)
- `log_format`: Format string for log messages

## Scan Settings

```json
"scan": {
  "include_objects": true,
  "max_objects_per_bucket": 100,
  "scan_all_regions": true,
  "skip_empty_services": true
}
```

- `include_objects`: Whether to include S3 objects in the scan
- `max_objects_per_bucket`: Maximum number of objects to list per S3 bucket
- `scan_all_regions`: Whether to scan all regions by default
- `skip_empty_services`: Whether to skip services that return no resources

## Using Environment Variables

Some settings can be overridden with environment variables:

- `AWS_DEFAULT_REGION`: Overrides the default region
- `AWS_INVENTORY_SCAN_OUTPUT`: Overrides the default output file
- `AWS_INVENTORY_SCAN_VERBOSE`: Set to "true" to enable verbose logging

## Command Line Overrides

Command line options take precedence over configuration file settings:

- `--region` overrides the default region
- `--output` overrides the default output file
- `--verbose` enables verbose logging regardless of configuration
- `--services` adds services to the default list
