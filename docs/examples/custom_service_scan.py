#!/usr/bin/env python3

# This file is part of aws_inventory_scan.
#
# aws_inventory_scan is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# aws_inventory_scan is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with aws_inventory_scan. If not, see <https://www.gnu.org/licenses/>.

"""
Example: Custom service scan.

This example demonstrates how to scan specific AWS services in a specific region.
"""

import json
from aws_inventory_scan.scan_aws import get_all_resource_arns

def main():
    """Run a custom AWS resource scan for specific services in a specific region."""
    print("Starting custom AWS resource scan...")
    
    # Define the services to scan
    additional_services = [
        "apigateway",
        "lambda",
        "dynamodb",
        "s3",
        "ec2"
    ]
    
    # Define the region to scan
    region = "us-west-2"
    
    # Enable verbose output
    verbose = True
    
    print(f"Scanning services: {', '.join(additional_services)}")
    print(f"Region: {region}")
    
    # Perform the scan
    resource_arns = get_all_resource_arns(
        additional_services=additional_services,
        specific_region=region,
        verbose=verbose
    )
    
    # Print the results
    print(f"\nFound {len(resource_arns)} resources:")
    
    # Group by service
    services = {}
    for arn in resource_arns:
        service = arn.split(":")[2]
        if service not in services:
            services[service] = []
        services[service].append(arn)
    
    # Print count by service
    for service, arns in services.items():
        print(f"{service}: {len(arns)} resources")
    
    # Save to a file
    output_file = f"scan_results_{region}.json"
    with open(output_file, 'w') as f:
        json.dump(resource_arns, f, indent=2)
    
    print(f"\nResource ARNs have been saved to {output_file}")

if __name__ == "__main__":
    main()
