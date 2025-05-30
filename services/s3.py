#!/usr/bin/env python3

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

try:
    from error_handlers import safe_api_call, AWSErrorHandler
except ImportError:
    # Fallback if error_handlers module is not available
    def safe_api_call(client, method_name, service_name, region, verbose=False, **kwargs):
        try:
            method = getattr(client, method_name)
            return method(**kwargs)
        except Exception as e:
            if verbose:
                logger.debug(f"Error calling {method_name} for {service_name} in {region}: {str(e)}")
            return None
    
    class AWSErrorHandler:
        def __init__(self, service_name, region, verbose=False):
            self.service_name = service_name
            self.region = region
            self.verbose = verbose
        
        def handle_error(self, error, resource_type=None):
            if self.verbose:
                logger.debug(f"Error with {self.service_name} in {self.region}: {str(error)}")
            return "error"

def collect_resources(client, region, account_id, resource_arns, verbose=False):
    """Collect S3 resources."""
    error_handler = AWSErrorHandler('s3', region, verbose)
    
    # S3 buckets (global service but listing here)
    response = safe_api_call(client, 'list_buckets', 's3', region, verbose)
    if not response:
        if verbose:
            logger.warning(f"Failed to list S3 buckets in {region}")
        return
        
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
            bucket_region_response = safe_api_call(
                client, 'get_bucket_location', 's3', region, verbose, 
                Bucket=bucket_name
            )
            
            if not bucket_region_response:
                if verbose:
                    logger.warning(f"Failed to get location for bucket {bucket_name}")
                continue
                
            location_constraint = bucket_region_response.get('LocationConstraint', '')

            # Handle the special case where None means us-east-1
            if location_constraint is None:
                location_constraint = 'us-east-1'

            if location_constraint == region or location_constraint == '':
                if verbose:
                    logger.debug(f"Listing objects in bucket {bucket_name} (region: {location_constraint})")
                    
                # Only list top-level objects to avoid excessive API calls
                paginator = client.get_paginator('list_objects_v2')
                try:
                    for page in paginator.paginate(Bucket=bucket_name, MaxKeys=100, Delimiter='/'):
                        for obj in page.get('Contents', []):
                            arn = f"arn:aws:s3:::{bucket_name}/{obj['Key']}"
                            resource_arns.append(arn)
                except Exception as e:
                    error_handler.handle_error(e, f"bucket/{bucket_name}/objects")
                    if verbose:
                        logger.warning(f"Error listing objects in bucket {bucket_name}: {str(e)}")
        except Exception as e:
            error_handler.handle_error(e, f"bucket/{bucket_name}")
            if verbose:
                logger.warning(f"Error processing bucket {bucket_name}: {str(e)}")

    if verbose:
        logger.debug(f"Processed {bucket_count} S3 buckets")
