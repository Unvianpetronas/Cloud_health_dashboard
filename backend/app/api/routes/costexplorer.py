from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.aws.client import AWSClientProvider
from app.services.aws.costexplorer import CostExplorerScanner
from app.api.middleware.dependency import get_aws_client_provider
from app.services.cache.redis_client import cache
import asyncio
import logging
from datetime import datetime, timedelta, UTC

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/costexplorer/total-cost", tags=["Cost Explorer"])
async def get_total_cost(
        start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
        end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
        granularity: str = Query("MONTHLY", description="DAILY | MONTHLY | HOURLY"),
        force_refresh: bool = False,
        client_provider: AWSClientProvider = Depends(get_aws_client_provider)
):
    """
    Lấy tổng chi phí AWS trong khoảng thời gian.
    """
    try:
        cache_key = f"costexplorer:total:{start_date}:{end_date}:{granularity}"
        if not force_refresh:
            if cached := cache.get(cache_key):
                logger.info("Returning cached total cost data")
                return {**cached, "source": "cache", "cache": True}

        scanner = CostExplorerScanner(client_provider)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, scanner.get_total_cost, start_date, end_date, granularity)

        cache.set(cache_key, result, ttl=300)
        return {**result, "source": "aws", "cache": False}
    except Exception as e:
        logger.exception("Error fetching total cost")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costexplorer/by-service", tags=["Cost Explorer"])
async def get_cost_by_service(
        start_date: str = Query(...),
        end_date: str = Query(...),
        granularity: str = "MONTHLY",
        force_refresh: bool = False,
        client_provider: AWSClientProvider = Depends(get_aws_client_provider)
):
    """
    Chi phí AWS theo từng service.
    """
    try:
        cache_key = f"costexplorer:by-service:{start_date}:{end_date}:{granularity}"
        if not force_refresh:
            if cached := cache.get(cache_key):
                logger.info("Returning cached service cost data")
                return {**cached, "source": "cache", "cache": True}

        scanner = CostExplorerScanner(client_provider)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, scanner.get_cost_by_service, start_date, end_date, granularity)

        cache.set(cache_key, result, ttl=300)
        return {**result, "source": "aws", "cache": False}
    except Exception as e:
        logger.exception("Error fetching cost by service")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costexplorer/by-account", tags=["Cost Explorer"])
async def get_cost_by_account(
        start_date: str = Query(...),
        end_date: str = Query(...),
        granularity: str = "MONTHLY",
        force_refresh: bool = False,
        client_provider: AWSClientProvider = Depends(get_aws_client_provider)
):
    """
    Chi phí AWS theo từng account.
    """
    try:
        cache_key = f"costexplorer:by-account:{start_date}:{end_date}:{granularity}"
        if not force_refresh:
            if cached := cache.get(cache_key):
                logger.info("Returning cached account cost data")
                return {**cached, "source": "cache", "cache": True}

        scanner = CostExplorerScanner(client_provider)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, scanner.get_cost_by_account, start_date, end_date, granularity)

        cache.set(cache_key, result, ttl=300)
        return {**result, "source": "aws", "cache": False}
    except Exception as e:
        logger.exception("Error fetching cost by account")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costexplorer/forecast", tags=["Cost Explorer"])
async def get_cost_forecast(
        days_ahead: int = Query(30, description="Number of days to forecast ahead"),
        metric: str = "UNBLENDED_COST",
        force_refresh: bool = False,
        client_provider: AWSClientProvider = Depends(get_aws_client_provider)
):
    """
    Dự báo chi phí trong tương lai.
    """
    try:
        cache_key = f"costexplorer:forecast:{days_ahead}:{metric}"
        if not force_refresh:
            if cached := cache.get(cache_key):
                logger.info("Returning cached cost forecast")
                return {**cached, "source": "cache", "cache": True}

        scanner = CostExplorerScanner(client_provider)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, scanner.get_cost_forecast, days_ahead, metric)

        cache.set(cache_key, result, ttl=300)
        return {**result, "source": "aws", "cache": False}
    except Exception as e:
        logger.exception("Error fetching cost forecast")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costexplorer/rightsizing", tags=["Cost Explorer"])
async def get_rightsizing_recommendations(
        service: str = Query("AmazonEC2", description="Service to get rightsizing recommendations for"),
        force_refresh: bool = False,
        client_provider: AWSClientProvider = Depends(get_aws_client_provider)
):
    """
    Gợi ý rightsizing (ví dụ: EC2) để tiết kiệm chi phí.
    """
    try:
        cache_key = f"costexplorer:rightsizing:{service}"
        if not force_refresh:
            if cached := cache.get(cache_key):
                logger.info("Returning cached rightsizing data")
                return {**cached, "source": "cache", "cache": True}

        scanner = CostExplorerScanner(client_provider)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, scanner.get_rightsizing_recommendations, service)

        cache.set(cache_key, result, ttl=600)
        return {**result, "source": "aws", "cache": False}
    except Exception as e:
        logger.exception("Error fetching rightsizing recommendations")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/costexplorer/summary", tags=["Cost Explorer"])
async def get_cost_summary(
        start_days_ago: int = 30,
        granularity: str = "MONTHLY",
        forecast_days: int = 30,
        force_refresh: bool = False,
        client_provider: AWSClientProvider = Depends(get_aws_client_provider)
):
    """Tổng tất cả các cost: total cost, theo dịch vụ, theo tài khoản, và dự báo."""
    try:
        end_date = datetime.now(UTC).date().isoformat()
        start_date = (datetime.now(UTC) - timedelta(days=start_days_ago)).date().isoformat()

        cache_key = f"costexplorer:summary:{start_date}:{end_date}:{granularity}:{forecast_days}"
        if not force_refresh:
            if cache_data := cache.get(cache_key):
                logger.info("Returning cached cost summary data")
                return {**cache_data, "source": "cache", "cache": True}

        scanner = CostExplorerScanner(client_provider)
        loop = asyncio.get_running_loop()

        total_task = loop.run_in_executor(None, scanner.get_total_cost, start_date, end_date, granularity)
        service_task = loop.run_in_executor(None, scanner.get_cost_by_service, start_date, end_date, granularity)
        account_task = loop.run_in_executor(None, scanner.get_cost_by_account, start_date, end_date, granularity)
        forecast_task = loop.run_in_executor(None, scanner.get_cost_forecast, forecast_days)

        total, by_service, by_account, forecast = await asyncio.gather(
            total_task, service_task, account_task, forecast_task
        )

        summary = {
            "total_cost": total,
            "by_service": by_service,
            "by_account": by_account,
            "forecast": forecast,
            "period": {"start": start_date, "end": end_date},
        }

        cache.set(cache_key, summary, ttl=300)
        return {**summary, "source": "aws", "cache": False}
    except Exception as e:
        logger.exception("Error fetching cost summary")
        raise HTTPException(status_code=500, detail=f"CostExplorer summary error: {str(e)}")