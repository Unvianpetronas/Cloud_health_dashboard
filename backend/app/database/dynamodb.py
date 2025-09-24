# backend/app/database/dynamodb.py

import boto3
import logging
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, Any
from app.config import settings
logger = logging.getLogger(__name__)

class DynamoDBConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DynamoDBConnection, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return

        self.region_name = settings.AWS_REGION
        self.dynamodb = None
        self.dynamodb_client = None
        self.initialized = True

        self._initialize_connection()

    def _initialize_connection(self):
        """Initialize DynamoDB connection"""
        try:
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                self.dynamodb = boto3.resource(
                    'dynamodb',
                    region_name=self.region_name,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                )
                self.dynamodb_client = boto3.client(
                    'dynamodb',
                    region_name=self.region_name,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                )
            else:
                # Use default credentials (AWS CLI, IAM role, etc.)
                self.dynamodb = boto3.resource('dynamodb', region_name=self.region_name)
                self.dynamodb_client = boto3.client('dynamodb', region_name=self.region_name)

            logger.info("DynamoDB connection initialized successfully")

        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB connection: {e}")
            raise

    def get_table(self, table_name: str):
        """Get a DynamoDB table resource"""
        try:
            if not self.dynamodb:
                raise Exception("DynamoDB connection not initialized")

            table = self.dynamodb.Table(table_name)
            return table
        except Exception as e:
            logger.error(f"Error getting table {table_name}: {e}")
            raise

    async def test_connection(self) -> bool:
        """Test DynamoDB connection"""
        try:
            if not self.dynamodb_client:
                return False

            response = self.dynamodb_client.list_tables(Limit=1)
            logger.info("DynamoDB connection test successful")
            return True
        except Exception as e:
            logger.error(f"DynamoDB connection test failed: {e}")
            return False

    def create_tables(self) -> bool:
        """Create all required DynamoDB tables"""
        # FIXED IMPORT:
        from .schemas.table_definitions import TABLE_DEFINITIONS

        try:
            for table_def in TABLE_DEFINITIONS:
                self._create_table_if_not_exists(table_def)
            return True
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            return False

    def _create_table_if_not_exists(self, table_definition: Dict[str, Any]):
        """Create a single table if it doesn't exist"""
        table_name = table_definition['TableName']

        try:
            # Check if table exists
            self.dynamodb_client.describe_table(TableName=table_name)
            logger.info(f"Table {table_name} already exists")

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Table doesn't exist, create it
                logger.info(f"Creating table {table_name}...")

                # Remove custom fields for AWS API
                aws_table_def = {k: v for k, v in table_definition.items()
                                 if k not in ['ttl_attribute']}

                table = self.dynamodb.create_table(**aws_table_def)
                table.wait_until_exists()

                # Enable TTL if specified
                if 'ttl_attribute' in table_definition:
                    self._enable_ttl(table_name, table_definition['ttl_attribute'])

                logger.info(f"Table {table_name} created successfully")
            else:
                logger.error(f"Error checking/creating table {table_name}: {e}")
                raise

    def _enable_ttl(self, table_name: str, ttl_attribute: str):
        """Enable TTL on a table"""
        try:
            self.dynamodb_client.update_time_to_live(
                TableName=table_name,
                TimeToLiveSpecification={
                    'AttributeName': ttl_attribute,
                    'Enabled': True
                }
            )
            logger.info(f"TTL enabled on {table_name}")
        except Exception as e:
            logger.warning(f"Could not enable TTL on {table_name}: {e}")