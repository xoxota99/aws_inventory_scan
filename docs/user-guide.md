# User Guide

This guide provides detailed instructions for using the AWS Inventory Scanner.

## Prerequisites

Before using the AWS Inventory Scanner, you need:

1. **AWS Credentials**: Configure your AWS credentials using one of these methods:
   - AWS CLI: Run `aws configure`
   - Environment variables: Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
   - IAM role: When running on an EC2 instance or other AWS service

2. **Python 3.6+**: The tool requires Python 3.6 or later.

3. **Required Packages**: Install the required packages:
   ```bash
   pip install boto3 botocore
   ```

## Installation

### From PyPI

```bash
pip install aws-inventory-scan
```

### From Source

```bash
git clone https://github.com/yourusername/aws_inventory_scan.git
cd aws_inventory_scan
pip install -e .
```

## Basic Usage

### Running a Scan

To scan your AWS account for resources:

```bash
aws-inventory-scan scan
```

This will scan all regions and the default set of services, then save the results to `aws_resource_arns.json`.

### Specifying Services

To scan additional services beyond the default set:

```bash
aws-inventory-scan scan -s apigateway kms secretsmanager
```

### Specifying a Region

To scan only a specific region:

```bash
aws-inventory-scan scan -r us-west-2
```

### Output File

To specify a custom output file:

```bash
aws-inventory-scan scan -o my_inventory.json
```

### Verbose Output

To enable detailed logging:

```bash
aws-inventory-scan scan -v
```

## Configuration

### Creating a Configuration File

Create a default configuration file:

```bash
aws-inventory-scan config create
```

This creates `aws_inventory_scan.json` in the current directory.

### Viewing Current Configuration

View the current configuration:

```bash
aws-inventory-scan config show
```

### Using a Custom Configuration File

Use a custom configuration file:

```bash
aws-inventory-scan scan -c my_config.json
```

## Advanced Usage

### Scanning Large AWS Accounts

For large AWS accounts, consider:

1. Scanning one region at a time:
   ```bash
   aws-inventory-scan scan -r us-east-1
   ```

2. Increasing the thread count in the configuration:
   ```json
   {
     "aws": {
       "max_threads": 10
     }
   }
   ```

3. Excluding S3 objects to reduce API calls:
   ```json
   {
     "scan": {
       "include_objects": false
     }
   }
   ```

### Troubleshooting

If you encounter issues:

1. Enable verbose logging:
   ```bash
   aws-inventory-scan scan -v
   ```

2. Check AWS credentials:
   ```bash
   aws sts get-caller-identity
   ```

3. Verify region access:
   ```bash
   aws ec2 describe-regions
   ```

4. Look for throttling errors in the logs, which might indicate you need to reduce concurrency.
