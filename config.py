#!/usr/bin/env python3

# This file is part of aws_inventory_scan.
#
# aws_inventory_scan is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# aws_inventory_scan is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with aws_inventory_scan. If not, see <https://www.gnu.org/licenses/>.

"""
Configuration module for AWS inventory scan.
Provides centralized configuration settings that can be customized.
"""

import os
import json
import logging
from pathlib import Path

# Default configuration values
DEFAULT_CONFIG = {
    # AWS settings
    "aws": {
        "default_region": "us-east-1",
        "global_services": [
            "iam", "s3", "route53", "cloudfront", "organizations",
            "waf", "shield", "budgets", "ce", "chatbot", "health"
        ],
        "default_services": [
            "ec2", "s3", "lambda", "dynamodb", "rds", "iam",
            "cloudformation", "sqs", "sns",
            "kinesisanalytics", "kinesisanalyticsv2", "cloudwatch", "logs", 
            "route53", "ecs", "kms"
        ],
        "max_threads": 10,
        "max_retries": 5,
        "initial_backoff": 1,
        "max_backoff": 60
    },
    
    # Output settings
    "output": {
        "default_output_file": "aws_resource_arns.json",
        "output_format": "json",  # Options: json, csv, text
        "pretty_print": True
    },
    
    # Logging settings
    "logging": {
        "log_level": "INFO",  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
        "log_file": "",  # Empty string means log to console only
        "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    },
    
    # Scan settings
    "scan": {
        "include_objects": True,  # For S3, whether to include objects or just buckets
        "max_objects_per_bucket": 100,  # Limit objects per bucket to avoid excessive API calls
        "scan_all_regions": True,  # Whether to scan all regions by default
        "skip_empty_services": True  # Skip services that return no resources
    }
}

# User configuration file paths to check (in order of precedence)
CONFIG_PATHS = [
    "./aws_inventory_scan.json",  # Current directory
    "~/.aws_inventory_scan.json",  # User's home directory
    "/etc/aws_inventory_scan.json"  # System-wide configuration
]

# Global configuration object
_config = None

def load_config():
    """
    Load configuration from file or use defaults.
    Checks multiple locations for configuration files.
    """
    global _config
    
    # Start with default configuration
    config = DEFAULT_CONFIG.copy()
    
    # Check for configuration files
    for path_str in CONFIG_PATHS:
        path = Path(os.path.expanduser(path_str))
        if path.exists() and path.is_file():
            try:
                with open(path, 'r') as f:
                    user_config = json.load(f)
                    # Deep merge user configuration with defaults
                    deep_merge(config, user_config)
                logging.info(f"Loaded configuration from {path}")
                break
            except Exception as e:
                logging.warning(f"Error loading configuration from {path}: {str(e)}")
    
    # Set the global configuration
    _config = config
    return config

def get_config():
    """Get the current configuration."""
    global _config
    if _config is None:
        return load_config()
    return _config

def deep_merge(base, override):
    """
    Deep merge two dictionaries.
    The override dictionary values take precedence.
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value

def create_default_config(path=None):
    """
    Create a default configuration file.
    
    Args:
        path: Path to save the configuration file. If None, uses the first path in CONFIG_PATHS.
    """
    if path is None:
        path = os.path.expanduser(CONFIG_PATHS[0])
    
    try:
        with open(path, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        print(f"Created default configuration file at {path}")
        return True
    except Exception as e:
        print(f"Error creating configuration file: {str(e)}")
        return False

def get_aws_config():
    """Get AWS-specific configuration."""
    return get_config()["aws"]

def get_output_config():
    """Get output-specific configuration."""
    return get_config()["output"]

def get_logging_config():
    """Get logging-specific configuration."""
    return get_config()["logging"]

def get_scan_config():
    """Get scan-specific configuration."""
    return get_config()["scan"]

# Initialize configuration when module is imported
load_config()
