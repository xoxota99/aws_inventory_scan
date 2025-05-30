#!/usr/bin/env python3

# This file is part of aws_inventory_scan.
#
# aws_inventory_scan is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# aws_inventory_scan is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with aws_inventory_scan. If not, see <https://www.gnu.org/licenses/>.

"""
CloudWatch Logs resource collector for AWS inventory scan.
"""

try:
    from logging_config import get_logger
    logger = get_logger()
except ImportError:
    import logging
    logger = logging.getLogger('aws_inventory_scan')

def collect_resources(client, region, account_id, resource_arns, verbose=False):
    """Collect CloudWatch Logs resources in a region."""
    # CloudWatch Log Groups
    paginator = client.get_paginator('describe_log_groups')
    for page in paginator.paginate():
        for log_group in page.get('logGroups', []):
            arn = log_group.get('arn')
            if not arn:  # If ARN is not directly provided, construct it
                log_group_name = log_group['logGroupName']
                arn = f"arn:aws:logs:{region}:{account_id}:log-group:{log_group_name}"
            resource_arns.append(arn)

    if verbose:
        logger.debug(f"Collected CloudWatch Log Groups in {region}")
