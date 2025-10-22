from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.aws.client import AWSClientProvider
from app.services.aws.s3 import S3Scanner
from app.api.middleware.dependency import get_aws_client_provider
from app.services.cache.redis_client import cache
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/s3/buckets", tags=["S3"])
async def list_buckets(
        force_refresh: bool = False,
        client_provider: AWSClientProvider = Depends(get_aws_client_provider)
):
    """
    Liệt kê tất cả các S3 buckets trong tài khoản và region của chúng.
    """
    try:
        cache_key = "s3:buckets:list"
        if not force_refresh:
            if cached := cache.get(cache_key):
                logger.info("Returning cached S3 bucket list")
                return {**cached, "source": "cache", "cache": True}

        scanner = S3Scanner(client_provider)
        loop = asyncio.get_running_loop()
        buckets = await loop.run_in_executor(None, scanner.list_buckets)

        result = {"total_buckets": len(buckets), "buckets": buckets}
        cache.set(cache_key, result, ttl=300)

        return {**result, "source": "aws", "cache": False}
    except Exception as e:
        logger.exception("Error listing S3 buckets")
        raise HTTPException(status_code=500, detail=f"S3 bucket list error: {str(e)}")


@router.get("/s3/bucket/metrics", tags=["S3"])
async def get_bucket_metrics(
        bucket_name: str = Query(..., description="Tên bucket S3 cần lấy metrics"),
        region: str = Query(..., description="Region của bucket"),
        force_refresh: bool = False,
        client_provider: AWSClientProvider = Depends(get_aws_client_provider)
):
    """
    Lấy thông tin metric (storage size & object count) cho 1 bucket cụ thể.
    """
    try:
        cache_key = f"s3:metrics:{bucket_name}:{region}"
        if not force_refresh:
            if cached := cache.get(cache_key):
                logger.info(f"Returning cached metrics for bucket {bucket_name}")
                return {**cached, "source": "cache", "cache": True}

        scanner = S3Scanner(client_provider)
        loop = asyncio.get_running_loop()
        metrics = await loop.run_in_executor(None, scanner.get_bucket_storage_metrics, bucket_name, region)

        result = {"bucket": bucket_name, "region": region, "metrics": metrics}
        cache.set(cache_key, result, ttl=300)

        return {**result, "source": "aws", "cache": False}
    except Exception as e:
        logger.exception(f"Error fetching S3 metrics for bucket {bucket_name}")
        raise HTTPException(status_code=500, detail=f"S3 bucket metrics error: {str(e)}")


@router.get("/s3/summary", tags=["S3"])
async def get_s3_summary(
        force_refresh: bool = False,
        client_provider: AWSClientProvider = Depends(get_aws_client_provider)
):
    """
    Quét toàn bộ S3 buckets và lấy metrics song song cho từng bucket.
    Trả về tổng quan toàn bộ usage S3.
    """
    try:
        cache_key = "s3:summary:all"
        if not force_refresh:
            if cached := cache.get(cache_key):
                logger.info("Returning cached S3 summary data")
                return {**cached, "source": "cache", "cache": True}

        scanner = S3Scanner(client_provider)
        loop = asyncio.get_running_loop()

        # Step 1: Lấy danh sách buckets
        buckets = await loop.run_in_executor(None, scanner.list_buckets)
        if not buckets:
            return {"total_buckets": 0, "buckets": [], "source": "aws", "cache": False}

        # Step 2: Quét metrics song song
        def fetch_metrics(b):
            return {
                "bucket": b["bucket"],
                "region": b["region"],
                "metrics": scanner.get_bucket_storage_metrics(b["bucket"], b["region"])
            }

        results = []
        with ThreadPoolExecutor(max_workers=min(10, len(buckets))) as executor:
            futures = [loop.run_in_executor(executor, fetch_metrics, b) for b in buckets]
            for f in asyncio.as_completed(futures):
                results.append(await f)

        summary = {"total_buckets": len(results), "buckets": results}

        cache.set(cache_key, summary, ttl=600)
        return {**summary, "source": "aws", "cache": False}

    except Exception as e:
        logger.exception("Error scanning all S3 buckets")
        raise HTTPException(status_code=500, detail=f"S3 summary error: {str(e)}")
