"""
CloudWatch resource collector for AWS inventory scan.
"""

import time

def collect_resources(client, region, account_id, resource_arns, verbose=False):
    """Collect CloudWatch resources in a region."""
    if verbose:
        print(f"DEBUG: Starting CloudWatch resource collection in {region}")
        start_time = time.time()

    # CloudWatch Alarms
    paginator = client.get_paginator('describe_alarms')
    for page in paginator.paginate():
        for alarm in page.get('MetricAlarms', []):
            alarm_name = alarm['AlarmName']
            arn = f"arn:aws:cloudwatch:{region}:{account_id}:alarm:{alarm_name}"
            resource_arns.append(arn)
        for alarm in page.get('CompositeAlarms', []):
            alarm_name = alarm['AlarmName']
            arn = f"arn:aws:cloudwatch:{region}:{account_id}:alarm:{alarm_name}"
            resource_arns.append(arn)

    if verbose:
        print(f"DEBUG: Collected CloudWatch alarms in {region}, now collecting dashboards")

    # CloudWatch Dashboards
    response = client.list_dashboards()
    for dashboard in response.get('DashboardEntries', []):
        arn = dashboard['DashboardArn']
        resource_arns.append(arn)

    if verbose:
        elapsed = time.time() - start_time
        print(f"DEBUG: Completed CloudWatch resource collection in {region} in {elapsed:.2f}s")
