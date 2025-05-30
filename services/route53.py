#!/usr/bin/env python3

# This file is part of aws_inventory_scan.
#
# aws_inventory_scan is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# aws_inventory_scan is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with aws_inventory_scan. If not, see <https://www.gnu.org/licenses/>.

"""
Route53 resource collector for AWS inventory scan.
"""

import time
try:
    from logging_config import get_logger
    logger = get_logger()
except ImportError:
    import logging
    logger = logging.getLogger('aws_inventory_scan')

def collect_resources(client, region, account_id, resource_arns, verbose=False):
    """Collect Route53 resources (global service)."""
    if verbose:
        logger.debug(f"Starting Route53 resource collection")
        start_time = time.time()

    paginator = client.get_paginator('list_hosted_zones')
    for page in paginator.paginate():
        for zone in page.get('HostedZones', []):
            zone_id = zone['Id']
            arn = f"arn:aws:route53:::{zone_id}"
            resource_arns.append(arn)

            # Get record sets for each zone
            try:
                if verbose:
                    logger.debug(f"Getting record sets for zone {zone_id}")
                # Extract the ID without the /hostedzone/ prefix
                clean_zone_id = zone_id.split('/')[-1]
                record_paginator = client.get_paginator('list_resource_record_sets')
                for record_page in record_paginator.paginate(HostedZoneId=clean_zone_id):
                    for record in record_page.get('ResourceRecordSets', []):
                        record_name = record['Name']
                        record_type = record['Type']
                        # Route53 record ARNs don't officially exist, but we can create a pseudo-ARN
                        arn = f"arn:aws:route53:::{zone_id}/record/{record_name}/{record_type}"
                        resource_arns.append(arn)
            except Exception as e:
                if verbose:
                    logger.debug(f"Error getting record sets for zone {zone_id}: {str(e)}")
                else:
                    print(f"Error getting record sets for zone {zone_id}: {str(e)}")

    # Get health checks
    paginator = client.get_paginator('list_health_checks')
    for page in paginator.paginate():
        for health_check in page.get('HealthChecks', []):
            health_check_id = health_check['Id']
            arn = f"arn:aws:route53:::healthcheck/{health_check_id}"
            resource_arns.append(arn)

    if verbose:
        elapsed = time.time() - start_time
        logger.debug(f"Completed Route53 resource collection in {elapsed:.2f}s")