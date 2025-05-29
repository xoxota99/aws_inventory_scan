"""
IAM resource collector for AWS inventory scan.
"""

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
        print(f"DEBUG: Collected IAM roles and users, now collecting policies")

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
        print(f"DEBUG: Collected IAM groups, now collecting instance profiles")

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
        print(f"DEBUG: Collected IAM SAML providers, now collecting server certificates")

    # IAM server certificates
    try:
        response = client.list_server_certificates()
        for cert in response.get('ServerCertificateMetadataList', []):
            arn = cert['Arn']
            resource_arns.append(arn)
    except Exception as e:
        if verbose:
            print(f"DEBUG: Error listing server certificates: {str(e)}")
        else:
            print(f"Error listing server certificates: {str(e)}")