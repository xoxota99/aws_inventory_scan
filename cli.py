#!/usr/bin/env python3

# This file is part of aws_inventory_scan.
#
# aws_inventory_scan is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# aws_inventory_scan is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with aws_inventory_scan. If not, see <https://www.gnu.org/licenses/>.

"""
Command-line interface for AWS Inventory Scanner.
Provides a user-friendly CLI for scanning AWS resources.
"""

import argparse
import sys
import os
import json
from typing import List, Optional

try:
    from .scan_aws import main as scan_main
    from .config import get_config, create_default_config
    from .__init__ import __version__
except ImportError:
    # When running as a script, not as a package
    from scan_aws import main as scan_main
    try:
        from config import get_config, create_default_config
        from __init__ import __version__
    except ImportError:
        __version__ = "0.1.0"
        def get_config():
            return {}
        def create_default_config(path=None):
            print("Configuration module not available.")
            return False

def parse_args(args: List[str]) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="aws-inventory-scan",
        description="AWS Inventory Scanner - Discover and list AWS resources across services and regions",
        epilog="For more information, visit: https://github.com/yourusername/aws_inventory_scan"
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan AWS resources")
    scan_parser.add_argument('--services', '-s', nargs='+', 
                            help='Additional AWS services to scan (e.g., "apigateway" "kms" "secretsmanager")')
    scan_parser.add_argument('--output', '-o', 
                            help='Output file path (default from config)')
    scan_parser.add_argument('--verbose', '-v', action='store_true', 
                            help='Enable verbose debug output')
    scan_parser.add_argument('--region', '-r', 
                            help='Specific AWS region to scan (default: scan all regions)')
    scan_parser.add_argument('--config', '-c', 
                            help='Path to custom configuration file')
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_subparsers = config_parser.add_subparsers(dest="config_command", help="Configuration command")
    
    # Create default config
    create_config_parser = config_subparsers.add_parser("create", help="Create default configuration file")
    create_config_parser.add_argument('--path', '-p', 
                                    help='Path to save the configuration file')
    
    # Show config
    show_config_parser = config_subparsers.add_parser("show", help="Show current configuration")
    show_config_parser.add_argument('--path', '-p', 
                                  help='Path to configuration file to show')
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")
    
    return parser.parse_args(args)

def show_version():
    """Display version information."""
    print(f"AWS Inventory Scanner v{__version__}")
    print("License: GNU General Public License v3.0 (GPL-3)")
    print("https://github.com/yourusername/aws_inventory_scan")

def show_config(config_path: Optional[str] = None):
    """Show the current configuration."""
    config = get_config()
    print(json.dumps(config, indent=2))

def main():
    """Main entry point for the CLI."""
    args = parse_args(sys.argv[1:])
    
    # If no command is specified, default to scan
    if not args.command:
        args.command = "scan"
    
    # Handle different commands
    if args.command == "scan":
        # Convert CLI args to a format that scan_main expects
        sys.argv = [sys.argv[0]]
        if args.services:
            sys.argv.extend(['--services'] + args.services)
        if args.output:
            sys.argv.extend(['--output', args.output])
        if args.verbose:
            sys.argv.append('--verbose')
        if args.region:
            sys.argv.extend(['--region', args.region])
        if args.config:
            sys.argv.extend(['--config', args.config])
        
        # Run the scan
        scan_main()
    
    elif args.command == "config":
        if args.config_command == "create":
            create_default_config(args.path)
        elif args.config_command == "show":
            show_config(args.path)
        else:
            print("Please specify a config command. Use --help for more information.")
    
    elif args.command == "version":
        show_version()
    
    else:
        print(f"Unknown command: {args.command}")
        print("Use --help for more information.")

if __name__ == "__main__":
    main()
