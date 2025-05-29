"""
KMS resource collector for AWS inventory scan.
"""

def collect_resources(client, region, account_id, resource_arns, verbose=False):
    """Collect KMS resources in a region."""
    if verbose:
        print(f"DEBUG: Starting KMS resource collection in {region}")

    paginator = client.get_paginator('list_keys')
    for page in paginator.paginate():
        for key in page.get('Keys', []):
            key_id = key['KeyId']
            key_arn = key['KeyArn']
            resource_arns.append(key_arn)

            # Get aliases for each key
            try:
                if verbose:
                    print(f"DEBUG: Getting aliases for key {key_id}")
                alias_response = client.list_aliases(KeyId=key_id)
                for alias in alias_response.get('Aliases', []):
                    alias_arn = alias['AliasArn']
                    resource_arns.append(alias_arn)
            except Exception as e:
                if verbose:
                    print(f"DEBUG: Error getting aliases for key {key_id}: {str(e)}")
                else:
                    print(f"Error getting aliases for key {key_id}: {str(e)}")

    if verbose:
        print(f"DEBUG: Completed KMS resource collection in {region}")