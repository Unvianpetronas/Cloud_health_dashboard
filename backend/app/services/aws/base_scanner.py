from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
from botocore.exceptions import ClientError, BotoCoreError
import logging

logger = logging.getLogger(__name__)


class BaseAWSScanner:
    """
    Base class for all AWS scanners with built-in retry logic

    All scanners should inherit from this class to get automatic
    retry handling for AWS API throttling and transient errors.
    """

    @staticmethod
    def with_retry():
        """
        Decorator that adds retry logic to AWS API calls

        Retries on:
        - Throttling errors
        - Rate limit exceeded
        - Connection errors

        Retry strategy:
        - Up to 3 attempts
        - Exponential backoff: 2s, 4s, 8s
        - Logs before each retry
        """
        return retry(
            # What errors to retry on
            retry=retry_if_exception_type((
                ClientError,  # AWS service errors (throttling, etc)
                BotoCoreError,  # boto3 connection errors
                ConnectionError,  # Network errors
            )),

            # How many times to retry
            stop=stop_after_attempt(3),

            # How long to wait between retries (exponential backoff)
            wait=wait_exponential(multiplier=2, min=2, max=10),

            # Log before sleeping
            before_sleep=before_sleep_log(logger, logging.WARNING),

            # Reraise the last exception if all retries fail
            reraise=True
        )

    @staticmethod
    def should_retry_error(error: Exception) -> bool:
        """
        Check if an error should trigger a retry

        Args:
            error: The exception that was raised

        Returns:
            True if the error is retryable, False otherwise
        """
        if isinstance(error, ClientError):
            error_code = error.response.get('Error', {}).get('Code', '')

            # List of retryable AWS error codes
            retryable_errors = [
                'Throttling',
                'ThrottlingException',
                'RequestLimitExceeded',
                'TooManyRequestsException',
                'ProvisionedThroughputExceededException',
                'RequestThrottled',
                'ServiceUnavailable',
                'InternalError',
            ]

            return error_code in retryable_errors

        # Retry on connection errors
        return isinstance(error, (BotoCoreError, ConnectionError))