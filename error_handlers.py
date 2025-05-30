#!/usr/bin/env python3

# This file is part of aws_inventory_scan.
#
# aws_inventory_scan is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# aws_inventory_scan is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with aws_inventory_scan. If not, see <https://www.gnu.org/licenses/>.

"""
Error handling utilities for AWS inventory scan.
Provides centralized error handling for AWS API calls.
"""

import time
import random
from botocore.exceptions import ClientError
import logging

# Configure module logger
logger = logging.getLogger('aws_inventory_scan.error_handlers')

class AWSErrorHandler:
    """Class to handle AWS API errors with appropriate retry logic and logging."""
    
    # Error categories
    ACCESS_ERRORS = ['AccessDenied', 'UnauthorizedOperation', 'AccessDeniedException']
    THROTTLING_ERRORS = ['Throttling', 'RequestLimitExceeded', 'TooManyRequestsException', 'ThrottlingException']
    RESOURCE_ERRORS = ['ResourceNotFoundException', 'NoSuchEntity', 'NoSuchBucket', 'NoSuchKey']
    REGION_ERRORS = ['OptInRequired', 'NotSignedUp']
    AUTH_ERRORS = ['InvalidClientTokenId', 'AuthFailure', 'ExpiredToken', 'InvalidAccessKeyId']
    
    def __init__(self, service_name, region, verbose=False):
        """Initialize with service and region context."""
        self.service_name = service_name
        self.region = region
        self.verbose = verbose
    
    def handle_error(self, error, resource_type=None):
        """Handle AWS API errors with appropriate logging and classification."""
        error_type = type(error).__name__
        error_message = str(error)
        
        context = f"service {self.service_name} in region {self.region}"
        if resource_type:
            context += f" (resource: {resource_type})"
        
        if isinstance(error, ClientError):
            error_code = error.response.get('Error', {}).get('Code', 'Unknown')
            
            # Handle access denied errors
            if error_code in self.ACCESS_ERRORS:
                logger.warning(f"Access denied for {context}: {error_message}")
                return "access_denied"
                
            # Handle throttling errors
            elif error_code in self.THROTTLING_ERRORS:
                logger.warning(f"Request throttled for {context}: {error_message}")
                return "throttled"
                
            # Handle resource not found errors
            elif error_code in self.RESOURCE_ERRORS:
                logger.info(f"Resource not found for {context}: {error_message}")
                return "not_found"
                
            # Handle region opt-in errors
            elif error_code in self.REGION_ERRORS:
                logger.info(f"Region {self.region} requires opt-in for service {self.service_name}")
                return "region_opt_in"
                
            # Handle authentication errors
            elif error_code in self.AUTH_ERRORS:
                logger.error(f"Authentication error for {context}: {error_message}")
                return "auth_error"
                
            # Handle other AWS API errors
            else:
                logger.error(f"AWS API error with {context}: {error_code} - {error_message}")
                return "api_error"
        else:
            # Handle non-ClientError exceptions
            logger.error(f"General error with {context}: {error_type} - {error_message}")
            return "general_error"
        
        # Log full traceback in verbose mode
        if self.verbose:
            import traceback
            logger.debug(f"Full exception details for {context}:\n{traceback.format_exc()}")

def aws_api_call_with_retry(api_function, service_name, region, max_retries=5, initial_backoff=1, verbose=False, **kwargs):
    """
    Execute an AWS API call with exponential backoff retry logic for throttling errors.
    
    Args:
        api_function: The AWS API function to call
        service_name: Name of the AWS service
        region: AWS region
        max_retries: Maximum number of retries
        initial_backoff: Initial backoff time in seconds
        verbose: Whether to log verbose details
        **kwargs: Arguments to pass to the API function
        
    Returns:
        The API response or None if all retries failed
    """
    error_handler = AWSErrorHandler(service_name, region, verbose)
    retries = 0
    
    while True:
        try:
            return api_function(**kwargs)
        except Exception as e:
            error_type = error_handler.handle_error(e)
            
            # Only retry on throttling errors
            if error_type == "throttled" and retries < max_retries:
                # Calculate exponential backoff with jitter
                backoff = min(initial_backoff * (2 ** retries) + random.uniform(0, 1), 60)
                retries += 1
                logger.warning(f"Request throttled. Retrying in {backoff:.2f} seconds... (Attempt {retries}/{max_retries})")
                time.sleep(backoff)
            elif error_type == "auth_error":
                logger.error("Authentication failed. Please check your AWS credentials.")
                return None
            elif error_type == "region_opt_in":
                # No need to retry for region opt-in issues
                return None
            elif error_type == "access_denied":
                # No need to retry for access denied issues
                return None
            else:
                # For other errors, don't retry
                return None
                
def safe_api_call(client, method_name, service_name, region, verbose=False, **kwargs):
    """
    Safely call an AWS API method with error handling.
    
    Args:
        client: boto3 client
        method_name: Name of the client method to call
        service_name: Name of the AWS service
        region: AWS region
        verbose: Whether to log verbose details
        **kwargs: Arguments to pass to the API method
        
    Returns:
        The API response or None if the call failed
    """
    try:
        method = getattr(client, method_name)
        return aws_api_call_with_retry(
            method, 
            service_name=service_name,
            region=region,
            verbose=verbose,
            **kwargs
        )
    except AttributeError:
        logger.error(f"Method {method_name} not found on {service_name} client")
        return None
    except Exception as e:
        error_handler = AWSErrorHandler(service_name, region, verbose)
        error_handler.handle_error(e)
        return None
