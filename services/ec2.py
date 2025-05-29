"""
EC2 resource collector for AWS inventory scan.
"""

import time

def collect_resources(client, region, account_id, resource_arns, verbose=False):
    """Collect EC2 resources in a region."""
    if verbose:
        print(f"DEBUG: Starting EC2 resource collection in {region}")
        start_time = time.time()

    # EC2 instances
    response = client.describe_instances()
    for reservation in response.get('Reservations', []):
        for instance in reservation.get('Instances', []):
            instance_id = instance['InstanceId']
            arn = f"arn:aws:ec2:{region}:{account_id}:instance/{instance_id}"
            resource_arns.append(arn)

    if verbose:
        print(f"DEBUG: Collected EC2 instances in {region}, now collecting volumes")

    # EC2 volumes
    response = client.describe_volumes()
    for volume in response.get('Volumes', []):
        volume_id = volume['VolumeId']
        arn = f"arn:aws:ec2:{region}:{account_id}:volume/{volume_id}"
        resource_arns.append(arn)

    if verbose:
        print(f"DEBUG: Collected EC2 volumes in {region}, now collecting security groups")

    # EC2 security groups
    response = client.describe_security_groups()
    for sg in response.get('SecurityGroups', []):
        sg_id = sg['GroupId']
        arn = f"arn:aws:ec2:{region}:{account_id}:security-group/{sg_id}"
        resource_arns.append(arn)

    if verbose:
        print(f"DEBUG: Collected EC2 security groups in {region}, now collecting Elastic IPs")

    # EC2 Elastic IP Addresses
    response = client.describe_addresses()
    for eip in response.get('Addresses', []):
        allocation_id = eip.get('AllocationId')
        if allocation_id:
            arn = f"arn:aws:ec2:{region}:{account_id}:elastic-ip/{allocation_id}"
            resource_arns.append(arn)

    if verbose:
        print(f"DEBUG: Collected EC2 Elastic IPs in {region}, now collecting VPCs")

    # EC2 VPC resources
    # VPCs
    response = client.describe_vpcs()
    for vpc in response.get('Vpcs', []):
        vpc_id = vpc['VpcId']
        arn = f"arn:aws:ec2:{region}:{account_id}:vpc/{vpc_id}"
        resource_arns.append(arn)

    if verbose:
        print(f"DEBUG: Collected EC2 VPCs in {region}, now collecting subnets")

    # Subnets
    response = client.describe_subnets()
    for subnet in response.get('Subnets', []):
        subnet_id = subnet['SubnetId']
        arn = f"arn:aws:ec2:{region}:{account_id}:subnet/{subnet_id}"
        resource_arns.append(arn)

    if verbose:
        print(f"DEBUG: Collected EC2 subnets in {region}, now collecting route tables")

    # Route Tables
    response = client.describe_route_tables()
    for rt in response.get('RouteTables', []):
        rt_id = rt['RouteTableId']
        arn = f"arn:aws:ec2:{region}:{account_id}:route-table/{rt_id}"
        resource_arns.append(arn)

    if verbose:
        print(f"DEBUG: Collected EC2 route tables in {region}, now collecting NACLs")

    # Network ACLs
    response = client.describe_network_acls()
    for nacl in response.get('NetworkAcls', []):
        nacl_id = nacl['NetworkAclId']
        arn = f"arn:aws:ec2:{region}:{account_id}:network-acl/{nacl_id}"
        resource_arns.append(arn)

    if verbose:
        print(f"DEBUG: Collected EC2 NACLs in {region}, now collecting internet gateways")

    # Internet Gateways
    response = client.describe_internet_gateways()
    for igw in response.get('InternetGateways', []):
        igw_id = igw['InternetGatewayId']
        arn = f"arn:aws:ec2:{region}:{account_id}:internet-gateway/{igw_id}"
        resource_arns.append(arn)

    if verbose:
        print(f"DEBUG: Collected EC2 internet gateways in {region}, now collecting NAT gateways")

    # NAT Gateways
    response = client.describe_nat_gateways()
    for nat in response.get('NatGateways', []):
        nat_id = nat['NatGatewayId']
        arn = f"arn:aws:ec2:{region}:{account_id}:nat-gateway/{nat_id}"
        resource_arns.append(arn)

    if verbose:
        print(f"DEBUG: Collected EC2 NAT gateways in {region}, now collecting network interfaces")

    # Elastic Network Interfaces
    response = client.describe_network_interfaces()
    for eni in response.get('NetworkInterfaces', []):
        eni_id = eni['NetworkInterfaceId']
        arn = f"arn:aws:ec2:{region}:{account_id}:network-interface/{eni_id}"
        resource_arns.append(arn)

    if verbose:
        print(f"DEBUG: Collected EC2 network interfaces in {region}, now collecting transit gateways")

    # Transit Gateways
    try:
        response = client.describe_transit_gateways()
        for tgw in response.get('TransitGateways', []):
            arn = tgw.get('TransitGatewayArn')
            if arn:
                resource_arns.append(arn)
    except Exception as e:
        if verbose:
            print(f"DEBUG: Error getting transit gateways in {region}: {str(e)}")
        else:
            print(f"Error getting transit gateways: {str(e)}")

    if verbose:
        elapsed = time.time() - start_time
        print(f"DEBUG: Completed EC2 resource collection in {region} in {elapsed:.2f}s")
