# backend/app/worker.py
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from app.config import settings
from app.database.models import (
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CloudHealthWorker:
    """
    Background worker that:
    1. Collects data from AWS using scanners
    2. Saves data to DynamoDB using models
    3. Runs continuously on a schedule
    """

    def __init__(self):
        logger.info("Initializing Cloud Health Worker...")

        # Initialize database models (Layer 2 - CRUD)
        self.metrics_model = MetricsModel()
        self.costs_model = CostsModel()
        self.security_model = SecurityFindingModel()
        self.recommendation_model = RecommendationModel()

        # Initialize AWS client provider
        if not settings.YOUR_AWS_ACCESS_KEY_ID or not settings.YOUR_AWS_SECRET_ACCESS_KEY:
            raise ValueError(
                "YOUR_AWS_ACCESS_KEY_ID and YOUR_AWS_SECRET_ACCESS_KEY must be set in config!"
            )

        self.client_provider = AWSClientProvider(
            access_key=settings.YOUR_AWS_ACCESS_KEY_ID,
            secret_key=settings.YOUR_AWS_SECRET_ACCESS_KEY,
            region=settings.YOUR_AWS_REGION
        )

        # Initialize AWS scanners (Layer 1 - Data Collection)
        self.ec2_scanner = EC2Scanner(self.client_provider)
        self.guardduty_scanner = GuardDutyScanner(self.client_provider)
        self.cost_scanner = CostExplorerScanner(self.client_provider)
        self.s3_scanner = S3Scanner(self.client_provider)
        self.cloudwatch_scanner = CloudWatchScanner(self.client_provider)

        logger.info("Cloud Health Worker initialized successfully!")

    # ═══════════════════════════════════════════════════════════════
    # EC2 METRICS COLLECTION
    # ═══════════════════════════════════════════════════════════════

    async def collect_ec2_metrics(self):
        """
        Collect EC2 metrics and save to DynamoDB in guide format:

        Table: CloudHealthMetrics
        pk: "EC2#MetricName"
        sk: "2025-09-22T14:30:00Z"
        gsi1_pk: "MetricName#2025-09-22T14:30:00Z"
        value: 10
        unit: "Count"
        dimensions: {...}
        ttl: 1669824000
        """
        try:
            logger.info("Collecting EC2 metrics...")

            #COLLECT: Get data from AWS
            summary = self.ec2_scanner.get_instance_summary()
            timestamp = datetime.now()

            #SAVE: Store total instances
            await self.metrics_model.store_metric(
                service="EC2",
                metric_name="TotalInstances",
                value=float(summary.get('total_instances', 0)),
                timestamp=timestamp,
                unit="Count",
                dimensions={}
            )
            logger.info(f"Saved EC2#TotalInstances = {summary.get('total_instances', 0)}")

            #SAVE: Store running instances
            running = summary.get('by_state', {}).get('running', 0)
            await self.metrics_model.store_metric(
                service="EC2",
                metric_name="RunningInstances",
                value=float(running),
                timestamp=timestamp,
                unit="Count",
                dimensions={}
            )
            logger.info(f"Saved EC2#RunningInstances = {running}")

            #SAVE: Store stopped instances
            stopped = summary.get('by_state', {}).get('stopped', 0)
            await self.metrics_model.store_metric(
                service="EC2",
                metric_name="StoppedInstances",
                value=float(stopped),
                timestamp=timestamp,
                unit="Count",
                dimensions={}
            )
            logger.info(f"Saved EC2#StoppedInstances = {stopped}")

            # SAVE: Store instance count by type
            for instance_type, count in summary.get('by_type', {}).items():
                await self.metrics_model.store_metric(
                    service="EC2",
                    metric_name="InstancesByType",
                    value=float(count),
                    timestamp=timestamp,
                    unit="Count",
                    dimensions={"InstanceType": instance_type}
                )
                logger.info(f"Saved EC2#InstancesByType[{instance_type}] = {count}")

            logger.info("EC2 metrics collection completed!")

        except Exception as e:
            logger.error(f"Error collecting EC2 metrics: {e}", exc_info=True)

    # ═══════════════════════════════════════════════════════════════
    # COST DATA COLLECTION
    # ═══════════════════════════════════════════════════════════════

    async def collect_cost_data(self):
        """
        Collect cost data and save to DynamoDB in guide format:

        Table: CloudHealthCosts
        pk: "EC2"
        sk: "2025-09-22#DAILY"
        cost: 12.45
        usage_quantity: 24.0
        usage_unit: "Hrs"
        currency: "USD"
        ttl: 1672502400
        """
        try:
            logger.info("Collecting cost data...")

            #COLLECT: Get cost data from AWS Cost Explorer
            today = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now().replace(day=1)).strftime('%Y-%m-%d')

            cost_data = self.cost_scanner.get_cost_by_service(
                start_date=start_date,
                end_date=today,
                granularity="DAILY"
            )

            #SAVE: Store cost data for each service
            for result in cost_data.get('ResultsByTime', []):
                date = result['TimePeriod']['Start']

                for group in result.get('Groups', []):
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])

                    # Get usage quantity if available
                    usage_quantity = None
                    usage_unit = None
                    if 'UsageQuantity' in group['Metrics']:
                        usage_quantity = float(group['Metrics']['UsageQuantity']['Amount'])
                        usage_unit = group['Metrics']['UsageQuantity'].get('Unit', 'Units')

                    await self.costs_model.store_cost_data(
                        service=service,
                        date=date,
                        cost=cost,
                        usage_quantity=usage_quantity,
                        usage_unit=usage_unit,
                        granularity="DAILY"
                    )
                    logger.info(f"Saved {service} cost for {date} = ${cost:.2f}")

            logger.info("Cost data collection completed!")

        except Exception as e:
            logger.error(f"Error collecting cost data: {e}", exc_info=True)

    # ═══════════════════════════════════════════════════════════════
    # SECURITY FINDINGS COLLECTION
    # ═══════════════════════════════════════════════════════════════

    async def collect_security_findings(self):
        """
        Collect security findings and save to DynamoDB in guide format:

        Table: SecurityFindings
        pk: "GuardDuty"
        sk: "finding-12345"
        severity: "HIGH"
        status: "ACTIVE"
        title: "Suspicious network traffic detected"
        description: "..."
        service: "EC2"
        resource_id: "i-1234567890abcdef0"
        created_at: "2025-09-22T14:30:00Z"
        updated_at: "2025-09-22T14:30:00Z"
        """
        try:
            logger.info("Collecting security findings...")

            #COLLECT: Get findings from GuardDuty
            findings_data = self.guardduty_scanner.get_all_findings(severity_filter=4)

            #SAVE: Store metrics about findings
            timestamp = datetime.now()

            await self.metrics_model.store_metric(
                service="GuardDuty",
                metric_name="TotalFindings",
                value=float(findings_data.get('total_count', 0)),
                timestamp=timestamp,
                unit="Count",
                dimensions={}
            )
            logger.info(f"Saved GuardDuty#TotalFindings = {findings_data.get('total_count', 0)}")

            # Save severity breakdown
            severity_breakdown = findings_data.get('severity_breakdown', {})
            for severity, count in severity_breakdown.items():
                await self.metrics_model.store_metric(
                    service="GuardDuty",
                    metric_name="FindingsBySeverity",
                    value=float(count),
                    timestamp=timestamp,
                    unit="Count",
                    dimensions={"Severity": severity}
                )
                logger.info(f"Saved GuardDuty#FindingsBySeverity[{severity}] = {count}")

            #SAVE: Store individual findings
            findings_saved = 0
            for finding in findings_data.get('findings', [])[:50]:  # Limit to 50 latest
                await self.security_model.store_finding(
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

            logger.info(f"Saved {findings_saved} individual findings to SecurityFindings table")
            logger.info("Security findings collection completed!")

        except Exception as e:
            logger.error(f"Error collecting security findings: {e}", exc_info=True)

    # ═══════════════════════════════════════════════════════════════
    # S3 METRICS COLLECTION
    # ═══════════════════════════════════════════════════════════════

    async def collect_s3_metrics(self):
        """
        Collect S3 metrics and save to DynamoDB in guide format
        """
        try:
            logger.info("Collecting S3 metrics...")

            #COLLECT: Get S3 bucket information
            s3_data = self.s3_scanner.scan_all_buckets()
            timestamp = datetime.now()

            #SAVE: Store total bucket count
            await self.metrics_model.store_metric(
                service="S3",
                metric_name="TotalBuckets",
                value=float(s3_data.get('total_buckets', 0)),
                timestamp=timestamp,
                unit="Count",
                dimensions={}
            )
            logger.info(f"Saved S3#TotalBuckets = {s3_data.get('total_buckets', 0)}")

            #SAVE: Store storage metrics for each bucket
            for bucket in s3_data.get('buckets', []):
                metrics = bucket.get('metrics', {})

                if 'StandardStorageBytes' in metrics:
                    storage_gb = metrics['StandardStorageBytes'] / (1024 ** 3)  # Convert to GB
                    await self.metrics_model.store_metric(
                        service="S3",
                        metric_name="StorageSize",
                        value=storage_gb,
                        timestamp=timestamp,
                        unit="Gigabytes",
                        dimensions={"BucketName": bucket['bucket']}
                    )
                    logger.info(f"Saved S3#StorageSize[{bucket['bucket']}] = {storage_gb:.2f} GB")

                if 'ObjectCount' in metrics:
                    await self.metrics_model.store_metric(
                        service="S3",
                        metric_name="ObjectCount",
                        value=float(metrics['ObjectCount']),
                        timestamp=timestamp,
                        unit="Count",
                        dimensions={"BucketName": bucket['bucket']}
                    )
                    logger.info(f"Saved S3#ObjectCount[{bucket['bucket']}] = {metrics['ObjectCount']}")

            logger.info("S3 metrics collection completed!")

        except Exception as e:
            logger.error(f"Error collecting S3 metrics: {e}", exc_info=True)

    # ═══════════════════════════════════════════════════════════════
    # RECOMMENDATIONS GENERATION
    # ═══════════════════════════════════════════════════════════════

    async def generate_recommendations(self):
        """
        Generate and save recommendations to DynamoDB in guide format:

        Table: Recommendations
        pk: "cost"
        sk: "2025-09-22T14:30:00Z#rec-123"
        title: "Rightsize EC2 instance"
        description: "Consider downsizing to t3.small"
        impact: "HIGH"
        effort: "LOW"
        confidence: 0.85
        estimated_savings: 50.0
        service: "EC2"
        resource_id: "i-1234567890abcdef0"
        implemented: false
        """
        try:
            logger.info("Generating recommendations...")

            #COLLECT: Get EC2 cost data
            cost_estimate = self.ec2_scanner.estimate_monthly_cost()

            #ANALYZE: Find optimization opportunities
            recommendations_generated = 0

            for instance_cost in cost_estimate.get('cost_breakdown', []):
                estimated_cost = instance_cost.get('estimated_cost', 0)
                instance_id = instance_cost.get('instance_id')
                instance_type = instance_cost.get('instance_type')

                # Example: Recommend downsizing if cost is high
                if estimated_cost > 50:
                    rec_id = await self.recommendation_model.store_recommendation(
                        rec_type="cost",
                        title=f"Consider rightsizing {instance_type}",
                        description=f"Instance {instance_id} costs ${estimated_cost:.2f}/month. "
                                    f"Consider reviewing utilization and downsizing if underutilized.",
                        impact="MEDIUM",
                        effort="LOW",
                        confidence=0.75,
                        service="EC2",
                        estimated_savings=estimated_cost * 0.3,  # Estimate 30% savings
                        resource_id=instance_id
                    )
                    if rec_id:
                        logger.info(f"Created recommendation {rec_id} for {instance_id}")
                        recommendations_generated += 1

            #SAVE: Store GuardDuty-based security recommendations
            findings_data = self.guardduty_scanner.get_findings_summary()

            if findings_data.get('critical_count', 0) > 0:
                rec_id = await self.recommendation_model.store_recommendation(
                    rec_type="security",
                    title="Review critical security findings",
                    description=f"Found {findings_data.get('critical_count', 0)} critical security findings. "
                                f"Immediate review recommended.",
                    impact="HIGH",
                    effort="MEDIUM",
                    confidence=0.95,
                    service="GuardDuty",
                    estimated_savings=None,
                    resource_id=None
                )
                if rec_id:
                    logger.info(f"Created security recommendation {rec_id}")
                    recommendations_generated += 1

            logger.info(f"Generated {recommendations_generated} recommendations!")

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}", exc_info=True)

    # ═══════════════════════════════════════════════════════════════
    # MAIN COLLECTION CYCLE
    # ═══════════════════════════════════════════════════════════════

    async def run_collection_cycle(self):
        """
        Run one complete data collection cycle
        """
        cycle_start = datetime.now()
        logger.info("=" * 70)
        logger.info(f"🔄 Starting collection cycle at {cycle_start.isoformat()}")
        logger.info("=" * 70)

        # Run all collection tasks
        await self.collect_ec2_metrics()
        await self.collect_cost_data()
        await self.collect_security_findings()
        await self.collect_s3_metrics()
        await self.generate_recommendations()

        cycle_end = datetime.now()
        duration = (cycle_end - cycle_start).total_seconds()

        logger.info("=" * 70)
        logger.info(f"Collection cycle completed in {duration:.2f} seconds")
        logger.info("=" * 70)

    async def start(self):
        """
        Start the background worker with continuous collection
        """
        logger.info("Cloud Health Background Worker Starting!")
        logger.info(f"Collection interval: {settings.METRICS_COLLECTION_INTERVAL} seconds")
        logger.info(f"Database: DynamoDB")
        logger.info(f"AWS Region: {settings.YOUR_AWS_REGION}")

        # Run first collection immediately
        await self.run_collection_cycle()

        # Then run on schedule
        while True:
            try:
                await asyncio.sleep(settings.METRICS_COLLECTION_INTERVAL)
                await self.run_collection_cycle()

            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                break
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                logger.info("Waiting 60 seconds before retry...")
                await asyncio.sleep(60)

        logger.info("Cloud Health Background Worker Stopped")

        async def start(self):
            """
            Start the background worker with continuous collection
            """
            logger.info("Cloud Health Background Worker Starting!")
            logger.info(f"Collection interval: {settings.METRICS_COLLECTION_INTERVAL} seconds")
            logger.info(f"Database: DynamoDB")
            logger.info(f"AWS Region: {settings.YOUR_AWS_REGION}")

            # Run first collection immediately
            try:
                await self.run_collection_cycle()
            except Exception as e:
                logger.error(f"First collection failed: {e}")

            # Then run on schedule
            while True:
                try:
                    await asyncio.sleep(settings.METRICS_COLLECTION_INTERVAL)
                    await self.run_collection_cycle()

                except asyncio.CancelledError:
                    # Handle graceful shutdown
                    logger.info("Worker received cancellation signal")
                    break
                except Exception as e:
                    logger.error(f"Error in worker loop: {e}", exc_info=True)
                    logger.info("Waiting 60 seconds before retry...")
                    await asyncio.sleep(60)

            logger.info("Cloud Health Background Worker Stopped")


