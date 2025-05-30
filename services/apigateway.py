#!/usr/bin/env python3

# This file is part of aws_inventory_scan.
#
# aws_inventory_scan is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# aws_inventory_scan is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with aws_inventory_scan. If not, see <https://www.gnu.org/licenses/>.

"""
API Gateway resource collector for AWS inventory scan.
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
    """Collect API Gateway resources."""
    if verbose:
        logger.debug(f"Starting API Gateway resource collection in {region}")
    
    # REST APIs
    collect_rest_apis(client, region, account_id, resource_arns, verbose)
    
    # HTTP APIs (API Gateway v2)
    collect_http_apis(client, region, account_id, resource_arns, verbose)

def collect_rest_apis(client: Any, region: str, account_id: str, resource_arns: List[str], verbose: bool = False) -> None:
    """Collect REST API resources."""
    # List REST APIs
    response = safe_api_call(client, 'get_rest_apis', 'apigateway', region, verbose)
    if not response:
        if verbose:
            logger.warning(f"Failed to list REST APIs in {region}")
        return
    
    # Process REST APIs
    for api in response.get('items', []):
        api_id = api.get('id')
        if api_id:
            arn = f"arn:aws:apigateway:{region}::/restapis/{api_id}"
            resource_arns.append(arn)
            if verbose:
                logger.debug(f"Found REST API: {arn}")
            
            # Collect resources for this API
            collect_api_resources(client, region, account_id, resource_arns, api_id, verbose)
            
            # Collect stages for this API
            collect_api_stages(client, region, account_id, resource_arns, api_id, verbose)
    
    # Handle pagination
    position = response.get('position')
    while position:
        response = safe_api_call(
            client, 
            'get_rest_apis', 
            'apigateway', 
            region, 
            verbose,
            position=position
        )
        
        if not response:
            break
        
        for api in response.get('items', []):
            api_id = api.get('id')
            if api_id:
                arn = f"arn:aws:apigateway:{region}::/restapis/{api_id}"
                resource_arns.append(arn)
                if verbose:
                    logger.debug(f"Found REST API: {arn}")
                
                # Collect resources for this API
                collect_api_resources(client, region, account_id, resource_arns, api_id, verbose)
                
                # Collect stages for this API
                collect_api_stages(client, region, account_id, resource_arns, api_id, verbose)
        
        position = response.get('position')

def collect_api_resources(client: Any, region: str, account_id: str, resource_arns: List[str], api_id: str, verbose: bool = False) -> None:
    """Collect API resources for a specific REST API."""
    response = safe_api_call(
        client, 
        'get_resources', 
        'apigateway', 
        region, 
        verbose,
        restApiId=api_id
    )
    
    if not response:
        return
    
    for resource in response.get('items', []):
        resource_id = resource.get('id')
        if resource_id:
            arn = f"arn:aws:apigateway:{region}::/restapis/{api_id}/resources/{resource_id}"
            resource_arns.append(arn)
            if verbose:
                logger.debug(f"Found API resource: {arn}")

def collect_api_stages(client: Any, region: str, account_id: str, resource_arns: List[str], api_id: str, verbose: bool = False) -> None:
    """Collect API stages for a specific REST API."""
    response = safe_api_call(
        client, 
        'get_stages', 
        'apigateway', 
        region, 
        verbose,
        restApiId=api_id
    )
    
    if not response:
        return
    
    for stage in response.get('item', []):
        stage_name = stage.get('stageName')
        if stage_name:
            arn = f"arn:aws:apigateway:{region}::/restapis/{api_id}/stages/{stage_name}"
            resource_arns.append(arn)
            if verbose:
                logger.debug(f"Found API stage: {arn}")

def collect_http_apis(client: Any, region: str, account_id: str, resource_arns: List[str], verbose: bool = False) -> None:
    """Collect HTTP API resources (API Gateway v2)."""
    # Create a separate client for API Gateway v2
    try:
        import boto3
        apigatewayv2_client = boto3.client('apigatewayv2', region_name=region)
    except Exception as e:
        if verbose:
            logger.warning(f"Failed to create API Gateway v2 client in {region}: {str(e)}")
        return
    
    # List HTTP APIs
    response = safe_api_call(apigatewayv2_client, 'get_apis', 'apigatewayv2', region, verbose)
    if not response:
        if verbose:
            logger.warning(f"Failed to list HTTP APIs in {region}")
        return
    
    # Process HTTP APIs
    for api in response.get('Items', []):
        api_id = api.get('ApiId')
        if api_id:
            arn = f"arn:aws:apigateway:{region}::/apis/{api_id}"
            resource_arns.append(arn)
            if verbose:
                logger.debug(f"Found HTTP API: {arn}")
            
            # Collect stages for this API
            collect_http_api_stages(apigatewayv2_client, region, account_id, resource_arns, api_id, verbose)
    
    # Handle pagination
    next_token = response.get('NextToken')
    while next_token:
        response = safe_api_call(
            apigatewayv2_client, 
            'get_apis', 
            'apigatewayv2', 
            region, 
            verbose,
            NextToken=next_token
        )
        
        if not response:
            break
        
        for api in response.get('Items', []):
            api_id = api.get('ApiId')
            if api_id:
                arn = f"arn:aws:apigateway:{region}::/apis/{api_id}"
                resource_arns.append(arn)
                if verbose:
                    logger.debug(f"Found HTTP API: {arn}")
                
                # Collect stages for this API
                collect_http_api_stages(apigatewayv2_client, region, account_id, resource_arns, api_id, verbose)
        
        next_token = response.get('NextToken')

def collect_http_api_stages(client: Any, region: str, account_id: str, resource_arns: List[str], api_id: str, verbose: bool = False) -> None:
    """Collect HTTP API stages for a specific HTTP API."""
    response = safe_api_call(
        client, 
        'get_stages', 
        'apigatewayv2', 
        region, 
        verbose,
        ApiId=api_id
    )
    
    if not response:
        return
    
    for stage in response.get('Items', []):
        stage_name = stage.get('StageName')
        if stage_name:
            arn = f"arn:aws:apigateway:{region}::/apis/{api_id}/stages/{stage_name}"
            resource_arns.append(arn)
            if verbose:
                logger.debug(f"Found HTTP API stage: {arn}")
