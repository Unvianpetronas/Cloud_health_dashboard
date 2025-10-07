# backend/app/api/routes/ec2.py - COMPLETE VERSION
from fastapi import APIRouter, Depends, HTTPException
from app.services.aws.client import AWSClientProvider
from app.services.aws.ec2 import EC2Scanner
from app.api.middleware.dependency import get_aws_client_provider
import asyncio

router = APIRouter()

@router.get("/ec2/scan-all-regions", tags=["EC2"])
async def scan_all_ec2_instances(
    client_provider: AWSClientProvider = Depends(get_aws_client_provider)
):
    try:
        scanner = EC2Scanner(client_provider)
        loop = asyncio.get_running_loop()
        report = await loop.run_in_executor(
            None, scanner.scan_all_regions
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan error: {str(e)}")

@router.get("/ec2/running-instances", tags=["EC2"])
async def get_running_instances(
    client_provider: AWSClientProvider = Depends(get_aws_client_provider)
):

    try:
        scanner = EC2Scanner(client_provider)
        loop = asyncio.get_running_loop()
        report = await loop.run_in_executor(
            None, scanner.get_running_instances
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/ec2/cost-estimate", tags=["EC2"])
async def get_cost_estimate(
    client_provider: AWSClientProvider = Depends(get_aws_client_provider)
):
    try:
        scanner = EC2Scanner(client_provider)
        loop = asyncio.get_running_loop()
        report = await loop.run_in_executor(
            None, scanner.estimate_monthly_cost
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cost estimate error: {str(e)}")

@router.get("/ec2/summary", tags=["EC2"])
async def get_instance_summary(
    client_provider: AWSClientProvider = Depends(get_aws_client_provider)
):
    try:
        scanner = EC2Scanner(client_provider)
        loop = asyncio.get_running_loop()
        summary = await loop.run_in_executor(
            None, scanner.get_instance_summary
        )
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary error: {str(e)}")