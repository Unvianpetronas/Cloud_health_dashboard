import boto3
import logging
from typing import Dict, Any
from botocore.exceptions import ClientError, NoCredentialsError
from app.config import settings


logger = logging.getLogger(__name__)


class DynamoDBConnection:
    _instance = None

    def __new__(cls):
        """Singleton pattern to ensure only one connection instance"""
        if cls._instance is None:
            cls._instance = super(DynamoDBConnection, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        """Connect to YOUR AWS account for storing client monitoring data"""
        if self.initialized:
            return

        self.region_name = settings.YOUR_AWS_REGION
        self.dynamodb = None
        self.dynamodb_client = None
        self.initialized = True

        self._initialize_connection()

    def _initialize_connection(self):
        """Initialize DynamoDB connection"""
        try:
            # Use YOUR credentials for DynamoDB storage
            if settings.YOUR_AWS_ACCESS_KEY_ID and settings.YOUR_AWS_SECRET_ACCESS_KEY:
                self.dynamodb = boto3.resource(
                    'dynamodb',
                    region_name=settings.YOUR_AWS_REGION,
                    aws_access_key_id=settings.YOUR_AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.YOUR_AWS_SECRET_ACCESS_KEY
                )
                self.dynamodb_client = boto3.client(
                    'dynamodb',
                    region_name=settings.YOUR_AWS_REGION,
                    aws_access_key_id=settings.YOUR_AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.YOUR_AWS_SECRET_ACCESS_KEY
                )
                logger.info("Connected to YOUR DynamoDB account for data storage")
            else:
                # Use default credentials for YOUR account
                self.dynamodb = boto3.resource('dynamodb', region_name=settings.YOUR_AWS_REGION)
                self.dynamodb_client = boto3.client('dynamodb', region_name=settings.YOUR_AWS_REGION)
                logger.info("Using default credentials for YOUR DynamoDB account")

        except NoCredentialsError:
            logger.error("AWS credentials not found for YOUR account")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize YOUR DynamoDB connection: {e}")
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
            logger.info("YOUR DynamoDB connection test successful")
            return True
        except Exception as e:
            logger.error(f"YOUR DynamoDB connection test failed: {e}")
            return False

    def create_tables(self) -> bool:
        """Create all required DynamoDB tables"""
        try:
            from .schemas.table_definitions import TABLE_DEFINITIONS

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
                if 'ttl_attribute' in table_definition:
                    self._enable_ttl(self.dynamodb_client)

                logger.info(f"Table {table_name} created successfully")
            else:
                logger.error(f"Error checking/creating table {table_name}: {e}")
                raise

    def _enable_ttl(self, dynamodb_client):
        """Enable TTL on a table"""
        tables_with_ttl = ["CloudHealthMetrics", "CloudHealthCosts"]
        for table_name in tables_with_ttl:
            try:
                dynamodb_client.update_time_to_live(
                    TableName=table_name,
                    TimeToLiveSpecification={
                        'AttributeName': 'ttl',
                        'Enabled': True
                    }
                )
                print(f"TTL enabled for {table_name}")
            except Exception as e:
                print(f"Error enabling TTL for {table_name}: {e}")

    def list_tables(self) -> list:
        """List all tables in YOUR DynamoDB account"""
        try:
            response = self.dynamodb_client.list_tables()
            return response.get('TableNames', [])
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return []

    def delete_table(self, table_name: str) -> bool:
        """Delete a table (use with caution!)"""
        try:
            table = self.dynamodb.Table(table_name)
            table.delete()
            table.wait_until_not_exists()
            logger.info(f"Table {table_name} deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting table {table_name}: {e}")
            return False