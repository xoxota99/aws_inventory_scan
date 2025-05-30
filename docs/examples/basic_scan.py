#!/usr/bin/env python3

# This file is part of aws_inventory_scan.
#
# aws_inventory_scan is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# aws_inventory_scan is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with aws_inventory_scan. If not, see <https://www.gnu.org/licenses/>.

"""
Example: Basic AWS resource scan.

This example demonstrates how to use the AWS Inventory Scanner to perform a basic scan
of AWS resources and print the results.
"""

import json
from aws_inventory_scan.scan_aws import get_all_resource_arns

def main():
    """Run a basic AWS resource scan."""
    print("Starting AWS resource scan...")
    
    # Perform the scan
    resource_arns = get_all_resource_arns()
    
    # Print the results
    print(f"\nFound {len(resource_arns)} resources:")
    for arn in sorted(resource_arns)[:10]:  # Print first 10 for brevity
        print(arn)
    
    if len(resource_arns) > 10:
        print(f"... and {len(resource_arns) - 10} more")
    
    # Save to a file
    output_file = "scan_results.json"
    with open(output_file, 'w') as f:
        json.dump(resource_arns, f, indent=2)
    
    print(f"\nResource ARNs have been saved to {output_file}")

if __name__ == "__main__":
    main()
