#!/usr/bin/env python3

# This file is part of aws_inventory_scan.
#
# aws_inventory_scan is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# aws_inventory_scan is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with aws_inventory_scan. If not, see <https://www.gnu.org/licenses/>.

"""
Secrets Manager resource collector for AWS inventory scan.
"""

from typing import List, Dict, Any, Optional

try:
    from logging_config import get_logger
    logger = get_logger()
except ImportError:
    import logging
    logger = logging.getLogger('aws_inventory_scan')

try:
    from error_handlers import safe_api_call
except ImportError:
    # Fallback if error_handlers module is not available
    def safe_api_call(client: Any, method_name: str, service_name: str, region: str, verbose: bool = False, **kwargs: Any) -> Optional[Dict[str, Any]]:
        try:
            method = getattr(client, method_name)
            return method(**kwargs)
        except Exception as e:
            if verbose:
                logger.debug(f"Error calling {method_name} for {service_name} in {region}: {str(e)}")
            return None

def collect_resources(client: Any, region: str, account_id: str, resource_arns: List[str], verbose: bool = False) -> None:
    """Collect Secrets Manager resources."""
    if verbose:
        logger.debug(f"Starting Secrets Manager resource collection in {region}")
    
    # List secrets
    response = safe_api_call(client, 'list_secrets', 'secretsmanager', region, verbose)
    if not response:
        if verbose:
            logger.warning(f"Failed to list Secrets Manager secrets in {region}")
        return
    
    # Process secrets
    for secret in response.get('SecretList', []):
        arn = secret.get('ARN')
        if arn:
            resource_arns.append(arn)
            if verbose:
                logger.debug(f"Found secret: {arn}")
    
    # Handle pagination
    next_token = response.get('NextToken')
    while next_token:
        response = safe_api_call(
            client, 
            'list_secrets', 
            'secretsmanager', 
            region, 
            verbose,
            NextToken=next_token
        )
        
        if not response:
            break
        
        for secret in response.get('SecretList', []):
            arn = secret.get('ARN')
            if arn:
                resource_arns.append(arn)
                if verbose:
                    logger.debug(f"Found secret: {arn}")
        
        next_token = response.get('NextToken')
    
    if verbose:
        logger.debug(f"Completed Secrets Manager resource collection in {region}, found {len(resource_arns)} secrets")
