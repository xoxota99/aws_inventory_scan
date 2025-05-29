"""
S3 resource collector for AWS inventory scan.
"""

def collect_resources(client, region, account_id, resource_arns, verbose=False):
    """Collect S3 resources."""
    # S3 buckets (global service but listing here)
    response = client.list_buckets()
    bucket_count = len(response.get('Buckets', []))
    for bucket in response.get('Buckets', []):
        bucket_name = bucket['Name']
        arn = f"arn:aws:s3:::{bucket_name}"
        resource_arns.append(arn)

        # List objects in buckets (with pagination)
        try:
            if verbose:
                print(f"DEBUG: Getting location for bucket {bucket_name}")
            # Only list objects in buckets that are in the current region or global
            bucket_region = client.get_bucket_location(Bucket=bucket_name)
            location_constraint = bucket_region.get('LocationConstraint', '')

            # Handle the special case where None means us-east-1
            if location_constraint is None:
                location_constraint = 'us-east-1'

            if location_constraint == region or location_constraint == '':
                if verbose:
                    print(f"DEBUG: Listing objects in bucket {bucket_name} (region: {location_constraint})")
                # Only list top-level objects to avoid excessive API calls
                paginator = client.get_paginator('list_objects_v2')
                for page in paginator.paginate(Bucket=bucket_name, MaxKeys=100, Delimiter='/'):
                    for obj in page.get('Contents', []):
                        arn = f"arn:aws:s3:::{bucket_name}/{obj['Key']}"
                        resource_arns.append(arn)
        except Exception as e:
            if verbose:
                print(f"DEBUG: Error listing objects in bucket {bucket_name}: {str(e)}")
            else:
                print(f"Error listing objects in bucket {bucket_name}: {str(e)}")

    if verbose:
        print(f"DEBUG: Processed {bucket_count} S3 buckets")
