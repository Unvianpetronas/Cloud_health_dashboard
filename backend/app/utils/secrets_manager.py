import boto3
import json
from botocore.exceptions import ClientError
from datetime import datetime
from zoneinfo import ZoneInfo
import logging
import asyncio
from functools import partial

logger = logging.getLogger(__name__)
UTC = ZoneInfo("UTC")


class SecretsManager:
    """
    AWS Secrets Manager wrapper for secure credential storage

    Usage:
        sm = SecretsManager()
        sm.store_credentials('client-123', 'AKIAIOSFODNN7EXAMPLE', 'wJalrXUtn...')
        creds = sm.get_credentials('client-123')
    """

    def __init__(self, region_name='ap-southeast-1'):
        """
        Initialize Secrets Manager client

        Args:
            region_name: AWS region (default: ap-southeast-1 for Vietnam)
        """
        self.client = boto3.client('secretsmanager', region_name=region_name)
        self.region = region_name

        # KMS key alias for encryption (you'll create this in AWS)
        self.kms_key_id = 'alias/cloud-health-kms'

    async def store_credentials_async(self, client_id: str, access_key: str,
                                      secret_key: str, aws_region: str = 'us-east-1') -> bool:
        """
        Async wrapper for store_credentials - runs in thread pool to avoid blocking event loop.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            partial(self.store_credentials, client_id, access_key, secret_key, aws_region)
        )

    def store_credentials(self, client_id: str, access_key: str,
                          secret_key: str, aws_region: str = 'us-east-1') -> bool:
        """
        Store AWS credentials in Secrets Manager with KMS encryption

        Args:
            client_id: Unique client identifier (e.g., 'client-123')
            access_key: AWS access key ID
            secret_key: AWS secret access key
            aws_region: Client's AWS region

        Returns:
            bool: True if successful, False otherwise

        Example:
            success = sm.store_credentials(
                'client-123',
                'AKIAIOSFODNN7EXAMPLE',
                'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
            )
        """
        secret_name = f'cloud-health/{client_id}/credentials'

        try:
            # Prepare secret value as JSON
            secret_value = json.dumps({
                'access_key': access_key,
                'secret_key': secret_key,
                'aws_region': aws_region,
                'created_at': datetime.now(UTC).isoformat(),
                'client_id': client_id
            })

            # Create secret with KMS encryption
            response = self.client.create_secret(
                Name=secret_name,
                Description=f'AWS credentials for client {client_id}',
                SecretString=secret_value,
                KmsKeyId=self.kms_key_id,
                Tags=[
                    {'Key': 'Client', 'Value': client_id},
                    {'Key': 'Environment', 'Value': 'production'},
                    {'Key': 'Application', 'Value': 'cloud-health-dashboard'},
                    {'Key': 'ManagedBy', 'Value': 'api'}
                ]
            )

            logger.info(f"Credentials stored for client {client_id} (ARN: {response['ARN']})")
            return True

        except ClientError as e:
            error_code = e.response['Error']['Code']

            if error_code == 'ResourceExistsException':
                # Secret already exists, update it instead
                logger.warning(f"Secret already exists for {client_id}, updating...")
                return self.update_credentials(client_id, access_key, secret_key, aws_region)
            else:
                logger.error(f"Error storing credentials for {client_id}: {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error storing credentials: {e}")
            return False

    async def get_credentials_async(self, client_id: str) -> dict:
        """
        Async wrapper for get_credentials - runs in thread pool to avoid blocking event loop.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            partial(self.get_credentials, client_id)
        )

    def get_credentials(self, client_id: str) -> dict:
        """
        Retrieve AWS credentials from Secrets Manager

        Args:
            client_id: Unique client identifier

        Returns:
            dict: {'access_key': '...', 'secret_key': '...', 'aws_region': '...'}
            None if not found or error

        Example:
            creds = sm.get_credentials('client-123')
            if creds:
                access_key = creds['access_key']
        """
        secret_name = f'cloud-health/{client_id}/credentials'

        try:
            # Get secret value
            response = self.client.get_secret_value(SecretId=secret_name)
            secret_data = json.loads(response['SecretString'])

            logger.debug(f"Retrieved credentials for client {client_id}")

            return {
                'access_key': secret_data['access_key'],
                'secret_key': secret_data['secret_key'],
                'aws_region': secret_data.get('aws_region', 'us-east-1')
            }

        except ClientError as e:
            error_code = e.response['Error']['Code']

            if error_code == 'ResourceNotFoundException':
                logger.error(f"Secret not found for client {client_id}")
            elif error_code == 'InvalidRequestException':
                logger.error(f"Invalid request for client {client_id}")
            elif error_code == 'InvalidParameterException':
                logger.error(f"Invalid parameter for client {client_id}")
            elif error_code == 'DecryptionFailure':
                logger.error(f"KMS decryption failed for client {client_id}")
            elif error_code == 'AccessDeniedException':
                logger.error(f"Access denied to secret for client {client_id}")
            else:
                logger.error(f"Error retrieving credentials: {e}")

            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in secret for {client_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving credentials: {e}")
            return None

    async def update_credentials_async(self, client_id: str, access_key: str,
                                       secret_key: str, aws_region: str = 'us-east-1') -> bool:
        """
        Async wrapper for update_credentials - runs in thread pool to avoid blocking event loop.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            partial(self.update_credentials, client_id, access_key, secret_key, aws_region)
        )

    def update_credentials(self, client_id: str, access_key: str,
                           secret_key: str, aws_region: str = 'us-east-1') -> bool:
        """
        Update existing credentials

        Args:
            client_id: Unique client identifier
            access_key: New AWS access key
            secret_key: New AWS secret key
            aws_region: Client's AWS region

        Returns:
            bool: True if successful, False otherwise
        """
        secret_name = f'cloud-health/{client_id}/credentials'

        try:
            secret_value = json.dumps({
                'access_key': access_key,
                'secret_key': secret_key,
                'aws_region': aws_region,
                'updated_at': datetime.now(UTC).isoformat(),
                'client_id': client_id
            })

            self.client.update_secret(
                SecretId=secret_name,
                SecretString=secret_value,
                KmsKeyId=self.kms_key_id
            )

            logger.info(f"Credentials updated for client {client_id}")
            return True

        except ClientError as e:
            logger.error(f"Error updating credentials for {client_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating credentials: {e}")
            return False

    async def delete_credentials_async(self, client_id: str,
                                       force_delete: bool = False) -> bool:
        """
        Async wrapper for delete_credentials - runs in thread pool to avoid blocking event loop.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            partial(self.delete_credentials, client_id, force_delete)
        )

    def delete_credentials(self, client_id: str,
                           force_delete: bool = False) -> bool:
        """
        Delete credentials with optional recovery window

        Args:
            client_id: Unique client identifier
            force_delete: If True, delete immediately without 30-day recovery

        Returns:
            bool: True if successful, False otherwise

        Note:
            By default, secrets are scheduled for deletion with 30-day recovery.
            Use force_delete=True only when absolutely necessary.
        """
        secret_name = f'cloud-health/{client_id}/credentials'

        try:
            if force_delete:
                # Immediate deletion (NOT RECOMMENDED)
                self.client.delete_secret(
                    SecretId=secret_name,
                    ForceDeleteWithoutRecovery=True
                )
                logger.warning(f"Credentials FORCE-DELETED for {client_id} (no recovery!)")
            else:
                # Scheduled deletion with 30-day recovery window (RECOMMENDED)
                self.client.delete_secret(
                    SecretId=secret_name,
                    RecoveryWindowInDays=30
                )
                logger.info(f"Credentials scheduled for deletion (30-day recovery) for {client_id}")

            return True

        except ClientError as e:
            error_code = e.response['Error']['Code']

            if error_code == 'ResourceNotFoundException':
                logger.warning(f"Secret not found for {client_id}, may already be deleted")
                return True  # Consider it successful if already gone
            else:
                logger.error(f"Error deleting credentials for {client_id}: {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error deleting credentials: {e}")
            return False

    def restore_credentials(self, client_id: str) -> bool:
        """
        Restore a secret that was scheduled for deletion

        Args:
            client_id: Unique client identifier

        Returns:
            bool: True if successful, False otherwise

        Note:
            Only works if secret is in recovery window (30 days after deletion)
        """
        secret_name = f'cloud-health/{client_id}/credentials'

        try:
            self.client.restore_secret(SecretId=secret_name)
            logger.info(f"Credentials restored for client {client_id}")
            return True

        except ClientError as e:
            logger.error(f"Error restoring credentials for {client_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error restoring credentials: {e}")
            return False

    def list_secrets(self, max_results: int = 100) -> list:
        """
        List all secrets for monitoring/audit purposes

        Args:
            max_results: Maximum number of secrets to return

        Returns:
            list: List of secret metadata dicts

        Example:
            secrets = sm.list_secrets()
            for secret in secrets:
                print(f"Name: {secret['Name']}, Created: {secret['CreatedDate']}")
        """
        try:
            response = self.client.list_secrets(
                MaxResults=max_results,
                Filters=[
                    {
                        'Key': 'name',
                        'Values': ['cloud-health/']
                    }
                ]
            )

            secrets = response.get('SecretList', [])
            logger.info(f"Found {len(secrets)} secrets")

            return secrets

        except ClientError as e:
            logger.error(f"Error listing secrets: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing secrets: {e}")
            return []

    def rotate_secret(self, client_id: str, rotation_lambda_arn: str) -> bool:
        """
        Enable automatic rotation for a secret

        Args:
            client_id: Unique client identifier
            rotation_lambda_arn: ARN of Lambda function for rotation

        Returns:
            bool: True if successful, False otherwise

        Note:
            Requires Lambda function to handle rotation logic
        """
        secret_name = f'cloud-health/{client_id}/credentials'

        try:
            self.client.rotate_secret(
                SecretId=secret_name,
                RotationLambdaARN=rotation_lambda_arn,
                RotationRules={
                    'AutomaticallyAfterDays': 90  # Rotate every 90 days
                }
            )

            logger.info(f"Automatic rotation enabled for {client_id}")
            return True

        except ClientError as e:
            logger.error(f"Error enabling rotation for {client_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error enabling rotation: {e}")
            return False


# Singleton instance for reuse
_secrets_manager_instance = None


def get_secrets_manager() -> SecretsManager:
    """
    Get singleton instance of SecretsManager

    Returns:
        SecretsManager: Singleton instance

    Usage:
        sm = get_secrets_manager()
        creds = sm.get_credentials('client-123')
    """
    global _secrets_manager_instance

    if _secrets_manager_instance is None:
        _secrets_manager_instance = SecretsManager()

    return _secrets_manager_instance