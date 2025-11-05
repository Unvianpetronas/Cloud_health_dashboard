import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from decimal import Decimal
from app.services.cache_client.redis_client import cache
from app.config import settings
from app.database.models import (
    ClientModel,
    MetricsModel,
    CostsModel,
    SecurityFindingModel,
    RecommendationModel
)
from app.services.aws.client import AWSClientProvider
from app.services.aws.ec2 import EC2Scanner
from app.services.aws.guardduty import GuardDutyScanner
from app.services.aws.costexplorer import CostExplorerScanner
from app.services.aws.s3 import S3Scanner
from app.services.aws.cloudwatch import CloudWatchScanner

logger = logging.getLogger(__name__)


class CloudHealthWorker:
    """
    Background worker for a single client that:
    1. Collects data from client's AWS account using their credentials
    2. Saves data to DynamoDB with client_id for multi-tenant isolation
    3. Runs continuously on a schedule
    4. Sends email alerts for critical security findings
    """

    def __init__(self, client_provider: AWSClientProvider, aws_account_id: str):
        """
        Initialize worker for a specific client

        Args:
            client_provider: AWS client provider with client's credentials
            client_id: Client ID (not AWS account ID!)
        """
        logger.info(f"[{aws_account_id}] Initializing Cloud Health Worker...")

        self.client_provider = client_provider
        self.aws_account_id = aws_account_id
        self.cache = cache

        # Initialize database models
        self.client_model = ClientModel()
        self.metrics_model = MetricsModel()
        self.costs_model = CostsModel()
        self.security_model = SecurityFindingModel()
        self.recommendation_model = RecommendationModel()

        # Initialize AWS scanners
        self.ec2_scanner = EC2Scanner(self.client_provider)
        self.guardduty_scanner = GuardDutyScanner(self.client_provider)
        self.cost_scanner = CostExplorerScanner(self.client_provider)
        self.s3_scanner = S3Scanner(self.client_provider)
        self.cloudwatch_scanner = CloudWatchScanner(self.client_provider)

        logger.info(f"[{self.aws_account_id}] Worker initialized successfully!")

    async def collect_ec2_metrics(self):
        """Collect EC2 metrics from client's AWS account"""
        try:
            logger.info(f"[{self.aws_account_id}] Collecting EC2 metrics...")

            summary = self.ec2_scanner.get_instance_summary()
            timestamp = datetime.now()

            if not summary.get('has_instances'):
                logger.info(f"[{self.aws_account_id}] No EC2 instances found")
                return

            # All calls now include client_id
            await self.metrics_model.store_metric(
                aws_account_id = self.aws_account_id,
                service="EC2",
                metric_name="TotalInstances",
                value=float(summary.get('total_instances', 0)),
                timestamp=timestamp,
                unit="Count",
                dimensions={}
            )

            # Store by state
            by_state = summary.get('by_state', {})
            for state, count in by_state.items():
                await self.metrics_model.store_metric(
                    aws_account_id = self.aws_account_id,
                    service="EC2",
                    metric_name=f"{state.capitalize()}Instances",
                    value=float(count),
                    timestamp=timestamp,
                    unit="Count",
                    dimensions={"State": state}
                )

            # Store by type
            by_type = summary.get('by_type', {})
            for instance_type, count in by_type.items():
                await self.metrics_model.store_metric(
                    aws_account_id = self.aws_account_id,
                    service="EC2",
                    metric_name="InstancesByType",
                    value=float(count),
                    timestamp=timestamp,
                    unit="Count",
                    dimensions={"InstanceType": instance_type}
                )

            logger.info(f"[{self.aws_account_id}] EC2 metrics collection completed!")

        except Exception as e:
            logger.error(f"[{self.aws_account_id}] Error collecting EC2 metrics: {e}", exc_info=True)

    async def collect_cost_data(self):
        """Collect cost data from AWS Cost Explorer"""
        try:
            logger.info(f"[{self.aws_account_id}] Collecting cost data...")

            today = datetime.now().strftime('%Y-%m-%d')
            start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')

            cost_data = self.cost_scanner.get_cost_by_service(
                start_date=start_date,
                end_date=today,
                granularity="DAILY"
            )

            saved_count = 0
            for result in cost_data.get('ResultsByTime', []):
                date = result['TimePeriod']['Start']

                for group in result.get('Groups', []):
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])

                    if cost == 0:
                        continue

                    usage_quantity = None
                    usage_unit = None
                    if 'UsageQuantity' in group['Metrics']:
                        usage_quantity = float(group['Metrics']['UsageQuantity']['Amount'])
                        usage_unit = group['Metrics']['UsageQuantity'].get('Unit', 'Units')

                    await self.costs_model.store_cost_data(
                        aws_account_id = self.aws_account_id,
                        service=service,
                        date=date,
                        cost=cost,
                        usage_quantity=usage_quantity,
                        usage_unit=usage_unit,
                        granularity="DAILY"
                    )
                    saved_count += 1

            logger.info(f"[{self.aws_account_id}] Cost data collection completed! ({saved_count} records)")

        except Exception as e:
            logger.error(f"[{self.aws_account_id}] Error collecting cost data: {e}", exc_info=True)

    async def collect_security_findings(self):
        """Collect security findings from GuardDuty"""
        try:
            logger.info(f"[{self.aws_account_id}] Collecting security findings...")

            findings_data = self.guardduty_scanner.get_all_findings(severity_filter=4)
            timestamp = datetime.now()

            # Now includes client_id
            await self.metrics_model.store_metric(
                aws_account_id = self.aws_account_id,
                service="GuardDuty",
                metric_name="TotalFindings",
                value=float(findings_data.get('total_count', 0)),
                timestamp=timestamp,
                unit="Count",
                dimensions={}
            )

            # Store severity breakdown
            severity_breakdown = findings_data.get('severity_breakdown', {})
            for severity, count in severity_breakdown.items():
                await self.metrics_model.store_metric(
                    aws_account_id = self.aws_account_id,
                    service="GuardDuty",
                    metric_name="FindingsBySeverity",
                    value=float(count),
                    timestamp=timestamp,
                    unit="Count",
                    dimensions={"Severity": severity}
                )

            # Store individual findings
            findings_saved = 0
            for finding in findings_data.get('findings', [])[:50]:
                await self.security_model.store_finding(
                    aws_account_id = self.aws_account_id,
                    finding_type="GuardDuty",
                    finding_id=finding.get('finding_id'),
                    severity=finding.get('severity_label', 'UNKNOWN'),
                    status="ACTIVE",
                    title=finding.get('title', 'Unknown'),
                    description=finding.get('description', ''),
                    service=finding.get('resource_type', 'Unknown'),
                    resource_id=finding.get('resource_id')
                )
                findings_saved += 1

            #Send email alerts for critical findings
            await self._send_critical_alerts(findings_data)

            logger.info(f"[{self.aws_account_id}] Security findings collection completed!")

        except Exception as e:
            logger.error(f"[{self.aws_account_id}] Error collecting security findings: {e}", exc_info=True)

    async def _send_critical_alerts(self, findings_data: Dict):
        """Send email alerts for critical security findings"""
        try:
            client = await self.client_model.get_client(self.aws_account_id)

            if not client or not client.get('email_verified'):
                return

            prefs = client.get('notification_preferences', {})
            if not prefs.get('critical_alerts', True):
                return

            critical_findings = [
                f for f in findings_data.get('findings', [])
                if f.get('severity_label') == 'HIGH'
            ][:3]

            if not critical_findings:
                return

            from app.services.email.ses_client import SESEmailService

            for finding in critical_findings:
                await SESEmailService.send_critical_alert(
                    recipient_email=client['email'],
                    alert_data={
                        'severity': finding['severity_label'],
                        'title': finding['title'],
                        'description': finding['description'],
                        'service': finding.get('resource_type', 'Unknown'),
                        'resource_id': finding.get('resource_id', 'N/A'),
                        'region': finding.get('region', client.get('aws_region', 'N/A')),
                        'timestamp': datetime.now().isoformat(),
                        'finding_id': finding['finding_id']
                    }
                )

                logger.info(f"[{self.aws_account_id}] Critical alert email sent")

        except Exception as e:
            logger.error(f"[{self.aws_account_id}] Error sending critical alerts: {e}", exc_info=True)

    async def collect_s3_metrics(self):
        """Collect S3 bucket metrics"""
        try:
            logger.info(f"[{self.aws_account_id}] Collecting S3 metrics...")

            s3_data = self.s3_scanner.scan_all_buckets()
            timestamp = datetime.now()

            #Now includes client_id
            await self.metrics_model.store_metric(
                aws_account_id = self.aws_account_id,
                service="S3",
                metric_name="TotalBuckets",
                value=float(s3_data.get('total_buckets', 0)),
                timestamp=timestamp,
                unit="Count",
                dimensions={}
            )

            for bucket in s3_data.get('buckets', []):
                metrics = bucket.get('metrics', {})

                if 'StandardStorageBytes' in metrics:
                    storage_gb = metrics['StandardStorageBytes'] / (1024 ** 3)
                    await self.metrics_model.store_metric(
                        aws_account_id = self.aws_account_id,
                        service="S3",
                        metric_name="StorageSize",
                        value=storage_gb,
                        timestamp=timestamp,
                        unit="Gigabytes",
                        dimensions={"BucketName": bucket['bucket']}
                    )

                if 'ObjectCount' in metrics:
                    await self.metrics_model.store_metric(
                        aws_account_id = self.aws_account_id,
                        service="S3",
                        metric_name="ObjectCount",
                        value=float(metrics['ObjectCount']),
                        timestamp=timestamp,
                        unit="Count",
                        dimensions={"BucketName": bucket['bucket']}
                    )

            logger.info(f"[{self.aws_account_id}] S3 metrics collection completed!")

        except Exception as e:
            logger.error(f"[{self.aws_account_id}] Error collecting S3 metrics: {e}", exc_info=True)

    async def collect_cloudwatch_metrics(self):
        """Collect CloudWatch metrics for EC2 instances"""
        try:
            logger.info(f"[{self.aws_account_id}] Collecting CloudWatch metrics...")

            # Get running EC2 instances
            ec2_summary = self.ec2_scanner.get_instance_summary()

            if not ec2_summary.get('has_instances'):
                logger.info(f"[{self.aws_account_id}] No EC2 instances found for CloudWatch metrics")
                return

            # Get all regions with instances
            all_instances = self.ec2_scanner.scan_all_regions()
            timestamp = datetime.now()
            metrics_collected = 0

            for region_data in all_instances.get('regions', []):
                region = region_data.get('region')
                instances = region_data.get('instances', [])

                # Only collect metrics for running instances
                running_instances = [
                    inst for inst in instances
                    if inst.get('State', {}).get('Name') == 'running'
                ]

                if not running_instances:
                    continue

                logger.info(f"[{self.aws_account_id}] Collecting CloudWatch metrics for {len(running_instances)} running instances in {region}")

                for instance in running_instances:
                    instance_id = instance.get('InstanceId')

                    try:
                        # Get CPU utilization
                        cpu_metrics = self.cloudwatch_scanner.get_ec2_cpu_utilization(
                            instance_id=instance_id,
                            hours=1,
                            region=region
                        )

                        if cpu_metrics and 'average' in cpu_metrics:
                            await self.metrics_model.store_metric(
                                aws_account_id=self.aws_account_id,
                                service="EC2",
                                metric_name="CPUUtilization",
                                value=float(cpu_metrics['average']),
                                timestamp=timestamp,
                                unit="Percent",
                                dimensions={
                                    "InstanceId": instance_id,
                                    "Region": region
                                }
                            )
                            metrics_collected += 1

                        # Get network in/out
                        network_in = self.cloudwatch_scanner.get_ec2_network_in(
                            instance_id=instance_id,
                            hours=1,
                            region=region
                        )

                        if network_in and 'average' in network_in:
                            await self.metrics_model.store_metric(
                                aws_account_id=self.aws_account_id,
                                service="EC2",
                                metric_name="NetworkIn",
                                value=float(network_in['average']),
                                timestamp=timestamp,
                                unit="Bytes",
                                dimensions={
                                    "InstanceId": instance_id,
                                    "Region": region
                                }
                            )
                            metrics_collected += 1

                        network_out = self.cloudwatch_scanner.get_ec2_network_out(
                            instance_id=instance_id,
                            hours=1,
                            region=region
                        )

                        if network_out and 'average' in network_out:
                            await self.metrics_model.store_metric(
                                aws_account_id=self.aws_account_id,
                                service="EC2",
                                metric_name="NetworkOut",
                                value=float(network_out['average']),
                                timestamp=timestamp,
                                unit="Bytes",
                                dimensions={
                                    "InstanceId": instance_id,
                                    "Region": region
                                }
                            )
                            metrics_collected += 1

                    except Exception as e:
                        logger.error(f"[{self.aws_account_id}] Error collecting CloudWatch metrics for {instance_id}: {e}")
                        continue

            logger.info(f"[{self.aws_account_id}] CloudWatch metrics collection completed! ({metrics_collected} metrics)")

        except Exception as e:
            logger.error(f"[{self.aws_account_id}] Error collecting CloudWatch metrics: {e}", exc_info=True)

    async def generate_recommendations(self):
        """Generate cost optimization recommendations"""
        try:
            logger.info(f"[{self.aws_account_id}] Generating recommendations...")

            recommendations_count = 0
            ec2_summary = self.ec2_scanner.get_instance_summary()

            if ec2_summary.get('has_instances'):
                stopped_count = ec2_summary.get('by_state', {}).get('stopped', 0)

                if stopped_count > 0:
                    await self.recommendation_model.store_recommendation(
                        aws_account_id=self.aws_account_id,
                        rec_type="cost",
                        title=f"Remove {stopped_count} stopped EC2 instances",
                        description=f"You have {stopped_count} stopped instances incurring EBS costs.",
                        impact="MEDIUM",
                        effort="LOW",
                        confidence=0.9,
                        service="EC2",
                        estimated_savings=stopped_count * 10.0
                    )
                    recommendations_count += 1

            logger.info(f"[{self.aws_account_id}] Generated {recommendations_count} recommendations!")

        except Exception as e:
            logger.error(f"[{self.aws_account_id}] Error generating recommendations: {e}", exc_info=True)


    async def run_collection_cycle(self):
        """Run one complete data collection cycle"""
        cycle_start = datetime.now()
        logger.info("=" * 70)
        logger.info(f"[{self.aws_account_id}] Starting collection cycle at {cycle_start.isoformat()}")
        logger.info("=" * 70)

        try:
            await self.collect_ec2_metrics()
            await self.collect_cost_data()
            await self.collect_security_findings()
            await self.collect_s3_metrics()
            await self.collect_cloudwatch_metrics()  # 🆕 NEW: CloudWatch metrics collection
            await self.generate_recommendations()

            # Update last collection timestamp
            await self.client_model.update_last_collection(self.aws_account_id)
            self.cache.clear_pattern(f"metrics:{self.aws_account_id}:*")
            self.cache.clear_pattern(f"client:{self.aws_account_id}:*")
            logger.debug(f"[{self.aws_account_id}] Cache invalidated for fresh data")

            cycle_end = datetime.now()
            duration = (cycle_end - cycle_start).total_seconds()

            logger.info("=" * 70)
            logger.info(f"[{self.aws_account_id}] Collection cycle completed in {duration:.2f}s")
            logger.info("=" * 70)

        except Exception as e:
            logger.error(f"[{self.aws_account_id}] Collection cycle failed: {e}", exc_info=True)

    async def start(self):
        """Start the background worker with continuous collection"""
        logger.info(f"[{self.aws_account_id}] Cloud Health Worker Starting!")
        logger.info(f"[{self.aws_account_id}] Collection interval: {settings.WORKER_COLLECTION_INTERVAL}s")

        try:
            # Run first collection immediately
            await self.run_collection_cycle()

            # Then run on schedule
            while True:
                try:
                    await asyncio.sleep(settings.WORKER_COLLECTION_INTERVAL)
                    await self.run_collection_cycle()

                except asyncio.CancelledError:
                    logger.info(f"[{self.aws_account_id}] Worker received cancellation signal")
                    break

                except Exception as e:
                    logger.error(f"[{self.aws_account_id}] Error in worker loop: {e}", exc_info=True)
                    logger.info(f"[{self.aws_account_id}] Waiting 60s before retry...")
                    await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"[{self.aws_account_id}] Fatal error in worker: {e}", exc_info=True)

        finally:
            logger.info(f"[{self.aws_account_id}] Cloud Health Worker Stopped")