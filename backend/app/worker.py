import asyncio
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from app.services.cache_client.redis_client import cache
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
from app.services.analytics.analyzer import ArchitectureAnalyzer
from app.utils.jwt_handler import decode_refresh_token
from app.config import settings
import gc

logger = logging.getLogger(__name__)


class CloudHealthWorker:
    """
    Background worker for a single client that:
    1. Collects data from client's AWS account using their credentials
    2. Saves data to DynamoDB with client_id for multi-tenant isolation
    3. Runs continuously on a schedule
    4. Sends email alerts for critical security findings

    OPTIMIZED: Uses true parallel execution with asyncio.to_thread()
    """

    def __init__(self, client_provider: AWSClientProvider, aws_account_id: str, refresh_token: str):
        """
        Initialize worker for a specific client
        """
        logger.info(f"[{aws_account_id}] Initializing Cloud Health Worker...")

        self.client_provider = client_provider
        self.aws_account_id = aws_account_id
        self.refresh_token = refresh_token
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

    # =========================================================================
    # PHASE 1: Data Collection (True Parallel with asyncio.to_thread)
    # =========================================================================

    async def _fetch_ec2_data(self) -> dict:
        """Fetch EC2 data in background thread (non-blocking)"""
        logger.info(f"[{self.aws_account_id}] Fetching EC2 data...")
        # to_thread makes blocking boto3 calls run in parallel
        result = await asyncio.to_thread(self.ec2_scanner.scan_all_regions)
        logger.info(f"[{self.aws_account_id}] EC2: {len(result.get('instances', []))} instances")
        return result

    async def _fetch_s3_data(self) -> dict:
        """Fetch S3 data in background thread"""
        logger.info(f"[{self.aws_account_id}] Fetching S3 data...")
        result = await asyncio.to_thread(self.s3_scanner.list_all_buckets)
        logger.info(f"[{self.aws_account_id}] S3: {len(result.get('buckets', []))} buckets")
        return result

    async def _fetch_cost_data(self) -> dict:
        """Fetch cost data in background thread"""
        logger.info(f"[{self.aws_account_id}] Fetching cost data...")
        today = datetime.now().strftime('%Y-%m-%d')
        start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')

        result = await asyncio.to_thread(
            self.cost_scanner.get_cost_by_service,
            start_date,
            today,
            "DAILY"
        )
        logger.info(f"[{self.aws_account_id}] Cost: {len(result.get('ResultsByTime', []))} time periods")
        return result

    async def _fetch_security_data(self) -> dict:
        """Fetch GuardDuty data in background thread"""
        logger.info(f"[{self.aws_account_id}] Fetching security data...")
        try:
            result = await asyncio.to_thread(
                self.guardduty_scanner.get_all_findings,
                4  # severity_filter
            )
            logger.info(f"[{self.aws_account_id}] Security: {result.get('total_count', 0)} findings")
            return result
        except Exception as e:
            # Handle GuardDuty not enabled
            if 'SubscriptionRequiredException' in str(e):
                logger.warning(f"[{self.aws_account_id}] GuardDuty not enabled, skipping")
                return {'findings': [], 'total_count': 0, 'severity_breakdown': {}}
            raise

    async def _fetch_guardduty_regions(self) -> dict:
        """Fetch GuardDuty regional scan for architecture analysis"""
        logger.info(f"[{self.aws_account_id}] Fetching GuardDuty regions...")
        try:
            result = await asyncio.to_thread(self.guardduty_scanner.scan_all_regions)
            return result
        except Exception as e:
            if 'SubscriptionRequiredException' in str(e):
                logger.warning(f"[{self.aws_account_id}] GuardDuty not enabled")
                return {'regions': []}
            raise

    # =========================================================================
    # PHASE 2: Data Storage (uses fetched data)
    # =========================================================================

    async def _store_ec2_metrics(self, ec2_data: dict):
        """Store EC2 metrics from pre-fetched data"""
        try:
            # Get summary from the already-fetched data
            instances = ec2_data.get('instances', [])
            if not instances:
                logger.info(f"[{self.aws_account_id}] No EC2 instances to store")
                return

            timestamp = datetime.now()

            # Count by state
            by_state = {}
            by_type = {}
            for inst in instances:
                state = inst.get('State', {}).get('Name', 'unknown')
                inst_type = inst.get('InstanceType', 'unknown')
                by_state[state] = by_state.get(state, 0) + 1
                by_type[inst_type] = by_type.get(inst_type, 0) + 1

            # Store total
            await self.metrics_model.store_metric(
                aws_account_id=self.aws_account_id,
                service="EC2",
                metric_name="TotalInstances",
                value=float(len(instances)),
                timestamp=timestamp,
                unit="Count",
                dimensions={}
            )

            # Store by state
            for state, count in by_state.items():
                await self.metrics_model.store_metric(
                    aws_account_id=self.aws_account_id,
                    service="EC2",
                    metric_name=f"{state.capitalize()}Instances",
                    value=float(count),
                    timestamp=timestamp,
                    unit="Count",
                    dimensions={"State": state}
                )

            # Store by type
            for instance_type, count in by_type.items():
                await self.metrics_model.store_metric(
                    aws_account_id=self.aws_account_id,
                    service="EC2",
                    metric_name="InstancesByType",
                    value=float(count),
                    timestamp=timestamp,
                    unit="Count",
                    dimensions={"InstanceType": instance_type}
                )

            logger.info(f"[{self.aws_account_id}] EC2 metrics stored!")

        except Exception as e:
            logger.error(f"[{self.aws_account_id}] Error storing EC2 metrics: {e}", exc_info=True)

    async def _store_cost_data(self, cost_data: dict):
        """Store cost data from pre-fetched data"""
        try:
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
                        aws_account_id=self.aws_account_id,
                        service=service,
                        date=date,
                        cost=cost,
                        usage_quantity=usage_quantity,
                        usage_unit=usage_unit,
                        granularity="DAILY"
                    )
                    saved_count += 1

            logger.info(f"[{self.aws_account_id}] Cost data stored! ({saved_count} records)")

        except Exception as e:
            logger.error(f"[{self.aws_account_id}] Error storing cost data: {e}", exc_info=True)

    async def _store_security_findings(self, security_data: dict):
        """Store security findings from pre-fetched data"""
        try:
            timestamp = datetime.now()

            await self.metrics_model.store_metric(
                aws_account_id=self.aws_account_id,
                service="GuardDuty",
                metric_name="TotalFindings",
                value=float(security_data.get('total_count', 0)),
                timestamp=timestamp,
                unit="Count",
                dimensions={}
            )

            # Store severity breakdown
            severity_breakdown = security_data.get('severity_breakdown', {})
            for severity, count in severity_breakdown.items():
                await self.metrics_model.store_metric(
                    aws_account_id=self.aws_account_id,
                    service="GuardDuty",
                    metric_name="FindingsBySeverity",
                    value=float(count),
                    timestamp=timestamp,
                    unit="Count",
                    dimensions={"Severity": severity}
                )

            # Store individual findings
            findings_saved = 0
            for finding in security_data.get('findings', [])[:50]:
                await self.security_model.store_finding(
                    aws_account_id=self.aws_account_id,
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

            # Send email alerts
            await self._send_critical_alerts(security_data)

            logger.info(f"[{self.aws_account_id}] Security findings stored!")

        except Exception as e:
            logger.error(f"[{self.aws_account_id}] Error storing security findings: {e}", exc_info=True)

    async def _store_s3_metrics(self, s3_data: dict):
        """Store S3 metrics from pre-fetched data"""
        try:
            timestamp = datetime.now()

            await self.metrics_model.store_metric(
                aws_account_id=self.aws_account_id,
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
                        aws_account_id=self.aws_account_id,
                        service="S3",
                        metric_name="StorageSize",
                        value=storage_gb,
                        timestamp=timestamp,
                        unit="Gigabytes",
                        dimensions={"BucketName": bucket['bucket']}
                    )

                if 'ObjectCount' in metrics:
                    await self.metrics_model.store_metric(
                        aws_account_id=self.aws_account_id,
                        service="S3",
                        metric_name="ObjectCount",
                        value=float(metrics['ObjectCount']),
                        timestamp=timestamp,
                        unit="Count",
                        dimensions={"BucketName": bucket['bucket']}
                    )

            logger.info(f"[{self.aws_account_id}] S3 metrics stored!")

        except Exception as e:
            logger.error(f"[{self.aws_account_id}] Error storing S3 metrics: {e}", exc_info=True)

    async def _collect_cloudwatch_for_instances(self, ec2_data: dict):
        """Collect CloudWatch metrics for running instances (parallel per instance)"""
        try:
            instances = ec2_data.get('instances', [])
            running = [i for i in instances if i.get('State', {}).get('Name') == 'running']

            if not running:
                logger.info(f"[{self.aws_account_id}] No running instances for CloudWatch")
                return

            logger.info(f"[{self.aws_account_id}] Collecting CloudWatch for {len(running)} instances")
            timestamp = datetime.now()
            metrics_collected = 0

            # Collect metrics for all instances in parallel
            async def get_instance_metrics(instance):
                instance_id = instance.get('InstanceId')
                az = instance.get('Placement', {}).get('AvailabilityZone', '')
                region = az[:-1] if az else None

                if not region:
                    return 0

                collected = 0
                try:
                    # CPU - use to_thread for blocking call
                    cpu = await asyncio.to_thread(
                        self.cloudwatch_scanner.get_ec2_cpu_utilization,
                        instance_id, 1, region
                    )
                    if cpu and 'average' in cpu:
                        await self.metrics_model.store_metric(
                            aws_account_id=self.aws_account_id,
                            service="EC2",
                            metric_name="CPUUtilization",
                            value=float(cpu['average']),
                            timestamp=timestamp,
                            unit="Percent",
                            dimensions={"InstanceId": instance_id, "Region": region}
                        )
                        collected += 1

                    # Network In
                    net_in = await asyncio.to_thread(
                        self.cloudwatch_scanner.get_ec2_network_in,
                        instance_id, 1, region
                    )
                    if net_in and 'average' in net_in:
                        await self.metrics_model.store_metric(
                            aws_account_id=self.aws_account_id,
                            service="EC2",
                            metric_name="NetworkIn",
                            value=float(net_in['average']),
                            timestamp=timestamp,
                            unit="Bytes",
                            dimensions={"InstanceId": instance_id, "Region": region}
                        )
                        collected += 1

                    # Network Out
                    net_out = await asyncio.to_thread(
                        self.cloudwatch_scanner.get_ec2_network_out,
                        instance_id, 1, region
                    )
                    if net_out and 'average' in net_out:
                        await self.metrics_model.store_metric(
                            aws_account_id=self.aws_account_id,
                            service="EC2",
                            metric_name="NetworkOut",
                            value=float(net_out['average']),
                            timestamp=timestamp,
                            unit="Bytes",
                            dimensions={"InstanceId": instance_id, "Region": region}
                        )
                        collected += 1

                except Exception as e:
                    logger.error(f"[{self.aws_account_id}] CloudWatch error for {instance_id}: {e}")

                return collected

            # Run all instance metrics in parallel
            results = await asyncio.gather(
                *[get_instance_metrics(inst) for inst in running],
                return_exceptions=True
            )

            metrics_collected = sum(r for r in results if isinstance(r, int))
            logger.info(f"[{self.aws_account_id}] CloudWatch: {metrics_collected} metrics collected")

        except Exception as e:
            logger.error(f"[{self.aws_account_id}] Error collecting CloudWatch: {e}", exc_info=True)

    async def _run_architecture_analysis(
            self,
            ec2_data: dict,
            s3_data: dict,
            cost_data: dict,
            guardduty_data: dict
    ):
        """Run architecture analysis using already-fetched data (no duplicate API calls!)"""
        try:
            logger.info(f"[{self.aws_account_id}] Running architecture analysis...")

            # Transform EC2 data
            ec2_instances = []
            for instance in ec2_data.get('instances', []):
                az = instance.get('Placement', {}).get('AvailabilityZone', '')
                region = az[:-1] if az else 'unknown'
                ec2_instances.append({
                    'instance_id': instance.get('InstanceId'),
                    'instance_type': instance.get('InstanceType'),
                    'state': instance.get('State', {}).get('Name'),
                    'region': region,
                    'availability_zone': az,
                    'tags': instance.get('Tags', [])
                })

            # Transform S3 data
            s3_buckets = []
            for bucket in s3_data.get('buckets', []):
                s3_buckets.append({
                    'name': bucket.get('Name'),
                    'region': bucket.get('Region', 'us-east-1'),
                    'encryption_enabled': bucket.get('encryption_enabled', False),
                    'public_access': bucket.get('public_access', False),
                    'size_bytes': bucket.get('size_bytes', 0),
                    'object_count': bucket.get('object_count', 0)
                })

            # Transform security findings
            security_findings = []
            for region_data in guardduty_data.get('regions', []):
                for finding in region_data.get('findings', []):
                    security_findings.append({
                        'id': finding.get('finding_id'),
                        'title': finding.get('title', 'Security Finding'),
                        'severity': finding.get('severity_label', 'MEDIUM'),
                        'type': finding.get('type'),
                        'region': region_data.get('region')
                    })

            # Get cost totals from the daily data
            total_cost = 0.0
            by_service = {}
            for result in cost_data.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    total_cost += cost
                    by_service[service] = by_service.get(service, 0) + cost

            cost_processed = {
                'total_cost': total_cost,
                'by_service': by_service
            }

            # Run analysis
            analyzer = ArchitectureAnalyzer(client_id=self.aws_account_id)

            analysis_report = await analyzer.analyze_full_architecture(
                ec2_data=ec2_instances,
                s3_data=s3_buckets,
                cost_data=cost_processed,
                security_findings=security_findings,
                cloudwatch_metrics={}
            )

            # Cache results
            cache_key = f'architecture:analysis:{self.aws_account_id}'
            self.cache.set(cache_key, analysis_report, ttl=3600)

            # Store recommendations - FIX: Check your model's actual parameters
            recommendations = analysis_report.get('recommendations', [])
            if recommendations:
                logger.info(f"[{self.aws_account_id}] Storing {len(recommendations)} recommendations...")
                stored = 0
                for rec in recommendations:
                    try:
                        await self.recommendation_model.store_recommendation(
                            aws_account_id=self.aws_account_id,
                            rec_type=rec.get('category', 'General'),
                            title=rec.get('title', 'Recommendation'),
                            description=rec.get('description', ''),
                            impact=rec.get('impact', ''),
                            effort=rec.get('effort', 'MEDIUM'),
                            confidence=rec.get('confidence', 1.0),
                            service=rec.get('service', 'General'),
                            estimated_savings=rec.get('potential_savings', 0),
                            resource_id=rec.get('resource_id')
                        )
                        stored += 1
                    except Exception as e:
                        logger.error(f"[{self.aws_account_id}] Failed to store recommendation: {e}")

                logger.info(f"[{self.aws_account_id}] Stored {stored}/{len(recommendations)} recommendations")

            logger.info(
                f"[{self.aws_account_id}] Architecture analysis complete! "
                f"Score: {analysis_report.get('overall_score', 0)}/100, "
                f"Recommendations: {len(recommendations)}"
            )

        except Exception as e:
            logger.error(f"[{self.aws_account_id}] Error in architecture analysis: {e}", exc_info=True)

    async def _send_critical_alerts(self, findings_data: Dict):
        """Send email alerts for critical security findings"""
        try:
            client = await self.client_model.get_client(self.aws_account_id)

            if not client or not client.get('email_verified'):
                return

            prefs = client.get('notification_preferences', True)
            if not prefs:
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

    async def _validate_or_refresh_token(self):
        try:
            response = decode_refresh_token(self.refresh_token)
            if response:
                return True
            else:
                logger.info(f"[{self.aws_account_id}] Refresh token expired")
                return False
        except Exception as e:
            logger.error(f"[{self.aws_account_id}] Error validating token: {e}", exc_info=True)
            return False

    # =========================================================================
    # MAIN COLLECTION CYCLE - OPTIMIZED
    # =========================================================================

    async def run_collection_cycle(self):
        """
        OPTIMIZED: Run collection in phases with true parallelism.

        Phase 1: Fetch all data in parallel (uses asyncio.to_thread for blocking calls)
        Phase 2: Store data + CloudWatch (parallel, uses fetched data)
        Phase 3: Architecture analysis (uses fetched data, no re-fetching!)

        After:  ~20-25s (true parallel + data reuse)
        """
        cycle_start = datetime.now()
        logger.info("=" * 70)
        logger.info(f"[{self.aws_account_id}] Starting collection at {cycle_start.isoformat()}")
        logger.info("=" * 70)

        try:
            # =================================================================
            # PHASE 1: Fetch all data in TRUE parallel
            # =================================================================
            phase1_start = datetime.now()
            logger.info(f"[{self.aws_account_id}] Phase 1: Parallel data fetch...")

            # These run truly in parallel because of asyncio.to_thread()
            ec2_data, s3_data, cost_data, security_data, guardduty_regions = await asyncio.gather(
                self._fetch_ec2_data(),
                self._fetch_s3_data(),
                self._fetch_cost_data(),
                self._fetch_security_data(),
                self._fetch_guardduty_regions(),
                return_exceptions=True
            )

            # Handle any exceptions
            if isinstance(ec2_data, Exception):
                logger.error(f"[{self.aws_account_id}] EC2 fetch failed: {ec2_data}")
                ec2_data = {'instances': []}
            if isinstance(s3_data, Exception):
                logger.error(f"[{self.aws_account_id}] S3 fetch failed: {s3_data}")
                s3_data = {'buckets': [], 'total_buckets': 0}
            if isinstance(cost_data, Exception):
                logger.error(f"[{self.aws_account_id}] Cost fetch failed: {cost_data}")
                cost_data = {'ResultsByTime': []}
            if isinstance(security_data, Exception):
                logger.error(f"[{self.aws_account_id}] Security fetch failed: {security_data}")
                security_data = {'findings': [], 'total_count': 0, 'severity_breakdown': {}}
            if isinstance(guardduty_regions, Exception):
                logger.error(f"[{self.aws_account_id}] GuardDuty regions fetch failed: {guardduty_regions}")
                guardduty_regions = {'regions': []}

            phase1_duration = (datetime.now() - phase1_start).total_seconds()
            logger.info(f"[{self.aws_account_id}] Phase 1 completed in {phase1_duration:.2f}s")

            # =================================================================
            # PHASE 2: Store data + CloudWatch (parallel)
            # =================================================================
            phase2_start = datetime.now()
            logger.info(f"[{self.aws_account_id}] Phase 2: Parallel storage + CloudWatch...")

            await asyncio.gather(
                self._store_ec2_metrics(ec2_data),
                self._store_s3_metrics(s3_data),
                self._store_cost_data(cost_data),
                self._store_security_findings(security_data),
                self._collect_cloudwatch_for_instances(ec2_data),
                return_exceptions=True
            )

            phase2_duration = (datetime.now() - phase2_start).total_seconds()
            logger.info(f"[{self.aws_account_id}] Phase 2 completed in {phase2_duration:.2f}s")

            # =================================================================
            # PHASE 3: Architecture analysis (reuses fetched data!)
            # =================================================================
            phase3_start = datetime.now()
            logger.info(f"[{self.aws_account_id}] Phase 3: Architecture analysis...")

            await self._run_architecture_analysis(
                ec2_data=ec2_data,
                s3_data=s3_data,
                cost_data=cost_data,
                guardduty_data=guardduty_regions
            )

            phase3_duration = (datetime.now() - phase3_start).total_seconds()
            logger.info(f"[{self.aws_account_id}] Phase 3 completed in {phase3_duration:.2f}s")

            # =================================================================
            # Cleanup
            # =================================================================
            gc.collect()

            await self.client_model.update_last_collection(self.aws_account_id)
            self.cache.clear_pattern(f"metrics:{self.aws_account_id}:*")
            self.cache.clear_pattern(f"client:{self.aws_account_id}:*")

            cycle_end = datetime.now()
            duration = (cycle_end - cycle_start).total_seconds()

            logger.info("=" * 70)
            logger.info(f"[{self.aws_account_id}] Collection completed in {duration:.2f}s")
            logger.info(
                f"[{self.aws_account_id}] Breakdown: P1={phase1_duration:.1f}s, P2={phase2_duration:.1f}s, P3={phase3_duration:.1f}s")
            logger.info("=" * 70)

        except Exception as e:
            logger.error(f"[{self.aws_account_id}] Collection cycle failed: {e}", exc_info=True)

    async def start(self, initial_delay: int = 5):
        """Start the worker with an optional initial delay."""
        logger.info(f"[{self.aws_account_id}] Cloud Health Worker Starting!")
        logger.info(f"[{self.aws_account_id}] Collection interval: {settings.WORKER_COLLECTION_INTERVAL}s")
        logger.info(f"[{self.aws_account_id}] JWT validation: Enabled (12 hours access, 7 days refresh)")

        if initial_delay > 0:
            logger.info(f"[{self.aws_account_id}] Initial collection will start in {initial_delay} seconds...")

        try:
            if not await self._validate_or_refresh_token():
                logger.error(f"[{self.aws_account_id}] Initial token validation failed")
                return

            if initial_delay > 0:
                await asyncio.sleep(initial_delay)

            await self.run_collection_cycle()

            while True:
                try:
                    await asyncio.sleep(settings.WORKER_COLLECTION_INTERVAL)

                    if not await self._validate_or_refresh_token():
                        logger.error(f"[{self.aws_account_id}] Token validation failed - stopping")
                        break

                    await self.run_collection_cycle()

                except asyncio.CancelledError:
                    logger.info(f"[{self.aws_account_id}] Worker cancelled")
                    break

                except Exception as e:
                    logger.error(f"[{self.aws_account_id}] Error in worker loop: {e}", exc_info=True)
                    await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"[{self.aws_account_id}] Fatal error: {e}", exc_info=True)

        finally:
            logger.info(f"[{self.aws_account_id}] Cloud Health Worker Stopped")

    # =========================================================================
    # LEGACY METHODS (kept for compatibility, but not used in optimized cycle)
    # =========================================================================

    async def collect_ec2_metrics(self):
        """Legacy method - use _fetch_ec2_data + _store_ec2_metrics instead"""
        data = await self._fetch_ec2_data()
        await self._store_ec2_metrics(data)

    async def collect_cost_data(self):
        """Legacy method"""
        data = await self._fetch_cost_data()
        await self._store_cost_data(data)

    async def collect_security_findings(self):
        """Legacy method"""
        data = await self._fetch_security_data()
        await self._store_security_findings(data)

    async def collect_s3_metrics(self):
        """Legacy method"""
        data = await self._fetch_s3_data()
        await self._store_s3_metrics(data)

    async def collect_cloudwatch_metrics(self):
        """Legacy method"""
        ec2_data = await self._fetch_ec2_data()
        await self._collect_cloudwatch_for_instances(ec2_data)

    async def collect_architecture_analysis(self):
        """Legacy method - avoid using, it re-fetches all data"""
        ec2 = await self._fetch_ec2_data()
        s3 = await self._fetch_s3_data()
        cost = await self._fetch_cost_data()
        gd = await self._fetch_guardduty_regions()
        await self._run_architecture_analysis(ec2, s3, cost, gd)