from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.aws.client import AWSClientProvider
from app.services.aws.cloudwatch import CloudWatchScanner
from app.api.middleware.dependency import get_aws_client_provider
from app.services.cache_client.redis_client import cache
import asyncio
import logging
from datetime import datetime, timedelta, UTC

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/cloudwatch/metrics", tags=["CloudWatch"])
async def get_cloudwatch_metrics(
        namespace: str = Query(..., description="CloudWatch namespace, e.g. AWS/EC2"),
        metric_name: str = Query(..., description="Metric name, e.g. CPUUtilization"),
        dimensions: str | None = Query(
            None,
            description="Optional dimensions, format: Name1:Value1,Name2:Value2"
        ),
        start_minutes_ago: int = 60,
        period: int = 300,
        stat: str = "Average",
        force_refresh: bool = False,
        client_provider: AWSClientProvider = Depends(get_aws_client_provider)
):
    """
    Scan CloudWatch metrics across all regions.
    Can specify dimensions to filter data by specific resource.
    """

    try:
        # --- Parse optional dimensions ---
        dimension_list = []
        if dimensions:
            try:
                for pair in dimensions.split(","):
                    name, value = pair.split(":", 1)
                    dimension_list.append({"Name": name.strip(), "Value": value.strip()})
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid dimensions format. Use Name:Value,Name:Value"
                )

        # --- Prepare cache key ---
        dim_key = dimensions or "none"
        cache_key = f"cloudwatch:{namespace}:{metric_name}:{period}:{stat}:{dim_key}"

        if not force_refresh:
            cache_data = cache.get(cache_key)
            if cache_data:
                logger.info("Returning cached CloudWatch data")
                return {
                    **cache_data,
                    "source": "cache",
                    "cached": True
                }

        # --- Set time range ---
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(minutes=start_minutes_ago)

        # --- Run scan in threadpool (non-blocking) ---
        scanner = CloudWatchScanner(client_provider)
        loop = asyncio.get_running_loop()

        report = await loop.run_in_executor(
            None,
            scanner.scan_all_regions,
            namespace,
            metric_name,
            dimension_list,
            start_time,
            end_time,
            period,
            stat
        )

        cache.set(cache_key, report, ttl=300)

        return {
            **report,
            "source": "aws",
            "cached": False
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("CloudWatch scan error")
        raise HTTPException(status_code=500, detail=f"CloudWatch scan error: {str(e)}")
