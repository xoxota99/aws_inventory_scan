#!/usr/bin/env python3

# This file is part of aws_inventory_scan.
#
# aws_inventory_scan is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# aws_inventory_scan is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with aws_inventory_scan. If not, see <https://www.gnu.org/licenses/>.

"""
Output formatters for AWS inventory scan.
Provides functions to format and save scan results in different formats.
"""

import json
import csv
import os
from typing import List, Dict, Any, Optional, TextIO

def save_as_json(resource_arns: List[str], output_file: str, pretty_print: bool = True) -> None:
    """
    Save resource ARNs as JSON.
    
    Args:
        resource_arns: List of resource ARNs to save
        output_file: Path to output file
        pretty_print: Whether to format JSON with indentation
    """
    with open(output_file, 'w') as f:
        if pretty_print:
            json.dump(resource_arns, f, indent=2)
        else:
            json.dump(resource_arns, f)

def save_as_csv(resource_arns: List[str], output_file: str) -> None:
    """
    Save resource ARNs as CSV.
    
    Args:
        resource_arns: List of resource ARNs to save
        output_file: Path to output file
    """
    # Parse ARNs to extract service, region, account, and resource
    parsed_arns = []
    for arn in resource_arns:
        parts = arn.split(':')
        if len(parts) >= 6:
            parsed_arns.append({
                'arn': arn,
                'partition': parts[1],
                'service': parts[2],
                'region': parts[3],
                'account': parts[4],
                'resource': ':'.join(parts[5:]) if len(parts) > 6 else parts[5]
            })
        else:
            # Handle malformed ARNs
            parsed_arns.append({
                'arn': arn,
                'partition': '',
                'service': '',
                'region': '',
                'account': '',
                'resource': ''
            })
    
    # Write to CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['arn', 'partition', 'service', 'region', 'account', 'resource'])
        writer.writeheader()
        writer.writerows(parsed_arns)

def save_as_text(resource_arns: List[str], output_file: str) -> None:
    """
    Save resource ARNs as plain text.
    
    Args:
        resource_arns: List of resource ARNs to save
        output_file: Path to output file
    """
    with open(output_file, 'w') as f:
        for arn in sorted(resource_arns):
            f.write(f"{arn}\n")

def save_results(resource_arns: List[str], output_file: str, output_format: str = 'json', pretty_print: bool = True) -> None:
    """
    Save resource ARNs in the specified format.
    
    Args:
        resource_arns: List of resource ARNs to save
        output_file: Path to output file
        output_format: Format to save as ('json', 'csv', or 'text')
        pretty_print: Whether to format JSON with indentation
    """
    # Ensure the output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save in the specified format
    if output_format.lower() == 'csv':
        save_as_csv(resource_arns, output_file)
    elif output_format.lower() == 'text':
        save_as_text(resource_arns, output_file)
    else:
        # Default to JSON
        save_as_json(resource_arns, output_file, pretty_print)
