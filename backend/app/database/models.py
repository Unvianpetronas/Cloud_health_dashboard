from datetime import datetime, timedelta
from typing import Dict, Optional, List, Union
from boto3.dynamodb.conditions import Key, Attr
import uuid
import logging
from app.database.dynamodb import DynamoDBConnection
from app.config import settings
from decimal import Decimal
from app.utils.client_encryption import ClientEncryption
logger = logging.getLogger(__name__)


class BaseModel:
    def __init__(self):
        self.db = DynamoDBConnection()


class ClientModel(BaseModel):

    def __init__(self):
        super().__init__()
        self.table = self.db.get_table(settings.CLIENTS_TABLE)
        self.encryption = ClientEncryption()

    async def create_client(self,
                            email: str,
                            company_name: str,
                            aws_account_id: str,
                            aws_access_key: str,
                            aws_secret_key: str,
                            aws_region: str = "us-east-1") -> Optional[str]:

        try:
            existing_by_account = await self.get_client_by_aws_account_id(aws_account_id)
            if existing_by_account:
                logger.warning(f"Client with AWS Account ID {aws_account_id} already exists")
                return None

            encrypted_access = self.encryption.encrypt_credential(aws_access_key)
            encrypted_secret = self.encryption.encrypt_credential(aws_secret_key)

            item = {
                'pk': f"CLIENT#{aws_account_id}",
                'sk': 'METADATA',
                'aws_account_id': aws_account_id,
                'email': email.lower(),
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
                    'warning_alerts': False,
                    'cost_alerts': True,
                    'daily_summary': False
                }
            }

            self.table.put_item(Item=item)
            logger.info(f"Created client {aws_account_id} for {email}")
            return aws_account_id

        except Exception as e:
            logger.error(f"Error creating client: {e}", exc_info=True)
            return None

    async def get_client(self, aws_account_id: str) -> Optional[Dict]:
        try:
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
            logger.error(f"Error getting client {aws_account_id}: {e}", exc_info=True)
            return None

    async def get_client_by_aws_account_id(self, aws_account_id: str) -> Optional[Dict]:
        try:
            response = self.table.query(
                IndexName='AwsAccountIdIndex',
                KeyConditionExpression=Key('aws_account_id').eq(aws_account_id)
            )

            items = response.get('Items', [])
            if not items:
                return None

            client = items[0]

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
            logger.error(f"Error getting client by AWS Account ID: {e}")
            return None

    async def get_client_by_email(self, email: str) -> Optional[Dict]:
        try:
            response = self.table.query(
                IndexName='EmailIndex',
                KeyConditionExpression=Key('email').eq(email.lower())
            )

            items = response.get('Items', [])
            if not items:
                return None

            client = items[0]

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
        try:
            response = self.table.scan(
                FilterExpression=Attr('status').eq('active') &
                                 Attr('sk').eq('METADATA')
            )

            clients = []
            for item in response.get('Items', []):
                try:
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
                UpdateExpression='SET last_collection = :timestamp',
                ExpressionAttributeValues={
                    ':timestamp': datetime.now().isoformat()
                }
            )
            return True

        except Exception as e:
            logger.error(f"Error updating last collection: {e}")
            return False

    async def delete_client_data(self, aws_account_id: str) -> bool:
        try:
            return await self.update_client_status(aws_account_id, 'deleted')

        except Exception as e:
            logger.error(f"Error deleting client data: {e}")
            return False

    async def verify_email(self, token: str) -> Optional[str]:
        try:
            response = self.table.scan(
                FilterExpression=Attr('email_verification_token').eq(token) &
                                 Attr('sk').eq('METADATA')
            )

            items = response.get('Items', [])
            if not items:
                logger.warning("Invalid verification token")
                return None

            client = items[0]

            expires_at = datetime.fromisoformat(client['email_verification_expires'])
            if datetime.now() > expires_at:
                logger.warning(f"Verification token expired for {client['client_id']}")
                return None

            self.table.update_item(
                Key={'pk': client['pk'], 'sk': 'METADATA'},
                UpdateExpression='SET email_verified = :verified, email_verification_token = :empty, updated_at = :updated',
                ExpressionAttributeValues={
                    ':verified': True,
                    ':empty': '',
                    ':updated': datetime.now().isoformat()
                }
            )

            logger.info(f"Email verified for client {client['client_id']}")
            return client['client_id']

        except Exception as e:
            logger.error(f"Error verifying email: {e}", exc_info=True)
            return None

    async def update_email(self, client_id: str, new_email: str) -> bool:
        try:
            existing = await self.get_client_by_email(new_email)
            if existing and existing['client_id'] != client_id:
                logger.warning(f"Email {new_email} already in use")
                return False

            self.table.update_item(
                Key={'pk': f"CLIENT#{client_id}", 'sk': 'METADATA'},
                UpdateExpression='SET email = :email, email_verified = :verified, updated_at = :updated',
                ExpressionAttributeValues={
                    ':email': new_email.lower(),
                    ':verified': False,
                    ':updated': datetime.now().isoformat()
                }
            )

            # Send verification email to new address
            await self.send_verification_email(client_id)

            logger.info(f"📧 Email updated to {new_email} for {client_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating email: {e}", exc_info=True)
            return False

    async def update_notification_preferences(self, client_id: str, preferences: dict) -> bool:
        """Update notification preferences"""
        try:
            self.table.update_item(
                Key={'pk': f"CLIENT#{client_id}", 'sk': 'METADATA'},
                UpdateExpression='SET notification_preferences = :prefs, updated_at = :updated',
                ExpressionAttributeValues={
                    ':prefs': preferences,
                    ':updated': datetime.now().isoformat()
                }
            )

            logger.info(f"Updated notification preferences for {client_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating preferences: {e}")
            return False


class MetricsModel(BaseModel):

    def __init__(self):
        super().__init__()
        self.table = self.db.get_table(settings.METRICS_TABLE)

    async def store_metric(self,
                           aws_account_id: str,
                           service: str,
                           metric_name: str,
                           value: Union[float, int, Decimal],
                           timestamp: Optional[datetime] = None,
                           unit: str = "Count",
                           dimensions: Optional[Dict] = None) -> bool:

        try:
            if timestamp is None:
                timestamp = datetime.now()

            decimal_value = Decimal(str(value))

            item = {
                'pk': f"CLIENT#{aws_account_id}#{service}#{metric_name}",  # ⭐ FIXED
                'sk': timestamp.isoformat(),
                'gsi1_pk': f"{metric_name}#{timestamp.isoformat()}",
                'aws_account_id': aws_account_id,
                'value': decimal_value,
                'unit': unit,
                'service': service,
                'metric_name': metric_name,
                'dimensions': dimensions or {},
                'created_at': timestamp.isoformat(),
                'ttl': int((timestamp + timedelta(days=settings.METRICS_TTL_DAYS)).timestamp())
            }

            self.table.put_item(Item=item)
            logger.debug(f"[{aws_account_id}] Stored metric: {service}#{metric_name} = {value}")
            return True

        except Exception as e:
            logger.error(f"[{aws_account_id}] Error storing metric: {e}")
            return False

    async def get_metrics(self,
                          aws_account_id,
                          service: str,
                          metric_name: str,
                          start_time: datetime,
                          end_time: datetime) -> List[Dict]:
        try:
            response = self.table.query(
                KeyConditionExpression=Key('pk').eq(
                    f"CLIENT#{aws_account_id}#{service}#{metric_name}"
                ) & Key('sk').between(
                    start_time.isoformat(),
                    end_time.isoformat()
                ),
                ScanIndexForward=True
            )
            return response.get('Items', [])

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
                              aws_account_id: str,  # ⭐ ADDED
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
                    f"CLIENT#{aws_account_id}#{service}"  # ⭐ FIXED
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
                                   aws_account_id: str,  #
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