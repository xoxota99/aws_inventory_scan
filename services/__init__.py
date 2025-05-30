"""
AWS Inventory Scanner - Service Collectors Package

This package contains service-specific resource collectors for the AWS Inventory Scanner.
Each module in this package implements a collect_resources function that knows how to
collect resources for a specific AWS service.
"""

# Import service collectors to make them available when importing the package
from . import ec2
from . import s3
from . import iam
from . import route53
from . import cloudwatch
from . import logs
from . import kms

# Define the list of available collectors
__all__ = [
    'ec2',
    's3',
    'iam',
    'route53',
    'cloudwatch',
    'logs',
    'kms',
]
