# This file is part of aws_inventory_scan.
#
# aws_inventory_scan is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# aws_inventory_scan is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with aws_inventory_scan. If not, see <https://www.gnu.org/licenses/>.

"""
KMS resource collector for AWS inventory scan.
"""

try:
    from logging_config import get_logger
    logger = get_logger()
except ImportError:
    import logging
    logger = logging.getLogger('aws_inventory_scan')
    
def collect_resources(client, region, account_id, resource_arns, verbose=False):
    """Collect KMS resources in a region."""
    if verbose:
        logger.debug(f"Starting KMS resource collection in {region}")

    paginator = client.get_paginator('list_keys')
    for page in paginator.paginate():
        for key in page.get('Keys', []):
            key_id = key['KeyId']
            key_arn = key['KeyArn']
            resource_arns.append(key_arn)

            # Get aliases for each key
            try:
                if verbose:
                    logger.debug(f"Getting aliases for key {key_id}")
                alias_response = client.list_aliases(KeyId=key_id)
                for alias in alias_response.get('Aliases', []):
                    alias_arn = alias['AliasArn']
                    resource_arns.append(alias_arn)
            except Exception as e:
                if verbose:
                    logger.debug(f"Error getting aliases for key {key_id}: {str(e)}")
                else:
                    print(f"Error getting aliases for key {key_id}: {str(e)}")

    if verbose:
        logger.debug(f"Completed KMS resource collection in {region}")