from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.aws.client import AWSClientProvider
from app.services.aws.guardduty import GuardDutyScanner
from app.api.middleware.dependency import get_aws_client_provider
from app.services.cache_client.redis_client import cache
import asyncio
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/guardduty/status", tags=["GuardDuty"])
async def check_guardduty_status(
        client_provider: AWSClientProvider = Depends(get_aws_client_provider),
        force_refresh: bool = False
):
    try:
        cache_key = "guardduty:status"

        if not force_refresh:
            cached = cache.get(cache_key)
            if cached:
                return {**cached, "cached": True}

        scanner = GuardDutyScanner(client_provider)
        loop = asyncio.get_running_loop()
        status = await loop.run_in_executor(
            None, scanner.check_all_regions_status
        )

        cache.set(cache_key, status, ttl=300)  # 5 min
        return {**status, "cached": False}

    except Exception as e:
        logger.error(f"Status check guardduty error: {e}")
        logger.error(f"Internal error details: {e}", exc_info=True)  # Log details
        raise HTTPException(status_code=500, detail="An error occurred processing your request")


@router.get("/guardduty/findings", tags=["GuardDuty"])
async def get_all_findings(
        client_provider: AWSClientProvider = Depends(get_aws_client_provider),
        severity_filter: int = Query(4, ge=0, le=10, description="Minimum severity (0-10)"),
        force_refresh: bool = False
):
    try:
        cache_key = f"guardduty:findings:severity{severity_filter}"

        if not force_refresh:
            cached = cache.get(cache_key)
            if cached:
                return {**cached, "cached": True}

        scanner = GuardDutyScanner(client_provider)
        loop = asyncio.get_running_loop()
        findings = await loop.run_in_executor(
            None, scanner.get_all_findings, severity_filter
        )

        cache.set(cache_key, findings, ttl=180)  # 3 min
        return {**findings, "cached": False}

    except Exception as e:
        logger.error(f"Findings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/guardduty/critical", tags=["GuardDuty"])
async def get_critical_findings(
        client_provider: AWSClientProvider = Depends(get_aws_client_provider),
        force_refresh: bool = False
):
    try:
        cache_key = "guardduty:critical"

        if not force_refresh:
            cached = cache.get(cache_key)
            if cached:
                return {**cached, "cached": True}

        scanner = GuardDutyScanner(client_provider)
        loop = asyncio.get_running_loop()
        findings = await loop.run_in_executor(
            None, scanner.get_critical_findings
        )

        cache.set(cache_key, findings, ttl=120)  # 2 min
        return {**findings, "cached": False}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/guardduty/summary", tags=["GuardDuty"])
async def get_findings_summary(
        client_provider: AWSClientProvider = Depends(get_aws_client_provider),
        force_refresh: bool = False
):
    try:
        cache_key = "guardduty:summary"

        if not force_refresh:
            cached = cache.get(cache_key)
            if cached:
                return {**cached, "cached": True}

        scanner = GuardDutyScanner(client_provider)
        loop = asyncio.get_running_loop()
        summary = await loop.run_in_executor(
            None, scanner.get_findings_summary
        )

        cache.set(cache_key, summary, ttl=300)  # 5 min
        return {**summary, "cached": False}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/guardduty/clear-cache", tags=["GuardDuty"])
async def clear_cache_guardduty():
    try:
        cache.clear_pattern("guardduty:*")
        return {"status": "success", "message": "GuardDuty cache_client cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))