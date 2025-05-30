#!/usr/bin/env python3

# This file is part of aws_inventory_scan.
#
# aws_inventory_scan is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# aws_inventory_scan is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with aws_inventory_scan. If not, see <https://www.gnu.org/licenses/>.

"""Tests for the config module."""

import os
import json
import tempfile
import unittest
from unittest.mock import patch, mock_open

# Import the module to test
try:
    from aws_inventory_scan.config import (
        load_config, get_config, deep_merge, create_default_config,
        get_aws_config, get_output_config, get_logging_config, get_scan_config,
        DEFAULT_CONFIG
    )
except ImportError:
    # When running tests directly
    import sys
    import os.path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import (
        load_config, get_config, deep_merge, create_default_config,
        get_aws_config, get_output_config, get_logging_config, get_scan_config,
        DEFAULT_CONFIG
    )


class TestConfig(unittest.TestCase):
    """Test cases for the config module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary config file for testing
        self.test_config = {
            "aws": {
                "default_region": "us-west-2",
                "max_threads": 10
            },
            "output": {
                "pretty_print": False
            }
        }

    def test_deep_merge(self):
        """Test deep_merge function."""
        base = {
            "a": 1,
            "b": {
                "c": 2,
                "d": 3
            }
        }
        override = {
            "b": {
                "c": 4,
                "e": 5
            },
            "f": 6
        }
        expected = {
            "a": 1,
            "b": {
                "c": 4,
                "d": 3,
                "e": 5
            },
            "f": 6
        }
        deep_merge(base, override)
        self.assertEqual(base, expected)

    @patch('builtins.open', new_callable=mock_open, read_data='{"aws": {"default_region": "us-west-2"}}')
    @patch('os.path.exists')
    @patch('os.path.isfile')
    def test_load_config(self, mock_isfile, mock_exists, mock_file):
        """Test load_config function."""
        # Mock file existence
        mock_exists.return_value = True
        mock_isfile.return_value = True
        
        # Load config
        config = load_config()
        
        # Check that config was loaded and merged with defaults
        self.assertEqual(config["aws"]["default_region"], "us-west-2")
        self.assertEqual(config["aws"]["max_threads"], DEFAULT_CONFIG["aws"]["max_threads"])

    def test_get_config(self):
        """Test get_config function."""
        # Should return the same as load_config
        with patch('aws_inventory_scan.config.load_config', return_value={"test": "value"}):
            config = get_config()
            self.assertEqual(config, {"test": "value"})

    def test_create_default_config(self):
        """Test create_default_config function."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Create default config
            result = create_default_config(temp_path)
            self.assertTrue(result)
            
            # Check file contents
            with open(temp_path, 'r') as f:
                saved_config = json.load(f)
            
            self.assertEqual(saved_config, DEFAULT_CONFIG)
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_get_specific_configs(self):
        """Test the specific config getter functions."""
        test_config = {
            "aws": {"key": "aws_value"},
            "output": {"key": "output_value"},
            "logging": {"key": "logging_value"},
            "scan": {"key": "scan_value"}
        }
        
        with patch('aws_inventory_scan.config.get_config', return_value=test_config):
            self.assertEqual(get_aws_config(), {"key": "aws_value"})
            self.assertEqual(get_output_config(), {"key": "output_value"})
            self.assertEqual(get_logging_config(), {"key": "logging_value"})
            self.assertEqual(get_scan_config(), {"key": "scan_value"})


if __name__ == '__main__':
    unittest.main()
