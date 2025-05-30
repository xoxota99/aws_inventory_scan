#!/usr/bin/env python3

# This file is part of aws_inventory_scan.
#
# aws_inventory_scan is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# aws_inventory_scan is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with aws_inventory_scan. If not, see <https://www.gnu.org/licenses/>.

"""
Example: Working with configuration.

This example demonstrates how to work with the configuration system.
"""

import json
import os
from aws_inventory_scan.config import (
    get_config, create_default_config, get_aws_config,
    get_output_config, get_logging_config, get_scan_config
)

def main():
    """Demonstrate configuration functionality."""
    print("AWS Inventory Scanner Configuration Example")
    print("=========================================\n")
    
    # Create a default configuration file
    config_path = "example_config.json"
    print(f"Creating default configuration file at {config_path}...")
    create_default_config(config_path)
    
    # Load and display the configuration
    print("\nLoading configuration...")
    config = get_config()
    
    print("\nFull configuration:")
    print(json.dumps(config, indent=2))
    
    # Access specific configuration sections
    print("\nAWS configuration:")
    aws_config = get_aws_config()
    print(f"Default region: {aws_config['default_region']}")
    print(f"Max threads: {aws_config['max_threads']}")
    
    print("\nOutput configuration:")
    output_config = get_output_config()
    print(f"Default output file: {output_config['default_output_file']}")
    print(f"Pretty print: {output_config['pretty_print']}")
    
    # Modify the configuration
    print("\nModifying configuration...")
    with open(config_path, 'r') as f:
        custom_config = json.load(f)
    
    custom_config["aws"]["max_threads"] = 10
    custom_config["output"]["pretty_print"] = False
    
    with open(config_path, 'w') as f:
        json.dump(custom_config, f, indent=2)
    
    print("Configuration modified.")
    
    # Clean up
    print("\nCleaning up...")
    os.remove(config_path)
    print(f"Removed {config_path}")

if __name__ == "__main__":
    main()
