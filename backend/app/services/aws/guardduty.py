from concurrent.futures import ThreadPoolExecutor
import boto3
import logging
from botocore.exceptions import ClientError
from typing import List, Dict, Any
from app.services.aws.client import AWSClientProvider

logger = logging.getLogger(__name__)


class GuardDutyScanner:
    def __init__(self, client_provider: AWSClientProvider):
        self.client_provider = client_provider

    def get_all_regions(self) -> List[str]:
        try:
            ec2_client = self.client_provider.get_client('ec2', region_name='us-east-1')
            response = ec2_client.describe_regions()
            return [region['RegionName'] for region in response['Regions']]
        except Exception as e:
            logger.error(f"Error getting regions: {e}")
            return ['us-east-1', 'us-west-2', 'eu-west-1']

    def check_all_regions_status(self) -> Dict[str, Any]:
        all_regions = self.get_all_regions()
        status_by_region = {}
        enabled_regions = []

        with ThreadPoolExecutor(max_workers=min(len(all_regions), 10)) as executor:
            future_to_region = {
                executor.submit(self._check_region, region): region
                for region in all_regions
            }

            for future in future_to_region:
                region = future_to_region[future]
                try:
                    result = future.result()
                    status_by_region[region] = result
                    if result['enabled']:
                        enabled_regions.append(region)
                except Exception as e:
                    logger.error(f"Error checking {region}: {e}")
                    status_by_region[region] = {
                        'enabled': False,
                        'error': str(e)
                    }

        return {
            'status_by_region': status_by_region,
            'enabled_regions': enabled_regions,
            'disabled_regions': [r for r in all_regions if r not in enabled_regions],
            'summary': {
                'total_regions': len(all_regions),
                'enabled_count': len(enabled_regions),
                'disabled_count': len(all_regions) - len(enabled_regions)
            }
        }

    def _check_region(self, region: str) -> Dict[str, Any]:
        try:
            client = self.client_provider.get_client('guardduty', region_name=region)
            response = client.list_detectors()
            detectors = response.get('DetectorIds', [])

            if detectors:
                return {
                    'enabled': True,
                    'detector_id': detectors[0]
                }
            else:
                return {
                    'enabled': False,
                    'message': 'GuardDuty not enabled'
                }
        except Exception as e:
            raise Exception(f"Error in {region}: {str(e)}")

    def get_all_findings(self, severity_filter: int = 4) -> Dict[str, Any]:
        status = self.check_all_regions_status()
        enabled_regions = status['enabled_regions']

        if not enabled_regions:
            return {
                'findings': [],
                'total_count': 0,
                'enabled_regions': [],
                'message': 'GuardDuty not enabled in any region'
            }

        all_findings = []
        findings_by_region = {}

        with ThreadPoolExecutor(max_workers=len(enabled_regions)) as executor:
            future_to_region = {
                executor.submit(self._get_findings_from_region, region, severity_filter): region
                for region in enabled_regions
            }

            for future in future_to_region:
                region = future_to_region[future]
                try:
                    findings = future.result()
                    all_findings.extend(findings)
                    findings_by_region[region] = {
                        'count': len(findings),
                        'findings': findings
                    }
                except Exception as e:
                    logger.error(f"Error getting findings from {region}: {e}")
                    findings_by_region[region] = {
                        'count': 0,
                        'error': str(e)
                    }

        return {
            'findings': all_findings,
            'total_count': len(all_findings),
            'enabled_regions': enabled_regions,
            'findings_by_region': findings_by_region,
            'severity_breakdown': self._calculate_severity_breakdown(all_findings)
        }

    def _get_findings_from_region(self, region: str, severity_filter: int) -> List[Dict]:
        try:
            client = self.client_provider.get_client('guardduty', region_name=region)

            detectors = client.list_detectors().get('DetectorIds', [])
            if not detectors:
                return []

            detector_id = detectors[0]

            findings_response = client.list_findings(
                DetectorId=detector_id,
                FindingCriteria={
                    'Criterion': {
                        'severity': {'Gte': severity_filter},
                        'service.archived': {'Eq': ['false']}
                    }
                },
                MaxResults=50
            )

            finding_ids = findings_response.get('FindingIds', [])
            if not finding_ids:
                return []

            details = client.get_findings(
                DetectorId=detector_id,
                FindingIds=finding_ids
            )

            formatted = []
            for finding in details.get('Findings', []):
                formatted.append({
                    'finding_id': finding['Id'],
                    'type': finding['Type'],
                    'severity': finding['Severity'],
                    'severity_label': self._get_severity_label(finding['Severity']),
                    'title': finding['Title'],
                    'description': finding['Description'],
                    'region': region,
                    'resource_type': finding['Resource'].get('ResourceType'),
                    'resource_id': self._extract_resource_id(finding['Resource']),
                    'created_at': finding['CreatedAt'],
                    'updated_at': finding['UpdatedAt'],
                    'count': finding['Service'].get('Count', 1)
                })

            return formatted

        except Exception as e:
            raise Exception(f"Failed to get findings from {region}: {str(e)}")

    def _extract_resource_id(self, resource: Dict) -> str:
        resource_type = resource.get('ResourceType', '')
        if resource_type == 'Instance':
            return resource.get('InstanceDetails', {}).get('InstanceId', 'Unknown')
        elif resource_type == 'AccessKey':
            return resource.get('AccessKeyDetails', {}).get('AccessKeyId', 'Unknown')
        elif resource_type == 'S3Bucket':
            buckets = resource.get('S3BucketDetails', [])
            return buckets[0].get('Name', 'Unknown') if buckets else 'Unknown'
        else:
            return 'Unknown'

    def _get_severity_label(self, severity: float) -> str:
        if severity >= 7.0:
            return 'HIGH'
        elif severity >= 4.0:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _calculate_severity_breakdown(self, findings: List[Dict]) -> Dict[str, int]:
        breakdown = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}

        for finding in findings:
            severity_label = finding.get('severity_label', 'LOW')
            breakdown[severity_label] = breakdown.get(severity_label, 0) + 1

        return breakdown