"""
CloudWatch Logs resource collector for AWS inventory scan.
"""

def collect_resources(client, region, account_id, resource_arns, verbose=False):
    """Collect CloudWatch Logs resources in a region."""
    # CloudWatch Log Groups
    paginator = client.get_paginator('describe_log_groups')
    for page in paginator.paginate():
        for log_group in page.get('logGroups', []):
            arn = log_group.get('arn')
            if not arn:  # If ARN is not directly provided, construct it
                log_group_name = log_group['logGroupName']
                arn = f"arn:aws:logs:{region}:{account_id}:log-group:{log_group_name}"
            resource_arns.append(arn)

    if verbose:
        print(f"DEBUG: Collected CloudWatch Log Groups in {region}")
