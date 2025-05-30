#!/usr/bin/env python3

# This file is part of aws_inventory_scan.
#
# aws_inventory_scan is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# aws_inventory_scan is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with aws_inventory_scan. If not, see <https://www.gnu.org/licenses/>.

"""Pytest configuration and fixtures."""

import os
import json
import tempfile
import pytest
from unittest.mock import MagicMock

# Mock AWS clients and resources
@pytest.fixture
def mock_boto3_client():
    """Create a mock boto3 client."""
    mock_client = MagicMock()
    
    # Mock common methods
    mock_client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-12345678",
                        "InstanceType": "t2.micro",
                        "State": {"Name": "running"}
                    }
                ]
            }
        ]
    }
    
    mock_client.list_buckets.return_value = {
        "Buckets": [
            {
                "Name": "test-bucket",
                "CreationDate": "2023-01-01T00:00:00+00:00"
            }
        ]
    }
    
    mock_client.get_bucket_location.return_value = {
        "LocationConstraint": "us-west-2"
    }
    
    mock_client.list_functions.return_value = {
        "Functions": [
            {
                "FunctionName": "test-function",
                "FunctionArn": "arn:aws:lambda:us-west-2:123456789012:function:test-function"
            }
        ]
    }
    
    return mock_client

@pytest.fixture
def mock_boto3():
    """Create a mock boto3 module."""
    mock_boto3 = MagicMock()
    mock_client = MagicMock()
    
    # Set up the mock client to return our mock_boto3_client
    mock_boto3.client.return_value = mock_client
    
    return mock_boto3

@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file."""
    config = {
        "aws": {
            "default_region": "us-west-2",
            "max_threads": 10
        },
        "output": {
            "default_output_file": "test_output.json"
        }
    }
    
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
        json.dump(config, temp_file)
        temp_path = temp_file.name
    
    yield temp_path
    
    # Clean up
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def mock_aws_credentials():
    """Mock AWS credentials for testing."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-west-2'
    
    yield
    
    # Clean up
    del os.environ['AWS_ACCESS_KEY_ID']
    del os.environ['AWS_SECRET_ACCESS_KEY']
    del os.environ['AWS_SECURITY_TOKEN']
    del os.environ['AWS_SESSION_TOKEN']
    del os.environ['AWS_DEFAULT_REGION']
