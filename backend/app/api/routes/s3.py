from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.aws.client import AWSClientProvider
from app.services.aws.s3 import S3Scanner
from app.api.middleware.dependency import get_aws_client_provider,get_current_client_id_dependency
from app.services.cache_client.redis_client import cache
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/s3/buckets", tags=["S3"])
async def list_buckets(
        force_refresh: bool = False,
        client_provider: AWSClientProvider = Depends(get_aws_client_provider),
        client_id: str = Depends(get_current_client_id_dependency)
):
    """
    List all S3 buckets names and regions.
    """
    try:
        cache_key = f"s3:buckets:list:{client_id}"
        if not force_refresh and (cached := cache.get(cache_key)):
            return {**cached, "source": "cache"}

        scanner = S3Scanner(client_provider)
        loop = asyncio.get_running_loop()
        buckets = await loop.run_in_executor(None, scanner.list_buckets)

        result = {"total_buckets": len(buckets), "buckets": buckets}
        cache.set(cache_key, result, ttl=300)
        return {**result, "source": "aws"}
    except Exception as e:
        logger.exception("Error listing S3 buckets")
        raise HTTPException(status_code=500, detail="Error listing buckets")


@router.get("/s3/bucket/metrics", tags=["S3"])
async def get_bucket_metrics(
        bucket_name: str = Query(..., description="Bucket name"),
        region: str = Query(..., description="Bucket region"),
        force_refresh: bool = False,
        client_provider: AWSClientProvider = Depends(get_aws_client_provider),
        client_id: str = Depends(get_current_client_id_dependency)
):
    """
    Get metrics for ONE specific bucket.
    """
    try:
        cache_key = f"s3:metrics:{bucket_name}:{region}:{client_id}"
        if not force_refresh and (cached := cache.get(cache_key)):
            return {**cached, "source": "cache"}

        scanner = S3Scanner(client_provider)
        loop = asyncio.get_running_loop()
        metrics = await loop.run_in_executor(None, scanner.get_bucket_storage_metrics, bucket_name, region)

        result = {"bucket": bucket_name, "region": region, "metrics": metrics}
        cache.set(cache_key, result, ttl=300)
        return {**result, "source": "aws"}
    except Exception as e:
        logger.exception(f"Error getting metrics for {bucket_name}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/s3/summary", tags=["S3"])
async def get_s3_summary(
        force_refresh: bool = False,
        client_provider: AWSClientProvider = Depends(get_aws_client_provider),
        client_id: str = Depends(get_current_client_id_dependency)
):
    """
    MASTER ENDPOINT:
    1. Scans ALL buckets.
    2. Calculates Total Storage (GB).
    3. Returns Top 10 Buckets AND Full List.
    """
    try:
        cache_key = f"s3:summary:dashboard:{client_id}"
        if not force_refresh and (cached := cache.get(cache_key)):
            return {**cached, "source": "cache"}

        scanner = S3Scanner(client_provider)
        loop = asyncio.get_running_loop()

        # 1. Get List of Buckets
        buckets = await loop.run_in_executor(None, scanner.list_buckets)
        if not buckets:
            return {
                "total_storage_gb": 0,
                "top_10_buckets": [],
                "all_buckets_details": [],
                "source": "aws"
            }

        # 2. Helper function to scan a single bucket
        def fetch_metrics(b):
            # This calls the S3Scanner to get real-time size
            m = scanner.get_bucket_storage_metrics(b["bucket"], b["region"])
            return {
                "name": b["bucket"],
                "region": b["region"],
                "size_gb": m.get("size_gb", 0),
                "size_mb": m.get("size_mb", 0),
                "object_count": m.get("ObjectCount", 0)
            }

        # 3. Parallel Scanning (Fast!)
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [loop.run_in_executor(executor, fetch_metrics, b) for b in buckets]
            for f in asyncio.as_completed(futures):
                results.append(await f)

        # 4. AGGREGATION LOGIC
        # Sum up all GB
        total_storage_gb = sum(r['size_gb'] for r in results)

        # Sort by size_gb (Largest first)
        sorted_buckets = sorted(results, key=lambda x: x['size_gb'], reverse=True)

        # Take Top 10
        top_10 = sorted_buckets[:10]

        ft_check = False
        ft_client = client_provider.get_client("freetier", region_name="us-east-1")
        response = ft_client.get_free_tier_usage()

        if response:
            # Calculate Free Tier Usage (5GB Limit)
            usage_percent = (total_storage_gb / 5.0) * 100
            ft_check = True
        else:
            usage_percent = 0
            ft_check = False

        data = {
            "total_buckets": len(buckets),
            "total_storage_gb": round(total_storage_gb, 4),
            "free_tier_usage_percent": round(usage_percent, 2),
            "top_10_buckets": top_10,
            "all_buckets_details": sorted_buckets,
            "free_tier_check": ft_check
        }

        cache.set(cache_key, data, ttl=600)
        return {**data, "source": "aws"}

    except Exception as e:
        logger.exception("Error generating S3 summary")
        raise HTTPException(status_code=500, detail=str(e))