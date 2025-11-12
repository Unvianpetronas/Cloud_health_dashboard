from fastapi import APIRouter, Depends, HTTPException
from app.services.aws.client import AWSClientProvider
from app.services.aws.securityhub import SecurityHubScanner
from app.api.middleware.dependency import get_aws_client_provider
from app.services.cache_client.redis_client import cache
import asyncio
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/securityhub/findings", tags=["SecurityHub"])
async def get_securityhub_findings(
        force_refresh: bool = False,
        client_provider: AWSClientProvider = Depends(get_aws_client_provider)
):
    """
    Quét tất cả findings từ AWS Security Hub trên toàn bộ regions có sẵn.
    Nếu dữ liệu đã được cache, sẽ trả về cache trừ khi `force_refresh=True`.
    """
    try:
        cache_key = "securityhub:findings:all"

        if not force_refresh:
            if cached := cache.get(cache_key):
                logger.info("Returning cached SecurityHub findings")
                return {**cached, "source": "cache", "cache": True}

        scanner = SecurityHubScanner(client_provider)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, scanner.scan_all_regions)

        cache.set(cache_key, result, ttl=900)  # cache 15 phút
        return {**result, "source": "aws", "cache": False}

    except Exception as e:
        logger.exception("Error scanning SecurityHub findings")
        raise HTTPException(status_code=500, detail=f"SecurityHub findings error: {str(e)}")
