from fastapi import APIRouter, Depends, HTTPException
from app.services.aws.client import AWSClientProvider
from app.services.aws.ec2 import EC2Scanner
from app.api.middleware.dependency import *
import asyncio
from app.services.cache_client.redis_client import cache
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/ec2/scan-all-regions", tags=["EC2"])
async def scan_all_ec2_instances(
        client_provider: AWSClientProvider = Depends(get_aws_client_provider),
        client_id: str = Depends(get_current_client_id_dependency),
        force_refresh: bool = False
):
    try:
        cache_key = f'ec2:scan-all-regions:{client_id}'
        if not force_refresh:
            cache_data = cache.get(cache_key)
            if cache_data:
                logger.info("Returning cached data")
                return {
                    **cache_data,
                    'source': 'cache',
                    'cached': True
                }

        scanner = EC2Scanner(client_provider)
        loop = asyncio.get_running_loop()
        report = await loop.run_in_executor(
            None, scanner.scan_all_regions
        )

        # Check if it's a permission error response
        if isinstance(report, dict) and report.get('error') == 'permission_denied':
            # Don't cache error responses
            return {
                **report,
                'source': 'aws',
                'cached': False
            }

        cache.set(cache_key, report, ttl=60)
        return {
            **report,
            'source': 'aws',
            'cached': False
        }
    except Exception as e:
        logger.error(f"Internal error details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred processing your request")


@router.get("/ec2/summary", tags=["EC2"])
async def get_instance_summary(
        client_provider: AWSClientProvider = Depends(get_aws_client_provider),
        client_id: str = Depends(get_current_client_id_dependency),
        force_refresh: bool = False
):
    try:
        if not force_refresh:
            cache_data = cache.get(f'ec2:summary:{client_id}')
            if cache_data:
                logger.info("Returning cached data")
                return {
                    **cache_data,
                    'source': 'cache',
                    'cached': True
                }

        scanner = EC2Scanner(client_provider)
        loop = asyncio.get_running_loop()
        summary = await loop.run_in_executor(
            None, scanner.get_instance_summary
        )

        # Check if it's a permission error response
        if isinstance(summary, dict) and summary.get('error') == 'permission_denied':
            return {
                **summary,
                'source': 'aws',
                'cached': False
            }

        cache.set('ec2:summary', summary, ttl=60)
        return {
            **summary,
            'source': 'aws',
            'cached': False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary error: {str(e)}")


@router.get("/ec2/running-instances", tags=["EC2"])
async def get_running_instances(
    client_provider: AWSClientProvider = Depends(get_aws_client_provider),
    client_id: str = Depends(get_current_client_id_dependency),
    force_refresh: bool = False
):

    try:
        cache_key =f'ec2:running-instances:{client_id}'
        if not force_refresh:
            cache_data = cache.get(cache_key)
            if cache_data:
                logger.info("Returning cached data")
                return {
                    **cache_data,
                    'source' : 'cache_client',
                    'cache_client' : True
                }
        scanner = EC2Scanner(client_provider)
        loop = asyncio.get_running_loop()
        report = await loop.run_in_executor(
            None, scanner.get_running_instances
        )
        cache.set(cache_key, report, ttl=60)
        return {
            **report,
            'source' : 'aws',
            'cache_client' : False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/ec2/cost-estimate", tags=["EC2"])
async def get_cost_estimate(
    client_provider: AWSClientProvider = Depends(get_aws_client_provider),
    client_id: str = Depends(get_current_client_id_dependency),
        force_refresh: bool = False
):
    try:
        cache_key =f'ec2:cost-estimate:{client_id}'
        if not force_refresh:
            cache_data = cache.get(cache_key)
            if cache_data:
                logger.info("Returning cached data")
                return {
                    **cache_data,
                    'source' : 'cache_client',
                    'cache_client' : True
                }
        scanner = EC2Scanner(client_provider)
        loop = asyncio.get_running_loop()
        report = await loop.run_in_executor(
            None, scanner.estimate_monthly_cost
        )
        cache.set(cache_key, report, ttl=60)
        return {
            **report,
            'source' : 'aws',
            'cache_client' : False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cost estimate error: {str(e)}")