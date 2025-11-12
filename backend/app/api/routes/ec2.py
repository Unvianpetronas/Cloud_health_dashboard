from fastapi import APIRouter, Depends, HTTPException
from app.services.aws.client import AWSClientProvider
from app.services.aws.ec2 import EC2Scanner
from app.api.middleware.dependency import get_aws_client_provider
import asyncio
from app.services.cache_client.redis_client import cache
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/ec2/scan-all-regions", tags=["EC2"])
async def scan_all_ec2_instances(
    client_provider: AWSClientProvider = Depends(get_aws_client_provider),
        force_refresh: bool = False
):
    try:
        cache_key ='ec2:scan-all-regions'
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
            None, scanner.scan_all_regions
        )
        cache.set(cache_key, report, ttl=60)
        return {
            **report,
            'source' : 'aws',
            'cache_client' : False
        }
    except Exception as e:
        logger.error(f"Internal error details: {e}", exc_info=True)  # Log details
        raise HTTPException(status_code=500, detail="An error occurred processing your request")

@router.get("/ec2/running-instances", tags=["EC2"])
async def get_running_instances(
    client_provider: AWSClientProvider = Depends(get_aws_client_provider),
    force_refresh: bool = False
):

    try:
        cache_key ='ec2:running-instances'
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
        force_refresh: bool = False
):
    try:
        cache_key ='ec2:cost-estimate'
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

@router.get("/ec2/summary", tags=["EC2"])
async def get_instance_summary(
    client_provider: AWSClientProvider = Depends(get_aws_client_provider),
        force_refresh: bool = False
):
    try:
        if not force_refresh:
            cache_data = cache.get('ec2:summary')
            if cache_data:
                logger.info("Returning cached data")
                return {
                    **cache_data,
                    'source' : 'cache_client',
                    'cache_client' : True
                }
        scanner = EC2Scanner(client_provider)
        loop = asyncio.get_running_loop()
        summary = await loop.run_in_executor(
            None, scanner.get_instance_summary
        )
        cache.set('ec2:summary', summary, ttl=60)
        return {
            **summary,
            'source' : 'aws',
            'cache_client' : False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary error: {str(e)}")