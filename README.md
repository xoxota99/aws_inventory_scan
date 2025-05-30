# AWS Inventory Scanner

A comprehensive Python tool for scanning and inventorying AWS resources across multiple services and regions. This tool discovers and lists all resource ARNs (Amazon Resource Names) in your AWS account.

## Features

- **Multi-Region Support**: Scans resources across all AWS regions or a specific region
- **Multi-Service Support**: Covers a wide range of AWS services (EC2, S3, Lambda, IAM, etc.)
- **Parallel Processing**: Uses concurrent execution to speed up scanning
- **Extensible Architecture**: Easily add support for additional AWS services
- **Error Handling**: Robust error handling with throttling protection and retries
- **Detailed Logging**: Configurable logging levels for troubleshooting

## Prerequisites

- Python 3.6+
- AWS credentials configured (via AWS CLI, environment variables, or IAM role)
- Required Python packages:
  - boto3
  - botocore

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd aws_inventory_scan
   ```

2. Install dependencies:
   ```
   pip install boto3 botocore
   ```

## Usage

### Basic Usage

```bash
# Using the installed command-line tool
aws-inventory-scan scan

# Using the Python module directly
python -m aws_inventory_scan

# Using the script directly
python scan_aws.py
```

### Command Line Options

```bash
# Scan with additional services
aws-inventory-scan scan -s apigateway kms secretsmanager

# Specify output file
aws-inventory-scan scan -o my_inventory.json

# Enable verbose output
aws-inventory-scan scan -v

# Scan a specific region
aws-inventory-scan scan -r us-west-2

# Use a custom configuration file
aws-inventory-scan scan -c my_config.json

# Create a default configuration file
aws-inventory-scan config create

# Show current configuration
aws-inventory-scan config show

# Show version information
aws-inventory-scan version
```

## Project Structure

- `scan_aws.py`: Main script that orchestrates the scanning process
- `service_mappings.py`: Contains mappings between AWS services and their API methods
- `logging_config.py`: Configures logging for the application
- `services/`: Directory containing service-specific resource collectors
  - `ec2.py`: EC2 resource collector
  - `s3.py`: S3 resource collector
  - `iam.py`: IAM resource collector
  - `route53.py`: Route53 resource collector
  - `cloudwatch.py`: CloudWatch resource collector
  - `logs.py`: CloudWatch Logs resource collector
  - `kms.py`: KMS resource collector

## Extending the Tool

### Adding Support for a New Service

1. Add service mapping to `service_mappings.py`:
   ```python
   'new-service': {
       'method': 'list_resources',
       'key': 'Resources',
       'arn_attr': 'ResourceArn'
   }
   ```

2. For more complex services, create a custom collector in the `services` directory:
   ```python
   # services/new_service.py
   def collect_resources(client, region, account_id, resource_arns, verbose=False):
       # Custom collection logic
       pass
   ```

## Configuration

The tool can be configured using a JSON configuration file. By default, it looks for configuration files in the following locations (in order of precedence):

1. `./aws_inventory_scan.json` (current directory)
2. `~/.aws_inventory_scan.json` (user's home directory)
3. `/etc/aws_inventory_scan.json` (system-wide configuration)

You can also specify a custom configuration file using the `--config` option.

### Configuration Options

```json
{
  "aws": {
    "default_region": "us-east-1",
    "global_services": ["iam", "s3", "route53", "cloudfront", "organizations"],
    "default_services": ["ec2", "s3", "lambda", "dynamodb", "rds", "iam"],
    "max_threads": 5,
    "max_retries": 5,
    "initial_backoff": 1,
    "max_backoff": 60
  },
  
  "output": {
    "default_output_file": "aws_resource_arns.json",
    "output_format": "json",
    "pretty_print": true
  },
  
  "logging": {
    "log_level": "INFO",
    "log_file": "",
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  },
  
  "scan": {
    "include_objects": true,
    "max_objects_per_bucket": 100,
    "scan_all_regions": true,
    "skip_empty_services": true
  }
}
```

## Output

The tool generates a JSON file containing an array of all discovered resource ARNs:

```json
[
  "arn:aws:ec2:us-east-1:123456789012:instance/i-0abc123def456789",
  "arn:aws:s3:::my-bucket",
  "arn:aws:lambda:us-west-2:123456789012:function:my-function",
  ...
]
```

## Error Handling

The tool handles various AWS API errors:
- Access denied errors
- Region opt-in requirements
- Invalid credentials
- API throttling (with exponential backoff)

## Performance Considerations

- Uses concurrent execution to scan multiple services and regions in parallel
- Implements throttling protection with exponential backoff
- For very large AWS accounts, consider using the `--region` flag to scan one region at a time

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3) - see the [GNU GPL v3 license](https://www.gnu.org/licenses/gpl-3.0.en.html) for details.
