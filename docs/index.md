# AWS Inventory Scanner Documentation

Welcome to the AWS Inventory Scanner documentation. This tool helps you discover and list all AWS resources across multiple services and regions.

## Overview

AWS Inventory Scanner is a Python tool that scans your AWS account and generates a comprehensive inventory of all resources. It uses the AWS SDK for Python (boto3) to query various AWS services and collect resource ARNs (Amazon Resource Names).

## Features

- **Multi-Region Support**: Scans resources across all AWS regions or a specific region
- **Multi-Service Support**: Covers a wide range of AWS services (EC2, S3, Lambda, IAM, etc.)
- **Parallel Processing**: Uses concurrent execution to speed up scanning
- **Extensible Architecture**: Easily add support for additional AWS services
- **Error Handling**: Robust error handling with throttling protection and retries
- **Detailed Logging**: Configurable logging levels for troubleshooting

## Installation

```bash
# Install from PyPI
pip install aws-inventory-scan

# Install from source
git clone https://github.com/yourusername/aws_inventory_scan.git
cd aws_inventory_scan
pip install -e .
```

## Quick Start

```bash
# Run a basic scan
aws-inventory-scan scan

# Scan specific services
aws-inventory-scan scan -s apigateway kms secretsmanager

# Scan a specific region
aws-inventory-scan scan -r us-west-2

# Enable verbose output
aws-inventory-scan scan -v
```

## Next Steps

- [User Guide](user-guide.md): Detailed instructions for using the tool
- [Configuration](configuration.md): How to configure the tool
- [API Reference](api-reference.md): Documentation for the Python API
- [Contributing](contributing.md): How to contribute to the project
