#!/usr/bin/env python3

# This file is part of aws_inventory_scan.
#
# aws_inventory_scan is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# aws_inventory_scan is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with aws_inventory_scan. If not, see <https://www.gnu.org/licenses/>.

"""
EC2 resource collector for AWS inventory scan.
"""

import time
try:
    from logging_config import get_logger
    logger = get_logger()
except ImportError:
    import logging
    logger = logging.getLogger('aws_inventory_scan')

try:
    from error_handlers import safe_api_call
except ImportError:
    # Fallback if error_handlers module is not available
    def safe_api_call(client, method_name, service_name, region, verbose=False, **kwargs):
        try:
            method = getattr(client, method_name)
            return method(**kwargs)
        except Exception as e:
            if verbose:
                logger.debug(f"Error calling {method_name} for {service_name} in {region}: {str(e)}")
            return None

def collect_resources(client, region, account_id, resource_arns, verbose=False):
    """Collect EC2 resources in a region."""
    if verbose:
        logger.debug(f"Starting EC2 resource collection in {region}")
        start_time = time.time()

    # EC2 instances
    response = safe_api_call(client, 'describe_instances', 'ec2', region, verbose)
    if response:
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                instance_id = instance['InstanceId']
                arn = f"arn:aws:ec2:{region}:{account_id}:instance/{instance_id}"
                resource_arns.append(arn)

    if verbose:
        logger.debug(f"Collected EC2 instances in {region}, now collecting volumes")

    # EC2 volumes
    response = safe_api_call(client, 'describe_volumes', 'ec2', region, verbose)
    if response:
        for volume in response.get('Volumes', []):
            volume_id = volume['VolumeId']
            arn = f"arn:aws:ec2:{region}:{account_id}:volume/{volume_id}"
            resource_arns.append(arn)

    if verbose:
        logger.debug(f"Collected EC2 volumes in {region}, now collecting security groups")

    # EC2 security groups
    response = safe_api_call(client, 'describe_security_groups', 'ec2', region, verbose)
    if response:
        for sg in response.get('SecurityGroups', []):
            sg_id = sg['GroupId']
            arn = f"arn:aws:ec2:{region}:{account_id}:security-group/{sg_id}"
            resource_arns.append(arn)

    if verbose:
        logger.debug(f"Collected EC2 security groups in {region}, now collecting Elastic IPs")

    # EC2 Elastic IP Addresses
    response = safe_api_call(client, 'describe_addresses', 'ec2', region, verbose)
    if response:
        for eip in response.get('Addresses', []):
            allocation_id = eip.get('AllocationId')
            if allocation_id:
                arn = f"arn:aws:ec2:{region}:{account_id}:elastic-ip/{allocation_id}"
                resource_arns.append(arn)

    if verbose:
        logger.debug(f"Collected EC2 Elastic IPs in {region}, now collecting VPCs")

    # EC2 VPC resources
    # VPCs
    response = safe_api_call(client, 'describe_vpcs', 'ec2', region, verbose)
    if response:
        for vpc in response.get('Vpcs', []):
            vpc_id = vpc['VpcId']
            arn = f"arn:aws:ec2:{region}:{account_id}:vpc/{vpc_id}"
            resource_arns.append(arn)

    if verbose:
        logger.debug(f"Collected EC2 VPCs in {region}, now collecting subnets")

    # Subnets
    response = safe_api_call(client, 'describe_subnets', 'ec2', region, verbose)
    if response:
        for subnet in response.get('Subnets', []):
            subnet_id = subnet['SubnetId']
            arn = f"arn:aws:ec2:{region}:{account_id}:subnet/{subnet_id}"
            resource_arns.append(arn)

    if verbose:
        logger.debug(f"Collected EC2 subnets in {region}, now collecting route tables")

    # Route Tables
    response = safe_api_call(client, 'describe_route_tables', 'ec2', region, verbose)
    if response:
        for rt in response.get('RouteTables', []):
            rt_id = rt['RouteTableId']
            arn = f"arn:aws:ec2:{region}:{account_id}:route-table/{rt_id}"
            resource_arns.append(arn)

    if verbose:
        logger.debug(f"Collected EC2 route tables in {region}, now collecting NACLs")

    # Network ACLs
    response = safe_api_call(client, 'describe_network_acls', 'ec2', region, verbose)
    if response:
        for nacl in response.get('NetworkAcls', []):
            nacl_id = nacl['NetworkAclId']
            arn = f"arn:aws:ec2:{region}:{account_id}:network-acl/{nacl_id}"
            resource_arns.append(arn)

    if verbose:
        logger.debug(f"Collected EC2 NACLs in {region}, now collecting internet gateways")

    # Internet Gateways
    response = safe_api_call(client, 'describe_internet_gateways', 'ec2', region, verbose)
    if response:
        for igw in response.get('InternetGateways', []):
            igw_id = igw['InternetGatewayId']
            arn = f"arn:aws:ec2:{region}:{account_id}:internet-gateway/{igw_id}"
            resource_arns.append(arn)

    if verbose:
        logger.debug(f"Collected EC2 internet gateways in {region}, now collecting NAT gateways")

    # NAT Gateways
    response = safe_api_call(client, 'describe_nat_gateways', 'ec2', region, verbose)
    if response:
        for nat in response.get('NatGateways', []):
            nat_id = nat['NatGatewayId']
            arn = f"arn:aws:ec2:{region}:{account_id}:nat-gateway/{nat_id}"
            resource_arns.append(arn)

    if verbose:
        logger.debug(f"Collected EC2 NAT gateways in {region}, now collecting network interfaces")

    # Elastic Network Interfaces
    response = safe_api_call(client, 'describe_network_interfaces', 'ec2', region, verbose)
    if response:
        for eni in response.get('NetworkInterfaces', []):
            eni_id = eni['NetworkInterfaceId']
            arn = f"arn:aws:ec2:{region}:{account_id}:network-interface/{eni_id}"
            resource_arns.append(arn)

    if verbose:
        logger.debug(f"Collected EC2 network interfaces in {region}, now collecting transit gateways")

    # Transit Gateways
    response = safe_api_call(client, 'describe_transit_gateways', 'ec2', region, verbose)
    if response:
        for tgw in response.get('TransitGateways', []):
            arn = tgw.get('TransitGatewayArn')
            if arn:
                resource_arns.append(arn)

    if verbose:
        elapsed = time.time() - start_time
        logger.debug(f"Completed EC2 resource collection in {region} in {elapsed:.2f}s")
