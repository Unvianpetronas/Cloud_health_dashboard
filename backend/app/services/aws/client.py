import boto3
from typing import Optional

class AWSClientProvider:

    def __init__(self, access_key: str, secret_key: str, region: str = 'us-east-1'):

        self.session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )

    def get_client(self, service_name: str, region_name: Optional[str] = None):
        """
        Creates and returns a low-level service client (e.g., for EC2, S3, RDS).

        Args:
            service_name (str): The name of the AWS service (e.g., 'ec2').
            region_name (Optional[str]): An optional region to override the default session region.

        Returns:
            A pre-configured Boto3 service client instance.
        """
        return self.session.client(service_name, region_name=region_name)

    def get_resource(self, service_name: str, region_name: Optional[str] = None):
        """
        Creates and returns a high-level, object-oriented service resource.

        Args:
            service_name (str): The name of the AWS service (e.g., 'dynamodb').
            region_name (Optional[str]): An optional region to override the default session region.

        Returns:
            A pre-configured Boto3 service resource instance.
        """
        return self.session.resource(service_name, region_name=region_name)