from concurrent.futures import ThreadPoolExecutor
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.services.aws.client import AWSClientProvider
from app.services.email.ses_client import SESEmailService
from .base_scanner import BaseAWSScanner
logger = logging.getLogger(__name__)


class GuardDutyScanner(BaseAWSScanner):
    def __init__(self, client_provider: AWSClientProvider):
        self.client_provider = client_provider

    @BaseAWSScanner.with_retry()
    def get_all_regions(self) -> List[str]:
        try:
            ec2_client = self.client_provider.get_client('ec2', region_name='us-east-1')
            response = ec2_client.describe_regions()
            return [region['RegionName'] for region in response['Regions']]
        except Exception as e:
            logger.error(f"Error getting regions: {e}")
            return ['us-east-1', 'us-west-2', 'eu-west-1']

    @BaseAWSScanner.with_retry()
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
                    error_str = str(e)
                    if 'SubscriptionRequiredException' in error_str:
                        logger.debug(f"GuardDuty not subscribed in {region}")
                    else:
                        logger.error(f"Error checking {region}: {e}")

                    status_by_region[region] = {
                        'enabled': False,
                        'error': error_str
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

    @BaseAWSScanner.with_retry()
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

    @BaseAWSScanner.with_retry()
    def scan_all_regions(self, severity_filter: int = 4) -> Dict[str, Any]:
        """
        Scan all regions for GuardDuty findings.
        Compatible format for architecture analyzer.

        Returns:
            Dict with 'regions' key containing list of region data
        """
        all_findings_data = self.get_all_findings(severity_filter)

        # Transform findings_by_region dict to regions list
        regions = []
        for region, region_data in all_findings_data.get('findings_by_region', {}).items():
            regions.append({
                'region': region,
                'findings': region_data.get('findings', []),
                'count': region_data.get('count', 0)
            })

        return {
            'regions': regions,
            'total_findings': all_findings_data.get('total_count', 0),
            'enabled_regions': all_findings_data.get('enabled_regions', [])
        }

    @BaseAWSScanner.with_retry()
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

    @BaseAWSScanner.with_retry()
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

    @BaseAWSScanner.with_retry()
    def get_critical_findings_for_api(self) -> Dict[str, Any]:
        """
        Get critical findings (for API endpoint display)
        Returns dict with 'findings' key
        """
        all_findings = self.get_all_findings(severity_filter=7)
        return {
            'total_critical': all_findings['total_count'],
            'findings': all_findings['findings'],
            'enabled_regions': all_findings['enabled_regions'],
            'by_type': self._group_by_type(all_findings['findings'])
        }

    @BaseAWSScanner.with_retry()
    def get_critical_findings(self,
                              start_time: Optional[str] = None,
                              end_time: Optional[str] = None,
                              region: str = 'us-east-1') -> List[Dict]:
        """
        Used by CRITICAL ALERT MONITOR

        Args:
            start_time: ISO format datetime (e.g., "2025-10-20T10:00:00")
            end_time: ISO format datetime
            region: AWS region (default: us-east-1)

        Returns:
            List of critical findings (raw GuardDuty format)
        """
        try:
            client = self.client_provider.get_client('guardduty', region_name=region)

            # Get detector ID
            detectors = client.list_detectors()
            detector_ids = detectors.get('DetectorIds', [])

            if not detector_ids:
                logger.warning("No GuardDuty detectors found")
                return []

            detector_id = detector_ids[0]

            # Build filter criteria
            finding_criteria = {
                'Criterion': {
                    'severity': {
                        'Gte': 7.0,  # Critical = 7.0 to 8.9
                        'Lte': 8.9
                    },
                    'service.archived': {'Eq': ['false']}  # Only active findings
                }
            }

            # Add time filter if provided
            if start_time and end_time:
                finding_criteria['Criterion']['updatedAt'] = {
                    'Gte': int(datetime.fromisoformat(start_time).timestamp() * 1000),
                    'Lte': int(datetime.fromisoformat(end_time).timestamp() * 1000)
                }

            # List finding IDs
            response = client.list_findings(
                DetectorId=detector_id,
                FindingCriteria=finding_criteria,
                SortCriteria={
                    'AttributeName': 'updatedAt',
                    'OrderBy': 'DESC'
                },
                MaxResults=50  # Limit to recent 50
            )

            finding_ids = response.get('FindingIds', [])

            if not finding_ids:
                return []

            # Get full finding details
            findings_response = client.get_findings(
                DetectorId=detector_id,
                FindingIds=finding_ids
            )

            findings = findings_response.get('Findings', [])

            logger.info(f"Found {len(findings)} critical findings in {region}")
            return findings

        except Exception as e:
            logger.error(f"Error getting critical findings: {e}")
            return []

    @BaseAWSScanner.with_retry()
    def get_findings_summary(self,
                             start_time: Optional[str] = None,
                             end_time: Optional[str] = None,
                             region: str = 'us-east-1') -> Dict:
        """
        Used by DAILY SUMMARY EMAIL

        Args:
            start_time: ISO format datetime
            end_time: ISO format datetime
            region: AWS region (default: us-east-1)

        Returns:
            Dictionary with counts by severity
        """
        try:
            client = self.client_provider.get_client('guardduty', region_name=region)

            # Get detector ID
            detectors = client.list_detectors()
            detector_ids = detectors.get('DetectorIds', [])

            if not detector_ids:
                logger.warning("No GuardDuty detectors found")
                return self._empty_summary()

            detector_id = detector_ids[0]

            # Build filter criteria
            finding_criteria = {
                'Criterion': {
                    'service.archived': {'Eq': ['false']}  # Only active findings
                }
            }

            # Add time filter if provided
            if start_time and end_time:
                finding_criteria['Criterion']['updatedAt'] = {
                    'Gte': int(datetime.fromisoformat(start_time).timestamp() * 1000),
                    'Lte': int(datetime.fromisoformat(end_time).timestamp() * 1000)
                }

            # Get all findings in time range
            response = client.list_findings(
                DetectorId=detector_id,
                FindingCriteria=finding_criteria,
                MaxResults=100
            )

            finding_ids = response.get('FindingIds', [])

            if not finding_ids:
                return self._empty_summary()

            # Get full details
            findings_response = client.get_findings(
                DetectorId=detector_id,
                FindingIds=finding_ids
            )

            findings = findings_response.get('Findings', [])

            # Count by severity
            summary = {
                'total': len(findings),
                'critical': 0,  # 7.0 - 8.9
                'high': 0,  # 4.0 - 6.9
                'medium': 0,  # 2.0 - 3.9
                'low': 0  # 0.1 - 1.9
            }

            for finding in findings:
                severity = finding.get('Severity', 0)

                if severity >= 7.0:
                    summary['critical'] += 1
                elif severity >= 4.0:
                    summary['high'] += 1
                elif severity >= 2.0:
                    summary['medium'] += 1
                else:
                    summary['low'] += 1

            logger.info(f"Findings summary: {summary}")
            return summary

        except Exception as e:
            logger.error(f"Error getting findings summary: {e}")
            return self._empty_summary()

    @BaseAWSScanner.with_retry()
    async def get_critical_findings_with_alerts(
            self,
            recipient_email: str = None
    ) -> Dict[str, Any]:
        """
        Get critical findings AND send email alerts.
        Used for manual alert testing from API endpoint.

        Args:
            recipient_email: Email to send alerts to (optional).

        Returns:
            A dictionary with findings and the alert status.
        """
        # Use the API method (returns dict)
        result = self.get_critical_findings_for_api()
        findings = result.get('findings', [])
        alerts_sent = 0
        alerts_failed = 0

        if recipient_email and findings:
            email_service = SESEmailService()

            # Send alerts for first 5 critical findings
            for finding in findings[:5]:
                try:
                    alert_data = {
                        'severity': 'CRITICAL',
                        'title': finding.get('title'),
                        'description': finding.get('description'),
                        'service': finding.get('resource_type', 'Unknown'),
                        'resource_id': finding.get('resource_id'),
                        'region': finding.get('region'),
                        'timestamp': finding.get('updated_at'),
                        'finding_id': finding.get('finding_id'),
                    }

                    success = await email_service.send_critical_alert(
                        recipient_email=recipient_email,
                        alert_data=alert_data
                    )

                    if success:
                        alerts_sent += 1
                    else:
                        alerts_failed += 1

                except Exception as e:
                    logger.error(f"Failed to send alert: {e}")
                    alerts_failed += 1

        return {
            **result,
            'alerts_sent': alerts_sent,
            'alerts_failed': alerts_failed,
            'recipient_email': recipient_email
        }


    def _extract_resource_id(self, resource: Dict) -> str:
        """Extract resource ID from GuardDuty resource object"""
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
        """Convert numeric severity to label"""
        if severity >= 7.0:
            return 'CRITICAL'
        elif severity >= 4.0:
            return 'HIGH'
        elif severity >= 2.0:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _calculate_severity_breakdown(self, findings: List[Dict]) -> Dict[str, int]:
        """Calculate count of findings by severity label"""
        breakdown = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}

        for finding in findings:
            severity_label = finding.get('severity_label', 'LOW')
            breakdown[severity_label] = breakdown.get(severity_label, 0) + 1

        return breakdown

    def _group_by_type(self, findings: List[Dict]) -> Dict[str, int]:
        """Group findings by threat type"""
        type_counts = {}
        for finding in findings:
            threat_type = finding.get('type', 'Unknown')
            type_counts[threat_type] = type_counts.get(threat_type, 0) + 1
        return type_counts

    def _empty_summary(self) -> Dict:
        """Return empty summary structure"""
        return {
            'total': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }