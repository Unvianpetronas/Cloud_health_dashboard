import boto3
import logging
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, Optional

from app.config import settings

logger = logging.getLogger(__name__)


async def verify_aws_credentials(access_key: str, secret_key: str) -> Optional[Dict]:
    if not access_key or not secret_key:
        logger.warning("Verification attempted with missing access or secret key.")
        return None

    try:
        sts_client = boto3.client(
            'sts',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=settings.YOUR_AWS_REGION
        )
        identity = sts_client.get_caller_identity()

        logger.info(f"AWS credentials verified successfully for Account ID: {identity['Account']}")
        return identity

    except ClientError as e:
        # This specific error code indicates the keys are wrong
        if e.response['Error']['Code'] == 'InvalidClientTokenId':
            logger.warning("Verification failed: Invalid AWS credentials provided.")
        else:
            # Log any other client-side API errors
            logger.error(f"An AWS ClientError occurred during verification: {e}")
        return None

    except NoCredentialsError:
        # This would typically happen if the backend environment itself is misconfigured
        logger.error("Boto3 could not find any credentials to use.")
        return None

    except Exception as e:
        # Catch any other unexpected exceptions
        logger.error(f"An unexpected error occurred during credential verification: {e}")
        return None
