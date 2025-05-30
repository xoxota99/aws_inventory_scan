#!/usr/bin/env python3

# This file is part of aws_inventory_scan.
#
# aws_inventory_scan is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# aws_inventory_scan is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with aws_inventory_scan. If not, see <https://www.gnu.org/licenses/>.

"""Tests for the CLI module."""

import unittest
from unittest.mock import patch, MagicMock
import sys

# Import the module to test
try:
    from aws_inventory_scan.cli import parse_args, main
except ImportError:
    # When running tests directly
    import sys
    import os.path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from cli import parse_args, main


class TestCLI(unittest.TestCase):
    """Test cases for the CLI module."""

    def test_parse_args_scan(self):
        """Test parsing scan command arguments."""
        args = parse_args(["scan", "-s", "ec2", "s3", "-v", "-r", "us-west-2"])
        self.assertEqual(args.command, "scan")
        self.assertEqual(args.services, ["ec2", "s3"])
        self.assertTrue(args.verbose)
        self.assertEqual(args.region, "us-west-2")

    def test_parse_args_config_create(self):
        """Test parsing config create command arguments."""
        args = parse_args(["config", "create", "-p", "/tmp/config.json"])
        self.assertEqual(args.command, "config")
        self.assertEqual(args.config_command, "create")
        self.assertEqual(args.path, "/tmp/config.json")

    def test_parse_args_config_show(self):
        """Test parsing config show command arguments."""
        args = parse_args(["config", "show"])
        self.assertEqual(args.command, "config")
        self.assertEqual(args.config_command, "show")

    def test_parse_args_version(self):
        """Test parsing version command arguments."""
        args = parse_args(["version"])
        self.assertEqual(args.command, "version")

    def test_parse_args_no_command(self):
        """Test parsing with no command (should default to scan)."""
        with patch('sys.argv', ['aws-inventory-scan']):
            args = parse_args([])
            self.assertIsNone(args.command)

    @patch('aws_inventory_scan.cli.scan_main')
    @patch('sys.argv')
    def test_main_scan(self, mock_argv, mock_scan_main):
        """Test main function with scan command."""
        with patch('aws_inventory_scan.cli.parse_args') as mock_parse_args:
            mock_args = MagicMock()
            mock_args.command = "scan"
            mock_args.services = ["ec2", "s3"]
            mock_args.verbose = True
            mock_args.region = "us-west-2"
            mock_args.output = "output.json"
            mock_args.config = None
            mock_parse_args.return_value = mock_args
            
            main()
            
            mock_scan_main.assert_called_once()
            # Check that sys.argv was modified correctly
            self.assertIn("--services", sys.argv)
            self.assertIn("ec2", sys.argv)
            self.assertIn("s3", sys.argv)
            self.assertIn("--verbose", sys.argv)
            self.assertIn("--region", sys.argv)
            self.assertIn("us-west-2", sys.argv)
            self.assertIn("--output", sys.argv)
            self.assertIn("output.json", sys.argv)

    @patch('aws_inventory_scan.cli.create_default_config')
    def test_main_config_create(self, mock_create_config):
        """Test main function with config create command."""
        with patch('aws_inventory_scan.cli.parse_args') as mock_parse_args:
            mock_args = MagicMock()
            mock_args.command = "config"
            mock_args.config_command = "create"
            mock_args.path = "/tmp/config.json"
            mock_parse_args.return_value = mock_args
            
            main()
            
            mock_create_config.assert_called_once_with("/tmp/config.json")

    @patch('aws_inventory_scan.cli.show_config')
    def test_main_config_show(self, mock_show_config):
        """Test main function with config show command."""
        with patch('aws_inventory_scan.cli.parse_args') as mock_parse_args:
            mock_args = MagicMock()
            mock_args.command = "config"
            mock_args.config_command = "show"
            mock_args.path = None
            mock_parse_args.return_value = mock_args
            
            main()
            
            mock_show_config.assert_called_once_with(None)

    @patch('aws_inventory_scan.cli.show_version')
    def test_main_version(self, mock_show_version):
        """Test main function with version command."""
        with patch('aws_inventory_scan.cli.parse_args') as mock_parse_args:
            mock_args = MagicMock()
            mock_args.command = "version"
            mock_parse_args.return_value = mock_args
            
            main()
            
            mock_show_version.assert_called_once()


if __name__ == '__main__':
    unittest.main()
