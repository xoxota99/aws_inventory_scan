# This file is part of aws_inventory_scan.
#
# aws_inventory_scan is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# aws_inventory_scan is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with aws_inventory_scan. If not, see <https://www.gnu.org/licenses/>.

"""
S3 resource collector for AWS inventory scan.
"""

try:
    from logging_config import get_logger
    logger = get_logger()
except ImportError:
    import logging
    logger = logging.getLogger('aws_inventory_scan')

def collect_resources(client, region, account_id, resource_arns, verbose=False):
    """Collect S3 resources."""
    # S3 buckets (global service but listing here)
    response = client.list_buckets()
    bucket_count = len(response.get('Buckets', []))
    for bucket in response.get('Buckets', []):
        bucket_name = bucket['Name']
        arn = f"arn:aws:s3:::{bucket_name}"
        resource_arns.append(arn)

        # List objects in buckets (with pagination)
        try:
            if verbose:
                logger.debug(f"Getting location for bucket {bucket_name}")
            # Only list objects in buckets that are in the current region or global
            bucket_region = client.get_bucket_location(Bucket=bucket_name)
            location_constraint = bucket_region.get('LocationConstraint', '')

            # Handle the special case where None means us-east-1
            if location_constraint is None:
                location_constraint = 'us-east-1'

            if location_constraint == region or location_constraint == '':
                if verbose:
                    logger.debug(f"Listing objects in bucket {bucket_name} (region: {location_constraint})")
                # Only list top-level objects to avoid excessive API calls
                paginator = client.get_paginator('list_objects_v2')
                for page in paginator.paginate(Bucket=bucket_name, MaxKeys=100, Delimiter='/'):
                    for obj in page.get('Contents', []):
                        arn = f"arn:aws:s3:::{bucket_name}/{obj['Key']}"
                        resource_arns.append(arn)
        except Exception as e:
            if verbose:
                logger.debug(f"Error listing objects in bucket {bucket_name}: {str(e)}")
            else:
                print(f"Error listing objects in bucket {bucket_name}: {str(e)}")

    if verbose:
        logger.debug(f"Processed {bucket_count} S3 buckets")
