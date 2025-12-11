from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.aws.client import AWSClientProvider
from app.services.aws.ec2 import EC2Scanner
from app.services.aws.s3 import S3Scanner
from app.services.aws.guardduty import GuardDutyScanner
from app.services.aws.costexplorer import CostExplorerScanner
from app.services.aws.cloudwatch import CloudWatchScanner
from app.services.analytics.analyzer import ArchitectureAnalyzer
from app.api.middleware.dependency import get_aws_client_provider, get_current_client_id_dependency
from app.services.cache_client.redis_client import cache
from app.database.dynamodb import DynamoDBConnection
import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/architecture/analyze", tags=["Architecture"])
async def analyze_architecture(
    client_provider: AWSClientProvider = Depends(get_aws_client_provider),
    client_id: str = Depends(get_current_client_id_dependency),
    force_refresh: bool = Query(False, description="Force fresh data collection"),
    save_report: bool = Query(True, description="Save analysis report to database")
):
    """
    Comprehensive architecture analysis endpoint.

    Analyzes customer's cloud architecture across multiple dimensions:
    - AWS Well-Architected Framework (5 pillars)
    - Cost optimization opportunities
    - Performance metrics and bottlenecks
    - Security posture assessment
    - Reliability and fault tolerance
    - Actionable recommendations

    Returns a complete architecture health report with scores and insights.
    """
    try:
        # Check cache first
        cache_key = f'architecture:analysis:{client_id}'

        if not force_refresh:
            cached_report = cache.get(cache_key)
            if cached_report:
                logger.info(f"Returning cached architecture analysis for client {client_id}")
                return {
                    **cached_report,
                    'source': 'cache',
                    'cached': True
                }

        logger.info(f"Starting comprehensive architecture analysis for client {client_id}")

        # Collect data from all AWS services in parallel
        loop = asyncio.get_running_loop()

        # Initialize scanners
        ec2_scanner = EC2Scanner(client_provider)
        s3_scanner = S3Scanner(client_provider)
        guardduty_scanner = GuardDutyScanner(client_provider)
        cost_scanner = CostExplorerScanner(client_provider)
        cloudwatch_scanner = CloudWatchScanner(client_provider)

        # Parallel data collection
        logger.info("Collecting data from AWS services...")

        ec2_data_task = loop.run_in_executor(None, ec2_scanner.scan_all_regions)
        s3_data_task = loop.run_in_executor(None, s3_scanner.list_all_buckets)
        guardduty_task = loop.run_in_executor(None, guardduty_scanner.scan_all_regions)

        # Cost data for last 30 days
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)
        cost_task = loop.run_in_executor(
            None,
            cost_scanner.get_total_cost,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )

        # Wait for all data collection to complete
        ec2_report, s3_report, guardduty_report, cost_report = await asyncio.gather(
            ec2_data_task,
            s3_data_task,
            guardduty_task,
            cost_task
        )

        logger.info("Data collection complete. Processing architecture analysis...")

        # Extract EC2 instances from report
        # Note: ec2_report has flat 'instances' array, not nested 'regions'
        ec2_instances = []
        for instance in ec2_report.get('instances', []):
            # Extract region from Placement.AvailabilityZone (e.g., "us-east-1a" -> "us-east-1")
            az = instance.get('Placement', {}).get('AvailabilityZone', '')
            region = az[:-1] if az else 'unknown'  # Remove last character (zone letter)

            ec2_instances.append({
                'instance_id': instance.get('InstanceId'),
                'instance_type': instance.get('InstanceType'),
                'state': instance.get('State', {}).get('Name'),
                'region': region,
                'availability_zone': az,
                'tags': instance.get('Tags', [])
            })

        # Extract S3 buckets
        s3_buckets = []
        for bucket in s3_report.get('buckets', []):
            s3_buckets.append({
                'name': bucket.get('Name'),
                'region': bucket.get('Region', 'us-east-1'),
                'encryption_enabled': bucket.get('encryption_enabled', False),
                'public_access': bucket.get('public_access', False),
                'size_bytes': bucket.get('size_bytes', 0),
                'object_count': bucket.get('object_count', 0)
            })

        # Extract security findings
        security_findings = []
        for region_data in guardduty_report.get('regions', []):
            for finding in region_data.get('findings', []):
                security_findings.append({
                    'id': finding.get('finding_id'),
                    'title': finding.get('title', 'Security Finding'),
                    'severity': finding.get('severity_label', 'MEDIUM'),  # Use severity_label (CRITICAL/HIGH/etc)
                    'type': finding.get('type'),
                    'region': region_data.get('region')
                })

        # Process cost data
        cost_data = {
            'total_cost': cost_report.get('total_cost', 0),
            'by_service': cost_report.get('by_service', {})
        }

        # Get CloudWatch metrics for performance analysis
        # Try to get CPU metrics for EC2 instances
        cloudwatch_metrics = {}
        if ec2_instances:
            try:
                # Get metrics for first instance as sample
                instance_id = ec2_instances[0].get('instance_id')
                region = ec2_instances[0].get('region', 'us-east-1')

                cpu_metrics = await loop.run_in_executor(
                    None,
                    cloudwatch_scanner.get_metric_statistics,
                    region,
                    'AWS/EC2',
                    'CPUUtilization',
                    {'Name': 'InstanceId', 'Value': instance_id},
                    3600  # 1 hour period
                )
                cloudwatch_metrics['CPUUtilization'] = cpu_metrics
            except Exception as e:
                logger.warning(f"Could not fetch CloudWatch metrics: {str(e)}")
                cloudwatch_metrics = {}

        # Initialize analyzer and run comprehensive analysis
        analyzer = ArchitectureAnalyzer(client_id=client_id)

        analysis_report = await analyzer.analyze_full_architecture(
            ec2_data=ec2_instances,
            s3_data=s3_buckets,
            cost_data=cost_data,
            security_findings=security_findings,
            cloudwatch_metrics=cloudwatch_metrics
        )

        logger.info(f"Architecture analysis complete. Overall score: {analysis_report['overall_score']}")

        # Save report to DynamoDB if requested
        if save_report:
            try:
                await _save_architecture_report(
                    client_id=client_id,
                    report=analysis_report
                )
                logger.info("Architecture report saved to database")
            except Exception as e:
                logger.error(f"Failed to save report to database: {str(e)}")

        # Cache the report for 1 hour
        cache.set(cache_key, analysis_report, ttl=3600)

        return {
            **analysis_report,
            'source': 'aws',
            'cached': False
        }

    except Exception as e:
        logger.error(f"Architecture analysis error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Architecture analysis failed: {str(e)}"
        )


@router.get("/architecture/score", tags=["Architecture"])
async def get_architecture_score(
    client_provider: AWSClientProvider = Depends(get_aws_client_provider),
    client_id: str = Depends(get_current_client_id_dependency)
):
    """
    Get quick architecture health score without full analysis.
    Returns cached score if available, otherwise triggers full analysis.
    """
    try:
        cache_key = f'architecture:analysis:{client_id}'
        cached_report = cache.get(cache_key)

        if cached_report:
            return {
                'client_id': client_id,
                'overall_score': cached_report.get('overall_score', 0),
                'overall_rating': cached_report.get('overall_rating', 'Unknown'),
                'analysis_timestamp': cached_report.get('analysis_timestamp'),
                'cached': True
            }
        else:
            # Trigger full analysis
            full_report = await analyze_architecture(
                client_provider=client_provider,
                client_id=client_id,
                force_refresh=False,
                save_report=True
            )

            return {
                'client_id': client_id,
                'overall_score': full_report.get('overall_score', 0),
                'overall_rating': full_report.get('overall_rating', 'Unknown'),
                'analysis_timestamp': full_report.get('analysis_timestamp'),
                'cached': False
            }

    except Exception as e:
        logger.error(f"Error getting architecture score: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get architecture score: {str(e)}"
        )


@router.get("/architecture/recommendations", tags=["Architecture"])
async def get_recommendations(
    client_provider: AWSClientProvider = Depends(get_aws_client_provider),
    client_id: str = Depends(get_current_client_id_dependency),
    priority: Optional[str] = Query(None, description="Filter by priority: CRITICAL, HIGH, MEDIUM, LOW")
):
    """
    Get architecture improvement recommendations.
    Can filter by priority level.
    """
    try:
        cache_key = f'architecture:analysis:{client_id}'
        cached_report = cache.get(cache_key)

        if not cached_report:
            # Trigger full analysis
            cached_report = await analyze_architecture(
                client_provider=client_provider,
                client_id=client_id,
                force_refresh=False,
                save_report=True
            )

        recommendations = cached_report.get('recommendations', [])

        # Filter by priority if specified
        if priority:
            priority_upper = priority.upper()
            recommendations = [
                rec for rec in recommendations
                if rec.get('priority') == priority_upper
            ]

        return {
            'client_id': client_id,
            'total_recommendations': len(recommendations),
            'recommendations': recommendations,
            'analysis_timestamp': cached_report.get('analysis_timestamp')
        }

    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recommendations: {str(e)}"
        )


@router.get("/architecture/cost-optimization", tags=["Architecture"])
async def get_cost_optimization(
    client_provider: AWSClientProvider = Depends(get_aws_client_provider),
    client_id: str = Depends(get_current_client_id_dependency)
):
    """
    Get detailed cost optimization analysis and potential savings.
    """
    try:
        cache_key = f'architecture:analysis:{client_id}'
        cached_report = cache.get(cache_key)

        if not cached_report:
            cached_report = await analyze_architecture(
                client_provider=client_provider,
                client_id=client_id,
                force_refresh=False,
                save_report=True
            )

        cost_analysis = cached_report.get('cost_analysis', {})

        # Get cost-related recommendations
        recommendations = cached_report.get('recommendations', [])
        cost_recommendations = [
            rec for rec in recommendations
            if rec.get('category') == 'Cost Optimization'
        ]

        return {
            'client_id': client_id,
            'cost_analysis': cost_analysis,
            'recommendations': cost_recommendations,
            'analysis_timestamp': cached_report.get('analysis_timestamp')
        }

    except Exception as e:
        logger.error(f"Error getting cost optimization: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cost optimization data: {str(e)}"
        )


@router.get("/architecture/well-architected", tags=["Architecture"])
async def get_well_architected_scores(
    client_provider: AWSClientProvider = Depends(get_aws_client_provider),
    client_id: str = Depends(get_current_client_id_dependency)
):
    """
    Get AWS Well-Architected Framework pillar scores.
    """
    try:
        cache_key = f'architecture:analysis:{client_id}'
        cached_report = cache.get(cache_key)

        if not cached_report:
            cached_report = await analyze_architecture(
                client_provider=client_provider,
                client_id=client_id,
                force_refresh=False,
                save_report=True
            )

        well_architected = cached_report.get('well_architected', {})

        return {
            'client_id': client_id,
            'well_architected_framework': well_architected,
            'analysis_timestamp': cached_report.get('analysis_timestamp')
        }

    except Exception as e:
        logger.error(f"Error getting well-architected scores: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get well-architected scores: {str(e)}"
        )


async def _save_architecture_report(client_id: str, report: dict):
    """Save architecture analysis report to DynamoDB."""
    try:
        db = DynamoDBConnection()
        table = db.get_table('CloudHealthMetrics')

        if table:
            table.put_item(
                Item={
                    'client_id': client_id,
                    'metric_type': 'architecture_analysis',
                    'timestamp': report['analysis_timestamp'],
                    'data': report,
                    'ttl': int((datetime.utcnow() + timedelta(days=90)).timestamp())
                }
            )
    except Exception as e:
        logger.error(f"Error saving architecture report: {str(e)}")
        raise