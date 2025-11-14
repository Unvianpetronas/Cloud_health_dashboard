from datetime import datetime, timedelta
from typing import Dict, Optional, List, Union
from boto3.dynamodb.conditions import Key, Attr
import uuid
import logging
from app.database.dynamodb import DynamoDBConnection
from app.config import settings
from decimal import Decimal
from app.utils.client_encryption import ClientEncryption
from app.utils.secrets_manager import get_secrets_manager
from app.services.cache_client.redis_client import cache
logger = logging.getLogger(__name__)


class BaseModel:
    def __init__(self):
        self.db = DynamoDBConnection()


class ClientModel(BaseModel):

    def __init__(self):
        super().__init__()
        self.table = self.db.get_table(settings.CLIENTS_TABLE)
        self.use_secrets_manager = getattr(settings, 'USE_SECRETS_MANAGER', False)
        if self.use_secrets_manager:
            self.secrets_manager = get_secrets_manager()
            logger.info("Secrets Manager enabled (hybrid mode)")

        self.encryption = ClientEncryption()
        self.cache = cache

    async def create_client(self,
                            email: str,
                            company_name: str,
                            aws_account_id: str,
                            aws_access_key: str,
                            aws_secret_key: str,
                            aws_region: str = "us-east-1") -> Optional[str]:
        """
        Create new client with HYBRID storage:
        - Always store encrypted in DynamoDB (backward compatible)
        - ALSO store in Secrets Manager if enabled (better security)
        """
        try:
            existing_by_account = await self.get_client_by_aws_account_id(aws_account_id)
            if existing_by_account:
                logger.warning(f"Client with AWS Account ID {aws_account_id} already exists")
                return None

            encrypted_access = self.encryption.encrypt_credential(aws_access_key)
            encrypted_secret = self.encryption.encrypt_credential(aws_secret_key)
            if self.use_secrets_manager:
                try:
                    success = self.secrets_manager.store_credentials(
                        client_id=aws_account_id,
                        access_key=aws_access_key,
                        secret_key=aws_secret_key,
                        aws_region=aws_region
                    )

                    if success:
                        logger.info(f"Credentials stored in Secrets Manager for {aws_account_id}")
                    else:
                        logger.warning(f"Failed to store in Secrets Manager, using DynamoDB only")
                except Exception as e:
                    logger.error(f"Secrets Manager error: {e}, using DynamoDB only")

            item = {
                'pk': f"CLIENT#{aws_account_id}",
                'sk': 'METADATA',
                'aws_account_id': aws_account_id,
                'email': email,
                'company_name': company_name,
                'aws_access_key_encrypted': encrypted_access,
                'aws_secret_key_encrypted': encrypted_secret,
                'aws_region': aws_region,
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'last_collection': None,
                'email_verified': False,
                'email_verification_token': '',
                'email_verification_expires': '',
                'notification_preferences': {
                    'critical_alerts': True,
                    'daily_summary': False
                },
                'use_secrets_manager': self.use_secrets_manager
            }

            self.table.put_item(Item=item)
            logger.info(f"Created client {aws_account_id} for {email}")
            return aws_account_id

        except Exception as e:
            logger.error(f"Error creating client: {e}", exc_info=True)
            return None

    async def get_client(self, aws_account_id: str) -> Optional[Dict]:
        """
        Get client with HYBRID credential retrieval:
        1. Check Redis cache_client first (fastest)
        2. Try Secrets Manager (if enabled)
        3. Fallback to DynamoDB (always works)
        """
        try:
            cache_key = f"client:{aws_account_id}"
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for client {aws_account_id}")
                return cached

            # Query DynamoDB
            response = self.table.get_item(
                Key={
                    'pk': f"CLIENT#{aws_account_id}",
                    'sk': 'METADATA'
                }
            )

            client = response.get('Item')
            if not client:
                logger.warning(f"Client {aws_account_id} not found")
                return None

            credentials_from_sm = False
            if self.use_secrets_manager or client.get('use_secrets_manager'):
                try:
                    creds = self.secrets_manager.get_credentials(aws_account_id)
                    if creds:
                        client['aws_access_key'] = creds['access_key']
                        client['aws_secret_key'] = creds['secret_key']
                        credentials_from_sm = True
                        logger.debug(f"Got credentials from Secrets Manager")
                except Exception as e:
                    logger.warning(f"Secrets Manager failed: {e}, using DynamoDB")

            if not credentials_from_sm:
                client['aws_access_key'] = self.encryption.decrypt_credential(
                    client['aws_access_key_encrypted']
                )
                client['aws_secret_key'] = self.encryption.decrypt_credential(
                    client['aws_secret_key_encrypted']
                )
                logger.debug(f"Got credentials from DynamoDB (Fernet)")

            del client['aws_access_key_encrypted']
            del client['aws_secret_key_encrypted']

            self.cache.set(cache_key, client, ttl=300)

            return client

        except Exception as e:
            logger.error(f"Error getting client {aws_account_id}: {e}", exc_info=True)
            return None

    async def get_client_by_aws_account_id(self, aws_account_id: str) -> Optional[Dict]:
        """Same HYBRID approach as get_client"""
        try:
            response = self.table.query(
                IndexName='AwsAccountIdIndex',
                KeyConditionExpression=Key('aws_account_id').eq(aws_account_id)
            )

            items = response.get('Items', [])
            if not items:
                return None

            client = items[0]

            credentials_from_sm = False

            if self.use_secrets_manager or client.get('use_secrets_manager'):
                try:
                    creds = self.secrets_manager.get_credentials(aws_account_id)
                    if creds:
                        client['aws_access_key'] = creds['access_key']
                        client['aws_secret_key'] = creds['secret_key']
                        credentials_from_sm = True
                except Exception as e:
                    logger.warning(f"Secrets Manager failed: {e}")

            if not credentials_from_sm:
                # Fallback to DynamoDB
                client['aws_access_key'] = self.encryption.decrypt_credential(
                    client['aws_access_key_encrypted']
                )
                client['aws_secret_key'] = self.encryption.decrypt_credential(
                    client['aws_secret_key_encrypted']
                )

            del client['aws_access_key_encrypted']
            del client['aws_secret_key_encrypted']

            return client

        except Exception as e:
            logger.error(f"Error getting client by AWS Account ID {aws_account_id}: {e}")
            return None

    async def get_client_by_email(self, email: str) -> Optional[Dict]:
        """Same HYBRID approach"""
        try:
            response = self.table.query(
                IndexName='EmailIndex',
                KeyConditionExpression=Key('email').eq(email.lower())
            )

            items = response.get('Items', [])
            if not items:
                return None

            client = items[0]
            aws_account_id = client['aws_account_id']
            credentials_from_sm = False

            if self.use_secrets_manager or client.get('use_secrets_manager'):
                try:
                    creds = self.secrets_manager.get_credentials(aws_account_id)
                    if creds:
                        client['aws_access_key'] = creds['access_key']
                        client['aws_secret_key'] = creds['secret_key']
                        credentials_from_sm = True
                except Exception as e:
                    logger.warning(f"Secrets Manager failed: {e}")

            if not credentials_from_sm:
                client['aws_access_key'] = self.encryption.decrypt_credential(
                    client['aws_access_key_encrypted']
                )
                client['aws_secret_key'] = self.encryption.decrypt_credential(
                    client['aws_secret_key_encrypted']
                )

            del client['aws_access_key_encrypted']
            del client['aws_secret_key_encrypted']

            return client

        except Exception as e:
            logger.error(f"Error getting client by email: {e}")
            return None

    async def get_all_active_clients(self) -> List[Dict]:
        """Get all active clients with HYBRID approach"""
        try:
            response = self.table.scan(
                FilterExpression=Attr('status').eq('active') &
                                 Attr('sk').eq('METADATA')
            )

            clients = []
            for item in response.get('Items', []):
                try:
                    aws_account_id = item['aws_account_id']
                    credentials_from_sm = False

                    if self.use_secrets_manager or item.get('use_secrets_manager'):
                        try:
                            creds = self.secrets_manager.get_credentials(aws_account_id)
                            if creds:
                                item['aws_access_key'] = creds['access_key']
                                item['aws_secret_key'] = creds['secret_key']
                                credentials_from_sm = True
                        except Exception as e:
                            logger.warning(f"Secrets Manager failed for {aws_account_id}: {e}")

                    if not credentials_from_sm:
                        item['aws_access_key'] = self.encryption.decrypt_credential(
                            item['aws_access_key_encrypted']
                        )
                        item['aws_secret_key'] = self.encryption.decrypt_credential(
                            item['aws_secret_key_encrypted']
                        )

                    del item['aws_access_key_encrypted']
                    del item['aws_secret_key_encrypted']

                    clients.append(item)
                except Exception as e:
                    logger.error(f"Error decrypting client {item.get('aws_account_id')}: {e}")
                    continue

            return clients

        except Exception as e:
            logger.error(f"Error getting active clients: {e}")
            return []

    async def update_credentials(self,
                                 aws_account_id: str,
                                 aws_access_key: str,
                                 aws_secret_key: str,
                                 aws_region: str = "us-east-1") -> bool:
        """
        Update credentials in BOTH places:
        - DynamoDB (always)
        - Secrets Manager (if enabled)
        """
        try:
            encrypted_access = self.encryption.encrypt_credential(aws_access_key)
            encrypted_secret = self.encryption.encrypt_credential(aws_secret_key)

            self.table.update_item(
                Key={'pk': f"CLIENT#{aws_account_id}", 'sk': 'METADATA'},
                UpdateExpression='SET aws_access_key_encrypted = :access, aws_secret_key_encrypted = :secret, aws_region = :region, updated_at = :updated',
                ExpressionAttributeValues={
                    ':access': encrypted_access,
                    ':secret': encrypted_secret,
                    ':region': aws_region,
                    ':updated': datetime.now().isoformat()
                }
            )
            if self.use_secrets_manager:
                try:
                    success = self.secrets_manager.update_credentials(
                        client_id=aws_account_id,
                        access_key=aws_access_key,
                        secret_key=aws_secret_key,
                        aws_region=aws_region
                    )

                    if success:
                        logger.info(f"Credentials updated in Secrets Manager")
                    else:
                        logger.warning(f"Failed to update Secrets Manager")
                except Exception as e:
                    logger.error(f"Secrets Manager update error: {e}")

            self.cache.delete(f"client:{aws_account_id}")
            self.cache.delete(f"credentials:{aws_account_id}")

            logger.info(f"Updated credentials for {aws_account_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating credentials: {e}")
            return False


    async def update_client_status(self, aws_account_id: str, status: str) -> bool:
        try:
            valid_statuses = ['active', 'suspended', 'deleted']
            if status not in valid_statuses:
                raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")

            self.table.update_item(
                Key={'pk': f"CLIENT#{aws_account_id}", 'sk': 'METADATA'},
                UpdateExpression='SET #status = :status, updated_at = :updated',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': status,
                    ':updated': datetime.now().isoformat()
                }
            )

            logger.info(f"Updated client {aws_account_id} status to {status}")
            return True

        except Exception as e:
            logger.error(f"Error updating client status: {e}")
            return False

    async def update_last_collection(self, aws_account_id: str) -> bool:
        try:
            self.table.update_item(
                Key={'pk': f"CLIENT#{aws_account_id}", 'sk': 'METADATA'},
                UpdateExpression='SET last_collection = :timestamp, updated_at = :updated',
                ExpressionAttributeValues={
                    ':timestamp': datetime.now().isoformat(),
                    ':updated': datetime.now().isoformat()
                }
            )
            return True

        except Exception as e:
            logger.error(f"Error updating last collection time: {e}")
            return False

    async def update_notification_preferences(self,
                                              aws_account_id: str,
                                              preferences: Dict) -> bool:
        try:
            self.table.update_item(
                Key={'pk': f"CLIENT#{aws_account_id}", 'sk': 'METADATA'},
                UpdateExpression='SET notification_preferences = :prefs, updated_at = :updated',
                ExpressionAttributeValues={
                    ':prefs': preferences,
                    ':updated': datetime.now().isoformat()
                }
            )

            # Invalidate cache_client
            self.cache.delete(f"client:{aws_account_id}")

            logger.info(f"Updated notification preferences for {aws_account_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating notification preferences: {e}")
            return False

    async def update_settings(self, aws_account_id: str, settings: Dict) -> bool:
        """
        Update user settings (notifications, dashboard, security)

        Args:
            aws_account_id: AWS account ID
            settings: Dictionary containing settings {notifications, dashboard, security}

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.table.update_item(
                Key={'pk': f"CLIENT#{aws_account_id}", 'sk': 'METADATA'},
                UpdateExpression='SET settings = :settings, updated_at = :updated',
                ExpressionAttributeValues={
                    ':settings': settings,
                    ':updated': datetime.now().isoformat()
                }
            )

            # Invalidate cache
            self.cache.delete(f"client:{aws_account_id}")

            logger.info(f"Updated settings for {aws_account_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating settings: {e}", exc_info=True)
            return False

    async def delete_client(self, aws_account_id: str) -> bool:
        """
        Delete client from BOTH places:
        - DynamoDB
        - Secrets Manager (if enabled)
        """
        try:
            if self.use_secrets_manager:
                try:
                    self.secrets_manager.delete_credentials(
                        aws_account_id,
                        force_delete=False  # 30-day recovery window
                    )
                    logger.info(f"Credentials deleted from Secrets Manager (30-day recovery)")
                except Exception as e:
                    logger.error(f"Secrets Manager delete error: {e}")

            self.cache.delete(f"client:{aws_account_id}")
            self.cache.delete_pattern(f"client:{aws_account_id}:*")
            self.table.delete_item(
                Key={
                    'pk': f"CLIENT#{aws_account_id}",
                    'sk': 'METADATA'
                }
            )

            logger.info(f"Client {aws_account_id} deleted successfully")
            return True

        except Exception as e:
            logger.error(f"Error deleting client: {e}")
            return False

    async def set_email_verification_token(self,
                                           aws_account_id: str,
                                           token: str,
                                           expires_at: datetime) -> bool:
        """Set email verification token"""
        try:
            self.table.update_item(
                Key={'pk': f"CLIENT#{aws_account_id}", 'sk': 'METADATA'},
                UpdateExpression='SET email_verification_token = :token, email_verification_expires = :expires, updated_at = :updated',
                ExpressionAttributeValues={
                    ':token': token,
                    ':expires': expires_at.isoformat(),
                    ':updated': datetime.now().isoformat()
                }
            )

            # Invalidate cache_client
            self.cache.delete(f"client:{aws_account_id}")

            logger.info(f"Set verification token for {aws_account_id}")
            return True

        except Exception as e:
            logger.error(f"Error setting verification token: {e}")
            return False

    async def verify_email(self, aws_account_id: str) -> bool:
        """Mark email as verified"""
        try:
            self.table.update_item(
                Key={'pk': f"CLIENT#{aws_account_id}", 'sk': 'METADATA'},
                UpdateExpression='SET email_verified = :verified, email_verification_token = :empty, updated_at = :updated',
                ExpressionAttributeValues={
                    ':verified': True,
                    ':empty': '',
                    ':updated': datetime.now().isoformat()
                }
            )

            # Invalidate cache_client
            self.cache.delete(f"client:{aws_account_id}")

            logger.info(f"Email verified for {aws_account_id}")
            return True

        except Exception as e:
            logger.error(f"Error verifying email: {e}")
            return False

    async def get_client_by_verification_token(self, token: str) -> Optional[Dict]:
        """Get client by email verification token"""
        try:
            # Scan for token (not indexed, but verification is rare)
            response = self.table.scan(
                FilterExpression=Attr('email_verification_token').eq(token) &
                                 Attr('sk').eq('METADATA')
            )

            items = response.get('Items', [])
            if not items:
                return None

            client = items[0]

            # Check if token expired
            expires_at = datetime.fromisoformat(client.get('email_verification_expires', ''))
            if datetime.now() > expires_at:
                logger.warning(f"Verification token expired for {client.get('aws_account_id')}")
                return None

            return client

        except Exception as e:
            logger.error(f"Error getting client by token: {e}")
            return None


    async def get_client_count(self) -> int:
        """Get total number of clients"""
        try:
            response = self.table.scan(
                FilterExpression=Attr('sk').eq('METADATA'),
                Select='COUNT'
            )
            return response.get('Count', 0)

        except Exception as e:
            logger.error(f"Error getting client count: {e}")
            return 0

    async def get_active_client_count(self) -> int:
        """Get number of active clients"""
        try:
            response = self.table.scan(
                FilterExpression=Attr('status').eq('active') & Attr('sk').eq('METADATA'),
                Select='COUNT'
            )
            return response.get('Count', 0)

        except Exception as e:
            logger.error(f"Error getting active client count: {e}")
            return 0

    async def get_clients_by_status(self, status: str) -> List[Dict]:
        """Get all clients by status"""
        try:
            response = self.table.scan(
                FilterExpression=Attr('status').eq(status) & Attr('sk').eq('METADATA')
            )

            # Return without credentials
            clients = []
            for item in response.get('Items', []):
                # Remove sensitive data
                item.pop('aws_access_key_encrypted', None)
                item.pop('aws_secret_key_encrypted', None)
                clients.append(item)

            return clients

        except Exception as e:
            logger.error(f"Error getting clients by status: {e}")
            return []

    async def client_exists(self, aws_account_id: str) -> bool:
        """Check if client exists"""
        try:
            response = self.table.get_item(
                Key={
                    'pk': f"CLIENT#{aws_account_id}",
                    'sk': 'METADATA'
                }
            )
            return 'Item' in response

        except Exception as e:
            logger.error(f"Error checking client existence: {e}")
            return False

    async def get_client_credentials(self, aws_account_id: str) -> Optional[Dict[str, str]]:
        """
        Get ONLY credentials (for worker use)
        Returns: {'aws_access_key': '...', 'aws_secret_key': '...', 'aws_region': '...'}
        """
        try:
            # Check cache_client first
            cache_key = f"credentials:{aws_account_id}"
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Credentials cache_client hit for {aws_account_id}")
                return cached

            # Get full client
            client = await self.get_client(aws_account_id)

            if not client:
                return None

            credentials = {
                'aws_access_key': client['aws_access_key'],
                'aws_secret_key': client['aws_secret_key'],
                'aws_region': client.get('aws_region', 'us-east-1')
            }

            # Cache credentials for 5 minutes
            self.cache.set(cache_key, credentials, ttl=300)

            return credentials

        except Exception as e:
            logger.error(f"Error getting credentials for {aws_account_id}: {e}")
            return None


class MetricsModel(BaseModel):

    def __init__(self):
        super().__init__()
        self.table = self.db.get_table(settings.METRICS_TABLE)
        self.cache = cache

    async def store_metric(self,
                           aws_account_id: str,
                           service: str,
                           metric_name: str,
                           timestamp: datetime,
                           value: Union[float, Decimal],
                           unit: Optional[str] = None,
                           dimensions: Optional[Dict] = None) -> bool:

        try:
            item = {
                'pk': f"CLIENT#{aws_account_id}#{service}#{metric_name}",
                'sk': timestamp.isoformat(),
                'aws_account_id': aws_account_id,
                'service': service,
                'metric_name': metric_name,
                'value': Decimal(str(value)),
                'timestamp': timestamp.isoformat(),
                'ttl': int((datetime.now() + timedelta(days=settings.METRICS_TTL_DAYS)).timestamp())
            }

            if unit:
                item['unit'] = unit
            if dimensions:
                item['dimensions'] = dimensions

            self.table.put_item(Item=item)

            cache_pattern = f"metrics:{aws_account_id}:{service}:{metric_name}:*"
            self.cache.clear_pattern(cache_pattern)

            logger.debug(f"[{aws_account_id}] Stored metric: {service}/{metric_name} = {value}")
            return True

        except Exception as e:
            logger.error(f"[{aws_account_id}] Error storing metric: {e}")
            return False

    async def get_metrics(self,
                          aws_account_id: str,
                          service: str,
                          metric_name: str,
                          start_time: datetime,
                          end_time: datetime) -> List[Dict]:
        try:
            cache_key = f"metrics:{aws_account_id}:{service}:{metric_name}:{start_time.isoformat()}:{end_time.isoformat()}"
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Metrics cache_client hit for {aws_account_id}/{service}/{metric_name}")
                return cached

            # Query DynamoDB
            response = self.table.query(
                KeyConditionExpression=Key('pk').eq(
                    f"CLIENT#{aws_account_id}#{service}#{metric_name}"
                ) & Key('sk').between(
                    start_time.isoformat(),
                    end_time.isoformat()
                ),
                ScanIndexForward=True
            )

            items = response.get('Items', [])

            self.cache.set(cache_key, items, ttl=300)

            return items

        except Exception as e:
            logger.error(f"[{aws_account_id}] Error fetching metrics: {e}")
            return []

    async def get_latest_metrics(self,
                                 aws_account_id: str,
                                 service: str,
                                 metric_name: str,
                                 limit: int = 10) -> List[Dict]:

        try:
            response = self.table.query(
                KeyConditionExpression=Key('pk').eq(
                    f"CLIENT#{aws_account_id}#{service}#{metric_name}"
                ),
                ScanIndexForward=False,
                Limit=limit
            )
            return response.get('Items', [])

        except Exception as e:
            logger.error(f"[{aws_account_id}] Error fetching latest metrics: {e}")
            return []


class CostsModel(BaseModel):

    def __init__(self):
        super().__init__()
        self.table = self.db.get_table(settings.COSTS_TABLE)

    async def store_cost_data(self,
                              aws_account_id: str,
                              service: str,
                              date: str,
                              cost: Union[float, Decimal],
                              usage_quantity: Optional[Union[float, Decimal]] = None,
                              usage_unit: Optional[str] = None,
                              granularity: str = "DAILY") -> bool:

        try:
            decimal_cost = Decimal(str(cost))

            item = {
                'pk': f"CLIENT#{aws_account_id}#{service}",
                'sk': f"{date}#{granularity}",
                'aws_account_id': aws_account_id,
                'cost': decimal_cost,
                'date': date,
                'granularity': granularity,
                'currency': 'USD',
                'created_at': datetime.now().isoformat(),
                'ttl': int((datetime.now() + timedelta(days=settings.COSTS_TTL_DAYS)).timestamp())
            }

            if usage_quantity is not None:
                item['usage_quantity'] = Decimal(str(usage_quantity))
            if usage_unit:
                item['usage_unit'] = usage_unit

            self.table.put_item(Item=item)
            logger.debug(f"[{aws_account_id}] Stored cost data: {service} = ${cost}")
            return True

        except Exception as e:
            logger.error(f"[{aws_account_id}] Error storing cost data: {e}")
            return False

    async def get_cost_data(self,
                            aws_account_id: str,
                            service: str,
                            start_date: str,
                            end_date: str,
                            granularity: str = "DAILY") -> List[Dict]:
        try:
            response = self.table.query(
                KeyConditionExpression=Key('pk').eq(
                    f"CLIENT#{aws_account_id}#{service}"
                ) & Key('sk').between(
                    f"{start_date}#{granularity}",
                    f"{end_date}#{granularity}"
                ),
                ScanIndexForward=True
            )
            return response.get('Items', [])

        except Exception as e:
            logger.error(f"[{aws_account_id}] Error fetching cost data: {e}")
            return []


class SecurityFindingModel(BaseModel):

    def __init__(self):
        super().__init__()
        self.table = self.db.get_table(settings.SECURITY_TABLE)

    async def store_finding(self,
                            aws_account_id: str,
                            finding_type: str,
                            finding_id: str,
                            severity: str,
                            status: str,
                            title: str,
                            description: str,
                            service: str,
                            resource_id: Optional[str] = None) -> bool:
        try:
            item = {
                'pk': f"CLIENT#{aws_account_id}#{finding_type}",
                'sk': finding_id,
                'aws_account_id': aws_account_id,
                'severity': severity,
                'status': status,
                'title': title,
                'description': description,
                'service': service,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            if resource_id:
                item['resource_id'] = resource_id

            self.table.put_item(Item=item)
            logger.debug(f"[{aws_account_id}] Stored security finding: {finding_type}#{finding_id}")
            return True

        except Exception as e:
            logger.error(f"[{aws_account_id}] Error storing security finding: {e}")
            return False

    async def get_findings_by_type(self,
                                   aws_account_id: str,
                                   finding_type: str) -> List[Dict]:
        try:
            response = self.table.query(
                KeyConditionExpression=Key('pk').eq(
                    f"CLIENT#{aws_account_id}#{finding_type}"
                )
            )
            return response.get('Items', [])

        except Exception as e:
            logger.error(f"[{aws_account_id}] Error fetching findings: {e}")
            return []


class RecommendationModel(BaseModel):

    def __init__(self):
        super().__init__()
        self.table = self.db.get_table(settings.RECOMMENDATIONS_TABLE)

    async def store_recommendation(self,
                                   aws_account_id: str,
                                   rec_type: str,
                                   title: str,
                                   description: str,
                                   impact: str,
                                   effort: str,
                                   confidence: Union[float, Decimal],
                                   service: str,
                                   estimated_savings: Optional[Union[float, Decimal]] = None,
                                   resource_id: Optional[str] = None) -> Optional[str]:

        try:
            timestamp = datetime.now()
            rec_id = f"rec-{uuid.uuid4().hex[:8]}"

            item = {
                'pk': f"CLIENT#{aws_account_id}#{rec_type}",
                'sk': f"{timestamp.isoformat()}#{rec_id}",
                'aws_account_id': aws_account_id,
                'id': rec_id,
                'title': title,
                'description': description,
                'impact': impact,
                'effort': effort,
                'confidence': Decimal(str(confidence)),
                'service': service,
                'implemented': False,
                'created_at': timestamp.isoformat(),
                'updated_at': timestamp.isoformat()
            }

            if estimated_savings is not None:
                item['estimated_savings'] = Decimal(str(estimated_savings))
            if resource_id:
                item['resource_id'] = resource_id

            self.table.put_item(Item=item)
            logger.debug(f"[{aws_account_id}] Stored recommendation: {rec_type}#{rec_id}")
            return rec_id

        except Exception as e:
            logger.error(f"[{aws_account_id}] Error storing recommendation: {e}")
            return None

    async def get_recommendations_by_type(self,
                                          aws_account_id: str,
                                          rec_type: str) -> List[Dict]:
        try:
            response = self.table.query(
                KeyConditionExpression=Key('pk').eq(
                    f"CLIENT#{aws_account_id}#{rec_type}"
                ),
                ScanIndexForward=False
            )
            return response.get('Items', [])

        except Exception as e:
            logger.error(f"[{aws_account_id}] Error fetching recommendations: {e}")
            return []