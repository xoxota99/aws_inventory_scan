#!/usr/bin/env python3

# This file is part of aws_inventory_scan.
#
# aws_inventory_scan is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# aws_inventory_scan is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with aws_inventory_scan. If not, see <https://www.gnu.org/licenses/>.

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
