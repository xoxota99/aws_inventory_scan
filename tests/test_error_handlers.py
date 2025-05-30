#!/usr/bin/env python3

# This file is part of aws_inventory_scan.
#
# aws_inventory_scan is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# aws_inventory_scan is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with aws_inventory_scan. If not, see <https://www.gnu.org/licenses/>.

"""Tests for the error_handlers module."""

import unittest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

# Import the module to test
try:
    from aws_inventory_scan.error_handlers import (
        AWSErrorHandler, aws_api_call_with_retry, safe_api_call
    )
except ImportError:
    # When running tests directly
    import sys
    import os.path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from error_handlers import (
        AWSErrorHandler, aws_api_call_with_retry, safe_api_call
    )


class TestErrorHandlers(unittest.TestCase):
    """Test cases for the error_handlers module."""

    def setUp(self):
        """Set up test fixtures."""
        self.service_name = "test-service"
        self.region = "us-west-2"
        self.error_handler = AWSErrorHandler(self.service_name, self.region)

    def test_handle_access_denied_error(self):
        """Test handling of access denied errors."""
        error = ClientError(
            {
                "Error": {
                    "Code": "AccessDenied",
                    "Message": "Access denied"
                }
            },
            "operation"
        )
        result = self.error_handler.handle_error(error)
        self.assertEqual(result, "access_denied")

    def test_handle_throttling_error(self):
        """Test handling of throttling errors."""
        error = ClientError(
            {
                "Error": {
                    "Code": "Throttling",
                    "Message": "Rate exceeded"
                }
            },
            "operation"
        )
        result = self.error_handler.handle_error(error)
        self.assertEqual(result, "throttled")

    def test_handle_resource_not_found_error(self):
        """Test handling of resource not found errors."""
        error = ClientError(
            {
                "Error": {
                    "Code": "ResourceNotFoundException",
                    "Message": "Resource not found"
                }
            },
            "operation"
        )
        result = self.error_handler.handle_error(error)
        self.assertEqual(result, "not_found")

    def test_handle_region_opt_in_error(self):
        """Test handling of region opt-in errors."""
        error = ClientError(
            {
                "Error": {
                    "Code": "OptInRequired",
                    "Message": "Region requires opt-in"
                }
            },
            "operation"
        )
        result = self.error_handler.handle_error(error)
        self.assertEqual(result, "region_opt_in")

    def test_handle_auth_error(self):
        """Test handling of authentication errors."""
        error = ClientError(
            {
                "Error": {
                    "Code": "InvalidClientTokenId",
                    "Message": "Invalid token"
                }
            },
            "operation"
        )
        result = self.error_handler.handle_error(error)
        self.assertEqual(result, "auth_error")

    def test_handle_general_error(self):
        """Test handling of general errors."""
        error = Exception("General error")
        result = self.error_handler.handle_error(error)
        self.assertEqual(result, "general_error")

    @patch('time.sleep')
    def test_aws_api_call_with_retry_success(self, mock_sleep):
        """Test successful API call with retry."""
        mock_function = MagicMock(return_value="success")
        result = aws_api_call_with_retry(
            mock_function, 
            service_name=self.service_name,
            region=self.region,
            max_retries=3
        )
        self.assertEqual(result, "success")
        mock_function.assert_called_once()
        mock_sleep.assert_not_called()

    @patch('time.sleep')
    def test_aws_api_call_with_retry_throttling(self, mock_sleep):
        """Test API call with throttling and retry."""
        error = ClientError(
            {
                "Error": {
                    "Code": "Throttling",
                    "Message": "Rate exceeded"
                }
            },
            "operation"
        )
        mock_function = MagicMock(side_effect=[error, error, "success"])
        
        result = aws_api_call_with_retry(
            mock_function, 
            service_name=self.service_name,
            region=self.region,
            max_retries=3
        )
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_function.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('time.sleep')
    def test_aws_api_call_with_retry_max_exceeded(self, mock_sleep):
        """Test API call with max retries exceeded."""
        error = ClientError(
            {
                "Error": {
                    "Code": "Throttling",
                    "Message": "Rate exceeded"
                }
            },
            "operation"
        )
        mock_function = MagicMock(side_effect=[error, error, error, error])
        
        with self.assertRaises(ClientError):
            aws_api_call_with_retry(
                mock_function, 
                service_name=self.service_name,
                region=self.region,
                max_retries=3
            )
        
        self.assertEqual(mock_function.call_count, 4)
        self.assertEqual(mock_sleep.call_count, 3)

    def test_safe_api_call_success(self):
        """Test safe API call with success."""
        mock_client = MagicMock()
        mock_method = MagicMock(return_value="success")
        mock_client.method_name = mock_method
        
        with patch('aws_inventory_scan.error_handlers.aws_api_call_with_retry', return_value="success"):
            result = safe_api_call(
                mock_client,
                "method_name",
                self.service_name,
                self.region
            )
            
            self.assertEqual(result, "success")

    def test_safe_api_call_attribute_error(self):
        """Test safe API call with attribute error."""
        mock_client = MagicMock(spec=[])
        
        result = safe_api_call(
            mock_client,
            "nonexistent_method",
            self.service_name,
            self.region
        )
        
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
