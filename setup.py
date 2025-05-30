#!/usr/bin/env python3

from setuptools import setup, find_packages

# Read the content of README.md for the long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements from requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as f:
    # Filter out comments and optional dev dependencies
    requirements = [
        line.strip() for line in f 
        if line.strip() and not line.startswith("#") and not line.startswith("pytest") 
        and not line.startswith("flake8") and not line.startswith("black")
    ]

setup(
    name="aws_inventory_scan",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A comprehensive tool for scanning and inventorying AWS resources",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/aws_inventory_scan",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "aws-inventory-scan=aws_inventory_scan.scan_aws:main",
        ],
    },
    include_package_data=True,
    keywords="aws, cloud, inventory, scanner, resources, arn",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/aws_inventory_scan/issues",
        "Source": "https://github.com/yourusername/aws_inventory_scan",
    },
)
