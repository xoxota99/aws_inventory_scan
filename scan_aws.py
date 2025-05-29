#!/usr/bin/env python3

import boto3
import json
from botocore.exceptions import ClientError
import argparse
import concurrent.futures

# Default region for global services
default_region = 'us-east-1'

def get_all_regions():
    """Get all available AWS regions."""
    ec2_client = boto3.client('ec2', region_name=default_region)  # Specify a default region
    regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
    return regions

def get_account_id():
    """Get the current AWS account ID."""
    try:
        sts_client = boto3.client('sts', region_name=default_region)  # Specify the region explicitly
        return sts_client.get_caller_identity()["Account"]
    except ClientError as e:
        if 'ExpiredToken' in str(e) or 'InvalidClientTokenId' in str(e) or 'AccessDenied' in str(e):
            print("Error: AWS authentication failed. Please check your credentials and try again.")
            print("Make sure you have valid AWS credentials configured via AWS CLI, environment variables, or IAM role.")
            print(f"Specific error: {str(e)}")
            exit(1)
        else:
            print(f"Unexpected error when authenticating: {str(e)}")
            exit(1)

# Service-specific resource collection functions
def get_service_resources(client, service_name, region, account_id):
    """Get resources for a specific service using appropriate API calls."""
    resources = []

    # Dictionary mapping services to their list/describe methods and ARN formats
    service_mappings = {
        # Format: 'service_name': {'method': 'api_method_name', 'key': 'response_key_for_resources', 'id_attr': 'id_attribute', 'arn_format': 'arn_format_string'}
        'accessanalyzer': {'method': 'list_analyzers', 'key': 'analyzers', 'arn_attr': 'arn'},
        'acm': {'method': 'list_certificates', 'key': 'CertificateSummaryList', 'id_attr': 'CertificateArn', 'arn_attr': 'CertificateArn'},
        'acm-pca': {'method': 'list_certificate_authorities', 'key': 'CertificateAuthorities', 'arn_attr': 'Arn'},
        'amp': {'method': 'list_workspaces', 'key': 'workspaces', 'arn_attr': 'arn'},
        'amplify': {'method': 'list_apps', 'key': 'apps', 'arn_attr': 'appArn'},
        'apigateway': {'method': 'get_rest_apis', 'key': 'items', 'id_attr': 'id', 'arn_format': 'arn:aws:apigateway:{region}::/restapis/{id}'},
        'apigatewayv2': {'method': 'get_apis', 'key': 'Items', 'id_attr': 'ApiId', 'arn_format': 'arn:aws:apigateway:{region}::/apis/{id}'},
        'appconfig': {'method': 'list_applications', 'key': 'Items', 'id_attr': 'Id', 'arn_format': 'arn:aws:appconfig:{region}:{account_id}:application/{id}'},
        'appflow': {'method': 'list_flows', 'key': 'flows', 'arn_attr': 'flowArn'},
        'apprunner': {'method': 'list_services', 'key': 'ServiceSummaryList', 'arn_attr': 'ServiceArn'},
        'appstream': {'method': 'describe_fleets', 'key': 'Fleets', 'arn_attr': 'Arn'},
        'appsync': {'method': 'list_graphql_apis', 'key': 'graphqlApis', 'arn_attr': 'arn'},
        'athena': {'method': 'list_work_groups', 'key': 'WorkGroups', 'id_attr': 'Name', 'arn_format': 'arn:aws:athena:{region}:{account_id}:workgroup/{id}'},
        'auditmanager': {'method': 'list_assessments', 'key': 'assessmentMetadata', 'arn_attr': 'arn'},
        'autoscaling': {'method': 'describe_auto_scaling_groups', 'key': 'AutoScalingGroups', 'arn_attr': 'AutoScalingGroupARN'},
        'backup': {'method': 'list_backup_vaults', 'key': 'BackupVaultList', 'arn_attr': 'BackupVaultArn'},
        'batch': {'method': 'describe_job_queues', 'key': 'jobQueues', 'arn_attr': 'jobQueueArn'},
        'bedrock': {'method': 'list_custom_models', 'key': 'modelSummaries', 'arn_attr': 'modelArn'},
        'ce': {'method': 'get_cost_and_usage', 'key': 'ResultsByTime', 'custom': True},  # Requires special handling
        'chime': {'method': 'list_accounts', 'key': 'Accounts', 'arn_attr': 'AccountId', 'arn_format': 'arn:aws:chime::{account_id}:account/{id}'},
        'cloud9': {'method': 'list_environments', 'key': 'environmentIds', 'id_list': True, 'arn_format': 'arn:aws:cloud9:{region}:{account_id}:environment/{id}'},
        'cloudfront': {'method': 'list_distributions', 'key': 'DistributionList.Items', 'arn_attr': 'ARN'},
        'cloudhsm': {'method': 'list_hsms', 'key': 'HsmList', 'id_attr': 'HsmArn', 'arn_attr': 'HsmArn'},
        'cloudsearch': {'method': 'describe_domains', 'key': 'DomainStatusList', 'arn_attr': 'ARN'},
        'cloudformation': {'method': 'list_stacks', 'key': 'StackSummaries', 'arn_attr': 'StackId'},
        'cloudwatch': {'method': 'list_metrics', 'key': 'Metrics', 'custom': True},  # Requires special handling
        'codeartifact': {'method': 'list_domains', 'key': 'domains', 'id_attr': 'name', 'arn_format': 'arn:aws:codeartifact:{region}:{account_id}:domain/{id}'},
        'codebuild': {'method': 'list_projects', 'key': 'projects', 'id_list': True, 'arn_format': 'arn:aws:codebuild:{region}:{account_id}:project/{id}'},
        'codecommit': {'method': 'list_repositories', 'key': 'repositories', 'arn_attr': 'repositoryId', 'arn_format': 'arn:aws:codecommit:{region}:{account_id}:repository/{id}'},
        'codedeploy': {'method': 'list_applications', 'key': 'applications', 'id_list': True, 'arn_format': 'arn:aws:codedeploy:{region}:{account_id}:application:{id}'},
        'codepipeline': {'method': 'list_pipelines', 'key': 'pipelines', 'id_attr': 'name', 'arn_format': 'arn:aws:codepipeline:{region}:{account_id}:{id}'},
        'cognito-identity': {'method': 'list_identity_pools', 'key': 'IdentityPools', 'id_attr': 'IdentityPoolId', 'arn_format': 'arn:aws:cognito-identity:{region}:{account_id}:identitypool/{id}'},
        'cognito-idp': {'method': 'list_user_pools', 'key': 'UserPools', 'id_attr': 'Id', 'arn_format': 'arn:aws:cognito-idp:{region}:{account_id}:userpool/{id}'},
        'comprehend': {'method': 'list_document_classifiers', 'key': 'DocumentClassifierPropertiesList', 'arn_attr': 'DocumentClassifierArn'},
        'config': {'method': 'describe_config_rules', 'key': 'ConfigRules', 'arn_attr': 'ConfigRuleArn'},
        'connect': {'method': 'list_instances', 'key': 'InstanceSummaryList', 'id_attr': 'Id', 'arn_format': 'arn:aws:connect:{region}:{account_id}:instance/{id}'},
        'datasync': {'method': 'list_tasks', 'key': 'Tasks', 'arn_attr': 'TaskArn'},
        'dax': {'method': 'describe_clusters', 'key': 'Clusters', 'arn_attr': 'ClusterArn'},
        'detective': {'method': 'list_graphs', 'key': 'GraphList', 'arn_attr': 'Arn'},
        'devicefarm': {'method': 'list_projects', 'key': 'projects', 'arn_attr': 'arn'},
        'directconnect': {'method': 'describe_connections', 'key': 'connections', 'id_attr': 'connectionId', 'arn_format': 'arn:aws:directconnect:{region}:{account_id}:dxcon/{id}'},
        'dlm': {'method': 'get_lifecycle_policies', 'key': 'Policies', 'id_attr': 'PolicyId', 'arn_format': 'arn:aws:dlm:{region}:{account_id}:policy/{id}'},
        'dms': {'method': 'describe_replication_instances', 'key': 'ReplicationInstances', 'arn_attr': 'ReplicationInstanceArn'},
        'docdb': {'method': 'describe_db_clusters', 'key': 'DBClusters', 'arn_attr': 'DBClusterArn'},
        'ds': {'method': 'describe_directories', 'key': 'DirectoryDescriptions', 'id_attr': 'DirectoryId', 'arn_format': 'arn:aws:ds:{region}:{account_id}:directory/{id}'},
        'dynamodb': {'method': 'list_tables', 'key': 'TableNames', 'id_list': True, 'arn_format': 'arn:aws:dynamodb:{region}:{account_id}:table/{id}'},
        'eks': {'method': 'list_clusters', 'key': 'clusters', 'id_list': True, 'arn_format': 'arn:aws:eks:{region}:{account_id}:cluster/{id}'},
        'elasticache': {'method': 'describe_cache_clusters', 'key': 'CacheClusters', 'arn_attr': 'ARN'},
        'elasticbeanstalk': {'method': 'describe_applications', 'key': 'Applications', 'id_attr': 'ApplicationName', 'arn_format': 'arn:aws:elasticbeanstalk:{region}:{account_id}:application/{id}'},
        'elastictranscoder': {'method': 'list_pipelines', 'key': 'Pipelines', 'id_attr': 'Id', 'arn_format': 'arn:aws:elastictranscoder:{region}:{account_id}:pipeline/{id}'},
        'elb': {'method': 'describe_load_balancers', 'key': 'LoadBalancerDescriptions', 'id_attr': 'LoadBalancerName', 'arn_format': 'arn:aws:elasticloadbalancing:{region}:{account_id}:loadbalancer/{id}'},
        'elbv2': {'method': 'describe_load_balancers', 'key': 'LoadBalancers', 'arn_attr': 'LoadBalancerArn'},
        'emr': {'method': 'list_clusters', 'key': 'Clusters', 'id_attr': 'Id', 'arn_format': 'arn:aws:elasticmapreduce:{region}:{account_id}:cluster/{id}'},
        'es': {'method': 'list_domain_names', 'key': 'DomainNames', 'id_attr': 'DomainName', 'arn_format': 'arn:aws:es:{region}:{account_id}:domain/{id}'},
        'events': {'method': 'list_event_buses', 'key': 'EventBuses', 'arn_attr': 'Arn'},
        'firehose': {'method': 'list_delivery_streams', 'key': 'DeliveryStreamNames', 'id_list': True, 'arn_format': 'arn:aws:firehose:{region}:{account_id}:deliverystream/{id}'},
        'fsx': {'method': 'describe_file_systems', 'key': 'FileSystems', 'arn_attr': 'ResourceARN'},
        'gamelift': {'method': 'list_fleets', 'key': 'FleetIds', 'id_list': True, 'arn_format': 'arn:aws:gamelift:{region}:{account_id}:fleet/{id}'},
        'glacier': {'method': 'list_vaults', 'key': 'VaultList', 'arn_attr': 'VaultARN'},
        'glue': {'method': 'get_databases', 'key': 'DatabaseList', 'id_attr': 'Name', 'arn_format': 'arn:aws:glue:{region}:{account_id}:database/{id}'},
        'greengrass': {'method': 'list_groups', 'key': 'Groups', 'id_attr': 'Id', 'arn_format': 'arn:aws:greengrass:{region}:{account_id}:/greengrass/groups/{id}'},
        'guardduty': {'method': 'list_detectors', 'key': 'DetectorIds', 'id_list': True, 'arn_format': 'arn:aws:guardduty:{region}:{account_id}:detector/{id}'},
        'health': {'method': 'describe_events', 'key': 'events', 'custom': True},  # Requires special handling
        'imagebuilder': {'method': 'list_image_pipelines', 'key': 'imagePipelineList', 'arn_attr': 'arn'},
        'inspector': {'method': 'list_assessment_templates', 'key': 'assessmentTemplateArns', 'arn_list': True},
        'inspector2': {'method': 'list_findings', 'key': 'findings', 'arn_attr': 'findingArn'},
        'iot': {'method': 'list_things', 'key': 'things', 'id_attr': 'thingName', 'arn_format': 'arn:aws:iot:{region}:{account_id}:thing/{id}'},
        'kafka': {'method': 'list_clusters', 'key': 'ClusterInfoList', 'arn_attr': 'ClusterArn'},
        'kendra': {'method': 'list_indices', 'key': 'IndexConfigurationSummaryItems', 'id_attr': 'Id', 'arn_format': 'arn:aws:kendra:{region}:{account_id}:index/{id}'},
        'keyspaces': {'method': 'list_keyspaces', 'key': 'keyspaces', 'id_attr': 'keyspaceName', 'arn_format': 'arn:aws:cassandra:{region}:{account_id}:/keyspace/{id}'},
        'kinesis': {'method': 'list_streams', 'key': 'StreamNames', 'id_list': True, 'arn_format': 'arn:aws:kinesis:{region}:{account_id}:stream/{id}'},
        'kinesisvideo': {'method': 'list_streams', 'key': 'StreamInfoList', 'arn_attr': 'StreamARN'},
        'kinesisanalytics': {'method': 'list_applications', 'key': 'ApplicationSummaries', 'id_attr': 'ApplicationName', 'arn_format': 'arn:aws:kinesisanalytics:{region}:{account_id}:application/{id}'},
        'kinesisanalyticsv2': {'method': 'list_applications', 'key': 'ApplicationSummaries', 'id_attr': 'ApplicationName', 'arn_format': 'arn:aws:kinesisanalytics:{region}:{account_id}:application/KinesisAnalyticsApplication/{id}'},
        'lambda': {'method': 'list_functions', 'key': 'Functions', 'arn_attr': 'FunctionArn'},
        'kms': {'method': 'list_keys', 'key': 'Keys', 'id_attr': 'KeyId', 'arn_format': 'arn:aws:kms:{region}:{account_id}:key/{id}'},
        'lakeformation': {'method': 'list_resources', 'key': 'ResourceInfoList', 'arn_attr': 'ResourceArn'},
        'lex-models': {'method': 'get_bots', 'key': 'bots', 'id_attr': 'name', 'arn_format': 'arn:aws:lex:{region}:{account_id}:bot:{id}'},
        'lightsail': {'method': 'get_instances', 'key': 'instances', 'arn_attr': 'arn'},
        'logs': {'method': 'describe_log_groups', 'key': 'logGroups', 'arn_attr': 'arn'},
        'mediaconvert': {'method': 'list_queues', 'key': 'Queues', 'arn_attr': 'Arn'},
        'mediapackage': {'method': 'list_channels', 'key': 'Channels', 'id_attr': 'Id', 'arn_format': 'arn:aws:mediapackage:{region}:{account_id}:channels/{id}'},
        'mediatailor': {'method': 'list_playback_configurations', 'key': 'Items', 'id_attr': 'Name', 'arn_format': 'arn:aws:mediatailor:{region}:{account_id}:playbackConfiguration/{id}'},
        'memorydb': {'method': 'describe_clusters', 'key': 'Clusters', 'arn_attr': 'ARN'},
        'mq': {'method': 'list_brokers', 'key': 'BrokerSummaries', 'id_attr': 'BrokerId', 'arn_format': 'arn:aws:mq:{region}:{account_id}:broker:{id}'},
        'neptune': {'method': 'describe_db_clusters', 'key': 'DBClusters', 'arn_attr': 'DBClusterArn'},
        'network-firewall': {'method': 'list_firewalls', 'key': 'Firewalls', 'arn_attr': 'FirewallArn'},
        'networkmanager': {'method': 'describe_global_networks', 'key': 'GlobalNetworks', 'arn_attr': 'GlobalNetworkArn'},
        'opensearch': {'method': 'list_domain_names', 'key': 'DomainNames', 'id_attr': 'DomainName', 'arn_format': 'arn:aws:es:{region}:{account_id}:domain/{id}'},
        'opsworks': {'method': 'describe_stacks', 'key': 'Stacks', 'arn_attr': 'Arn'},
        'organizations': {'method': 'list_accounts', 'key': 'Accounts', 'id_attr': 'Id', 'arn_format': 'arn:aws:organizations::{account_id}:account/{id}'},
        'pinpoint': {'method': 'get_apps', 'key': 'ApplicationsResponse.Item', 'id_attr': 'Id', 'arn_format': 'arn:aws:mobiletargeting:{region}:{account_id}:apps/{id}'},
        'polly': {'method': 'list_lexicons', 'key': 'Lexicons', 'id_attr': 'Name', 'arn_format': 'arn:aws:polly:{region}:{account_id}:lexicon/{id}'},
        'qldb': {'method': 'list_ledgers', 'key': 'Ledgers', 'id_attr': 'Name', 'arn_format': 'arn:aws:qldb:{region}:{account_id}:ledger/{id}'},
        'quicksight': {'method': 'list_dashboards', 'key': 'DashboardSummaryList', 'arn_attr': 'Arn'},
        'ram': {'method': 'list_resources', 'key': 'resources', 'arn_attr': 'arn'},
        'redshift': {'method': 'describe_clusters', 'key': 'Clusters', 'arn_attr': 'ClusterNamespaceArn'},
        'rds': {'method': 'describe_db_instances', 'key': 'DBInstances', 'arn_attr': 'DBInstanceArn'},
        'rekognition': {'method': 'list_collections', 'key': 'CollectionIds', 'id_list': True, 'arn_format': 'arn:aws:rekognition:{region}:{account_id}:collection/{id}'},
        'resource-groups': {'method': 'list_groups', 'key': 'Groups', 'arn_attr': 'GroupArn'},
        'robomaker': {'method': 'list_robot_applications', 'key': 'robotApplicationSummaries', 'arn_attr': 'arn'},
        'route53': {'method': 'list_hosted_zones', 'key': 'HostedZones', 'id_attr': 'Id', 'arn_format': 'arn:aws:route53:::{id}'},
        'route53resolver': {'method': 'list_resolver_endpoints', 'key': 'ResolverEndpoints', 'id_attr': 'Id', 'arn_format': 'arn:aws:route53resolver:{region}:{account_id}:resolver-endpoint/{id}'},
        'sagemaker': {'method': 'list_models', 'key': 'Models', 'id_attr': 'ModelName', 'arn_format': 'arn:aws:sagemaker:{region}:{account_id}:model/{id}'},
        'schemas': {'method': 'list_registries', 'key': 'Registries', 'arn_attr': 'RegistryArn'},
        'secretsmanager': {'method': 'list_secrets', 'key': 'SecretList', 'arn_attr': 'ARN'},
        'securityhub': {'method': 'describe_hub', 'key': 'HubArn', 'direct_arn': True},
        'serverlessrepo': {'method': 'list_applications', 'key': 'Applications', 'arn_attr': 'ApplicationId', 'arn_format': 'arn:aws:serverlessrepo:{region}:{account_id}:applications/{id}'},
        'servicecatalog': {'method': 'list_portfolios', 'key': 'PortfolioDetails', 'id_attr': 'Id', 'arn_format': 'arn:aws:catalog:{region}:{account_id}:portfolio/{id}'},
        'servicediscovery': {'method': 'list_services', 'key': 'Services', 'id_attr': 'Id', 'arn_format': 'arn:aws:servicediscovery:{region}:{account_id}:service/{id}'},
        'ses': {'method': 'list_identities', 'key': 'Identities', 'id_list': True, 'arn_format': 'arn:aws:ses:{region}:{account_id}:identity/{id}'},
        'shield': {'method': 'list_protections', 'key': 'Protections', 'id_attr': 'Id', 'arn_format': 'arn:aws:shield:{region}:{account_id}:protection/{id}'},
        'sns': {'method': 'list_topics', 'key': 'Topics', 'arn_attr': 'TopicArn'},
        'signer': {'method': 'list_signing_profiles', 'key': 'profiles', 'arn_attr': 'arn'},
        'stepfunctions': {'method': 'list_state_machines', 'key': 'stateMachines', 'arn_attr': 'stateMachineArn'},
        'storagegateway': {'method': 'list_gateways', 'key': 'Gateways', 'arn_attr': 'GatewayARN'},
        'textract': {'method': 'get_document_analysis', 'key': 'DocumentMetadata', 'custom': True},  # Requires special handling
        'timestream-query': {'method': 'list_databases', 'key': 'Databases', 'arn_attr': 'Arn'},
        'transfer': {'method': 'list_servers', 'key': 'Servers', 'arn_attr': 'Arn'},
        'translate': {'method': 'list_terminologies', 'key': 'TerminologyPropertiesList', 'arn_attr': 'TerminologyArn'},
        'waf': {'method': 'list_rules', 'key': 'Rules', 'id_attr': 'RuleId', 'arn_format': 'arn:aws:waf::{account_id}:rule/{id}'},
        'waf-regional': {'method': 'list_rules', 'key': 'Rules', 'id_attr': 'RuleId', 'arn_format': 'arn:aws:waf-regional:{region}:{account_id}:rule/{id}'},
        'wafv2': {'method': 'list_web_acls', 'key': 'WebACLs', 'arn_attr': 'ARN'},
        'workspaces': {'method': 'describe_workspaces', 'key': 'Workspaces', 'id_attr': 'WorkspaceId', 'arn_format': 'arn:aws:workspaces:{region}:{account_id}:workspace/{id}'},
        'xray': {'method': 'get_groups', 'key': 'Groups', 'arn_attr': 'GroupARN'},
    }

    # Check if we have a mapping for this service
    if service_name in service_mappings:
        mapping = service_mappings[service_name]
        method_name = mapping['method']
        response_key = mapping['key']

        try:
            # Get the method from the client
            method = getattr(client, method_name)

            # Call the method (with minimal parameters)
            if service_name == 'ce':
                # Special handling for Cost Explorer which requires time range
                from datetime import datetime, timedelta
                end = datetime.now()
                start = end - timedelta(days=30)
                response = method(
                    TimePeriod={
                        'Start': start.strftime('%Y-%m-%d'),
                        'End': end.strftime('%Y-%m-%d')
                    },
                    Granularity='MONTHLY',
                    Metrics=['UnblendedCost']
                )
            elif service_name == 'cloudwatch':
                # Just get a sample of metrics
                response = method(Namespace='AWS/EC2')
            elif service_name == 'health':
                # Health service requires filter
                response = method(filter={})
            elif service_name == 'textract':
                # Textract requires a document ID which we don't have
                return []
            else:
                # Standard method call
                response = method()

            # Extract resources based on the mapping
            if 'direct_arn' in mapping and mapping['direct_arn']:
                # The response itself is the ARN
                if response_key in response:
                    resources.append(response[response_key])
            else:
                # Navigate to the correct response key, handling nested keys with dots
                items = response
                for key_part in response_key.split('.'):
                    if key_part in items:
                        items = items[key_part]
                    else:
                        items = []
                        break

                # Process the items
                if 'id_list' in mapping and mapping['id_list']:
                    # Response is a list of IDs
                    for item_id in items:
                        arn = mapping['arn_format'].format(
                            region=region,
                            account_id=account_id,
                            id=item_id
                        )
                        resources.append(arn)
                elif 'arn_list' in mapping and mapping['arn_list']:
                    # Response is a list of ARNs
                    resources.extend(items)
                else:
                    # Response is a list of objects
                    for item in items:
                        if 'arn_attr' in mapping:
                            # Extract ARN directly from the item
                            if mapping['arn_attr'] in item:
                                resources.append(item[mapping['arn_attr']])
                        elif 'id_attr' in mapping and 'arn_format' in mapping:
                            # Construct ARN from ID and format
                            if mapping['id_attr'] in item:
                                item_id = item[mapping['id_attr']]
                                arn = mapping['arn_format'].format(
                                    region=region,
                                    account_id=account_id,
                                    id=item_id
                                )
                                resources.append(arn)

        except Exception as e:
            # Just log the error and continue
            print(f"Error getting resources for {service_name}: {str(e)}")

    return resources

def collect_resources_for_service(service_name, region, account_id, resource_arns):
    """Collect resources for a specific service in a region."""
    try:
        # Create a boto3 client for the service in the specified region
        client = boto3.client(service_name, region_name=region)

        # Different services have different list/describe methods
        if service_name == 'ec2':
            # EC2 instances
            response = client.describe_instances()
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instance_id = instance['InstanceId']
                    arn = f"arn:aws:ec2:{region}:{account_id}:instance/{instance_id}"
                    resource_arns.append(arn)

            # EC2 volumes
            response = client.describe_volumes()
            for volume in response.get('Volumes', []):
                volume_id = volume['VolumeId']
                arn = f"arn:aws:ec2:{region}:{account_id}:volume/{volume_id}"
                resource_arns.append(arn)

            # EC2 security groups
            response = client.describe_security_groups()
            for sg in response.get('SecurityGroups', []):
                sg_id = sg['GroupId']
                arn = f"arn:aws:ec2:{region}:{account_id}:security-group/{sg_id}"
                resource_arns.append(arn)

            # EC2 Elastic IP Addresses
            response = client.describe_addresses()
            for eip in response.get('Addresses', []):
                allocation_id = eip.get('AllocationId')
                if allocation_id:
                    arn = f"arn:aws:ec2:{region}:{account_id}:elastic-ip/{allocation_id}"
                    resource_arns.append(arn)

            # EC2 VPC resources
            # VPCs
            response = client.describe_vpcs()
            for vpc in response.get('Vpcs', []):
                vpc_id = vpc['VpcId']
                arn = f"arn:aws:ec2:{region}:{account_id}:vpc/{vpc_id}"
                resource_arns.append(arn)

            # Subnets
            response = client.describe_subnets()
            for subnet in response.get('Subnets', []):
                subnet_id = subnet['SubnetId']
                arn = f"arn:aws:ec2:{region}:{account_id}:subnet/{subnet_id}"
                resource_arns.append(arn)

            # Route Tables
            response = client.describe_route_tables()
            for rt in response.get('RouteTables', []):
                rt_id = rt['RouteTableId']
                arn = f"arn:aws:ec2:{region}:{account_id}:route-table/{rt_id}"
                resource_arns.append(arn)

            # Network ACLs
            response = client.describe_network_acls()
            for nacl in response.get('NetworkAcls', []):
                nacl_id = nacl['NetworkAclId']
                arn = f"arn:aws:ec2:{region}:{account_id}:network-acl/{nacl_id}"
                resource_arns.append(arn)

            # Internet Gateways
            response = client.describe_internet_gateways()
            for igw in response.get('InternetGateways', []):
                igw_id = igw['InternetGatewayId']
                arn = f"arn:aws:ec2:{region}:{account_id}:internet-gateway/{igw_id}"
                resource_arns.append(arn)

            # NAT Gateways
            response = client.describe_nat_gateways()
            for nat in response.get('NatGateways', []):
                nat_id = nat['NatGatewayId']
                arn = f"arn:aws:ec2:{region}:{account_id}:nat-gateway/{nat_id}"
                resource_arns.append(arn)

            # Elastic Network Interfaces
            response = client.describe_network_interfaces()
            for eni in response.get('NetworkInterfaces', []):
                eni_id = eni['NetworkInterfaceId']
                arn = f"arn:aws:ec2:{region}:{account_id}:network-interface/{eni_id}"
                resource_arns.append(arn)

            # Transit Gateways
            try:
                response = client.describe_transit_gateways()
                for tgw in response.get('TransitGateways', []):
                    arn = tgw.get('TransitGatewayArn')
                    if arn:
                        resource_arns.append(arn)
            except Exception as e:
                print(f"Error getting transit gateways: {str(e)}")

        elif service_name == 's3':
            # S3 buckets (global service but listing here)
            response = client.list_buckets()
            for bucket in response.get('Buckets', []):
                bucket_name = bucket['Name']
                arn = f"arn:aws:s3:::{bucket_name}"
                resource_arns.append(arn)

                # List objects in buckets (with pagination)
                try:
                    # Only list objects in buckets that are in the current region or global
                    bucket_region = client.get_bucket_location(Bucket=bucket_name)
                    location_constraint = bucket_region.get('LocationConstraint', '')

                    # Handle the special case where None means us-east-1
                    if location_constraint is None:
                        location_constraint = 'us-east-1'

                    if location_constraint == region or location_constraint == '':
                        # Only list top-level objects to avoid excessive API calls
                        paginator = client.get_paginator('list_objects_v2')
                        for page in paginator.paginate(Bucket=bucket_name, MaxKeys=100, Delimiter='/'):
                            for obj in page.get('Contents', []):
                                arn = f"arn:aws:s3:::{bucket_name}/{obj['Key']}"
                                resource_arns.append(arn)
                except Exception as e:
                    print(f"Error listing objects in bucket {bucket_name}: {str(e)}")

        elif service_name == 'iam':
            # IAM roles (global service)
            if region == default_region:  # Only check in one region to avoid duplicates
                response = client.list_roles()
                for role in response.get('Roles', []):
                    arn = role['Arn']
                    resource_arns.append(arn)

                # IAM users
                response = client.list_users()
                for user in response.get('Users', []):
                    arn = user['Arn']
                    resource_arns.append(arn)

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

                # IAM server certificates
                try:
                    response = client.list_server_certificates()
                    for cert in response.get('ServerCertificateMetadataList', []):
                        arn = cert['Arn']
                        resource_arns.append(arn)
                except Exception as e:
                    print(f"Error listing server certificates: {str(e)}")

        elif service_name == 'sqs':
            # SQS queues
            response = client.list_queues()
            for queue_url in response.get('QueueUrls', []):
                queue_attrs = client.get_queue_attributes(
                    QueueUrl=queue_url,
                    AttributeNames=['QueueArn']
                )
                arn = queue_attrs['Attributes']['QueueArn']
                resource_arns.append(arn)

        elif service_name == 'cloudwatch':
            # Create a separate logs client for log groups
            logs_client = boto3.client('logs', region_name=region)
            paginator = logs_client.get_paginator('describe_log_groups')
            for page in paginator.paginate():
                for log_group in page.get('logGroups', []):
                    arn = log_group.get('arn')
                    if not arn:  # If ARN is not directly provided, construct it
                        log_group_name = log_group['logGroupName']
                        arn = f"arn:aws:logs:{region}:{account_id}:log-group:{log_group_name}"
                    resource_arns.append(arn)

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

            # CloudWatch Dashboards
            response = client.list_dashboards()
            for dashboard in response.get('DashboardEntries', []):
                arn = dashboard['DashboardArn']
                resource_arns.append(arn)

        elif service_name == 'route53':
            # Route53 is a global service, only run in the default region
            if region == default_region:
                # Get hosted zones
                paginator = client.get_paginator('list_hosted_zones')
                for page in paginator.paginate():
                    for zone in page.get('HostedZones', []):
                        zone_id = zone['Id']
                        arn = f"arn:aws:route53:::{zone_id}"
                        resource_arns.append(arn)

                        # Get record sets for each zone
                        try:
                            # Extract the ID without the /hostedzone/ prefix
                            clean_zone_id = zone_id.split('/')[-1]
                            record_paginator = client.get_paginator('list_resource_record_sets')
                            for record_page in record_paginator.paginate(HostedZoneId=clean_zone_id):
                                for record in record_page.get('ResourceRecordSets', []):
                                    record_name = record['Name']
                                    record_type = record['Type']
                                    # Route53 record ARNs don't officially exist, but we can create a pseudo-ARN
                                    arn = f"arn:aws:route53:::{zone_id}/record/{record_name}/{record_type}"
                                    resource_arns.append(arn)
                        except Exception as e:
                            print(f"Error getting record sets for zone {zone_id}: {str(e)}")

                # Get health checks
                paginator = client.get_paginator('list_health_checks')
                for page in paginator.paginate():
                    for health_check in page.get('HealthChecks', []):
                        health_check_id = health_check['Id']
                        arn = f"arn:aws:route53:::healthcheck/{health_check_id}"
                        resource_arns.append(arn)

        elif service_name == 'ecs':
            # ECS Clusters
            paginator = client.get_paginator('list_clusters')
            cluster_arns = []
            for page in paginator.paginate():
                cluster_arns.extend(page.get('clusterArns', []))

            for cluster_arn in cluster_arns:
                resource_arns.append(cluster_arn)

                # Get services for each cluster
                try:
                    service_paginator = client.get_paginator('list_services')
                    for service_page in service_paginator.paginate(cluster=cluster_arn):
                        for service_arn in service_page.get('serviceArns', []):
                            resource_arns.append(service_arn)
                except Exception as e:
                    print(f"Error getting services for cluster {cluster_arn}: {str(e)}")

                # Get task definitions
                try:
                    task_def_paginator = client.get_paginator('list_task_definitions')
                    for task_def_page in task_def_paginator.paginate():
                        for task_def_arn in task_def_page.get('taskDefinitionArns', []):
                            resource_arns.append(task_def_arn)
                except Exception as e:
                    print(f"Error getting task definitions: {str(e)}")

                # Get tasks for each cluster
                try:
                    task_paginator = client.get_paginator('list_tasks')
                    for task_page in task_paginator.paginate(cluster=cluster_arn):
                        for task_arn in task_page.get('taskArns', []):
                            resource_arns.append(task_arn)
                except Exception as e:
                    print(f"Error getting tasks for cluster {cluster_arn}: {str(e)}")

        elif service_name == 'kms':
            # KMS Keys
            paginator = client.get_paginator('list_keys')
            for page in paginator.paginate():
                for key in page.get('Keys', []):
                    key_id = key['KeyId']
                    key_arn = key['KeyArn']
                    resource_arns.append(key_arn)

                    # Get aliases for each key
                    try:
                        alias_response = client.list_aliases(KeyId=key_id)
                        for alias in alias_response.get('Aliases', []):
                            alias_arn = alias['AliasArn']
                            resource_arns.append(alias_arn)
                    except Exception as e:
                        print(f"Error getting aliases for key {key_id}: {str(e)}")

        else:
            # Use the generic service resource collector for other services
            resources = get_service_resources(client, service_name, region, account_id)
            resource_arns.extend(resources)

    except ClientError as e:
        if 'AccessDenied' in str(e) or 'UnauthorizedOperation' in str(e):
            print(f"Access denied for service {service_name} in region {region}")
        elif 'OptInRequired' in str(e):
            print(f"Region {region} requires opt-in for service {service_name}")
        elif 'InvalidClientTokenId' in str(e):
            print(f"Invalid credentials for service {service_name} in region {region}")
        else:
            print(f"Error with service {service_name} in region {region}: {e}")
    except Exception as e:
        print(f"General error with service {service_name} in region {region}: {e}")

def get_all_resource_arns(additional_services=None, specific_region=None):
    """Get ARNs for all resources across supported services and regions."""
    account_id = get_account_id()
    # Use specific region if provided, otherwise get all regions
    regions = [specific_region] if specific_region else get_all_regions()

    # List of services to check
    default_services = [
        # Default services to scan
        'ec2', 's3', 'lambda', 'dynamodb', 'rds', 'iam',
        'cloudformation', 'sqs', 'sns',
        'kinesisanalytics', 'kinesisanalyticsv2', 'cloudwatch', 'route53', 'ecs', 'kms',
    ]

    resource_arns = []

    # Use ThreadPoolExecutor to parallelize API calls
    services = default_services.copy()

    # Add any additional services specified by the user
    if additional_services:
        services.extend([s for s in additional_services if s not in services])

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []

        # Global services only need to be checked once
        global_services = ['iam', 's3', 'route53']

        for service in services:
            if service in global_services:
                futures.append(
                    executor.submit(
                        collect_resources_for_service,
                        service,
                        default_region,  # Use a default region for global services
                        account_id,
                        resource_arns
                    )
                )
            else:
                for region in regions:
                    futures.append(
                        executor.submit(
                            collect_resources_for_service,
                            service,
                            region,
                            account_id,
                            resource_arns
                        )
                    )

        # Wait for all futures to complete
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error in thread: {e}")

    return resource_arns

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='List all AWS resource ARNs under the currently logged-in account.')
    parser.add_argument('--services', '-s', nargs='+', help='Additional AWS services to scan (e.g., "apigateway" "kms" "secretsmanager")')
    parser.add_argument('--output', '-o', default='aws_resource_arns.json', help='Output file path (default: aws_resource_arns.json)')
    parser.add_argument('--region', '-r', help='Specific AWS region to scan (default: scan all regions)')

    args = parser.parse_args()

    additional_services = args.services
    output_file = args.output

    if additional_services:
        print(f"Including additional services: {', '.join(additional_services)}")

    if args.region:
        print(f"Scanning only region: {args.region}")
        print("Scanning all available regions")

    print("Collecting AWS resource ARNs. This may take a while...")
    # Pass additional services to the function
    resource_arns = get_all_resource_arns(additional_services, args.region)

    # Print the results
    print(f"\nFound {len(resource_arns)} resources:")
    # for arn in sorted(resource_arns):
    #     print(arn)

    # Optionally save to a file
    with open(output_file, 'w') as f:
        json.dump(resource_arns, f, indent=2)

    print(f"\nResource ARNs have been saved to {output_file}")

if __name__ == "__main__":
    main()