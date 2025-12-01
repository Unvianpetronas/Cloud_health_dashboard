from fastapi import APIRouter, Depends, HTTPException
from app.services.aws.client import AWSClientProvider
from app.api.middleware.dependency import get_aws_client_provider
from app.services.cache_client.redis_client import cache
import logging


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/aws/billing", tags=["Free Tier"])
async def get_billing_status(
        force_refresh: bool = False,
        client_provider: AWSClientProvider = Depends(get_aws_client_provider)
):
    """
    Get Free Tier Usage information from AWS.
    Only returns services currently eligible for Free Tier.
    """
    try:
        cache_key = "aws:billing:freetier"
        if not force_refresh and (cached := cache.get(cache_key)):
            return {**cached, "source": "cache"}

        free_tier_data = []
        is_free_tier_active = False

        try:
            # FreeTier Client (requires region us-east-1)
            ft_client = client_provider.get_client("freetier", region_name="us-east-1")

            # Call API to get Free Tier usage information
            response = ft_client.get_free_tier_usage()

            for offer in response.get('freeTierUsages', []):
                # Only get items with a Limit for calculation
                if 'limit' in offer and offer['limit'] > 0:
                    is_free_tier_active = True
                    usage = offer.get('actualUsageAmount', 0)
                    limit = offer.get('limit', 0)
                    service_name = offer.get('service', 'Unknown')
                    operation = offer.get('operation', '')
                    unit = offer.get('unit', '')

                    # Calculate % and remaining balance
                    percent_used = (usage / limit) * 100
                    remaining = max(0, limit - usage)

                    # Find information about the duration (usually in the description)
                    description = offer.get('description', '')

                    free_tier_data.append({
                        "service": service_name,
                        "type": offer.get('freeTierType', 'Unknown'),  # Ex: 12 Months Free, Always Free
                        "description": description,
                        "usage": round(usage, 2),
                        "limit": round(limit, 2),
                        "remaining": round(remaining, 2),
                        "unit": unit,
                        "percent_used": round(percent_used, 1)
                    })

        except Exception as e:
            logger.warning(f"Unable to get Free Tier info (Check IAM Permission 'freetier:GetFreeTierUsage'): {e}")
            # If error (due to no permissions or not free tier), list will be empty

        # If no Free Tier data, return is_active = False to hide in frontend
        if not free_tier_data:
            is_free_tier_active = False

        data = {
            "is_active": is_free_tier_active,
            "offers": free_tier_data
        }

        cache.set(cache_key, data, ttl=3600)
        return {**data, "source": "aws"}

    except Exception as e:
        logger.exception("Error getting billing info")
        raise HTTPException(status_code=500, detail=str(e))