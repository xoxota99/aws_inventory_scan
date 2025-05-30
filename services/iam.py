# This file is part of aws_inventory_scan.
#
# aws_inventory_scan is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# aws_inventory_scan is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with aws_inventory_scan. If not, see <https://www.gnu.org/licenses/>.

"""
IAM resource collector for AWS inventory scan.
"""

try:
    from logging_config import get_logger
    logger = get_logger()
except ImportError:
    import logging
    logger = logging.getLogger('aws_inventory_scan')

def collect_resources(client, region, account_id, resource_arns, verbose=False):
    """Collect IAM resources (global service)."""
    # IAM roles
    response = client.list_roles()
    for role in response.get('Roles', []):
        arn = role['Arn']
        resource_arns.append(arn)

    # IAM users
    response = client.list_users()
    for user in response.get('Users', []):
        arn = user['Arn']
        resource_arns.append(arn)

    if verbose:
        logger.debug(f"Collected IAM roles and users, now collecting policies")

    # IAM policies
    response = client.list_policies(Scope='Local')
    for policy in response.get('Policies', []):
        arn = policy['Arn']
        resource_arns.append(arn)

    # IAM groups
    response = client.list_groups()
    for group in response.get('Groups', []):
        arn = group['Arn']
        resource_arns.append(arn)

    if verbose:
        logger.debug(f"Collected IAM groups, now collecting instance profiles")

    # IAM instance profiles
    response = client.list_instance_profiles()
    for profile in response.get('InstanceProfiles', []):
        arn = profile['Arn']
        resource_arns.append(arn)

    # IAM SAML providers
    response = client.list_saml_providers()
    for provider in response.get('SAMLProviderList', []):
        arn = provider['Arn']
        resource_arns.append(arn)

    if verbose:
        logger.debug(f"Collected IAM SAML providers, now collecting server certificates")

    # IAM server certificates
    try:
        response = client.list_server_certificates()
        for cert in response.get('ServerCertificateMetadataList', []):
            arn = cert['Arn']
            resource_arns.append(arn)
    except Exception as e:
        if verbose:
            logger.debug(f"Error listing server certificates: {str(e)}")
        else:
            print(f"Error listing server certificates: {str(e)}")