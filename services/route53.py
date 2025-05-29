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