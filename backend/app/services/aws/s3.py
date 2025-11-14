from typing import Dict, List
from botocore.exceptions import ClientError
from .client import AWSClientProvider
import logging
from datetime import datetime, timedelta, UTC
from .base_scanner import BaseAWSScanner
logger = logging.getLogger(__name__)

class S3Scanner(BaseAWSScanner):
    """
    Scans S3 bucket information: name, region, storage usage.
    Useful for monitoring and cost optimization.
    """

    def __init__(self, client_provider: AWSClientProvider):
        self.client_provider = client_provider

    @BaseAWSScanner.with_retry()
    def list_buckets(self) -> List[Dict]:
        """
        List all buckets with their regions.
        """
        try:
            client = self.client_provider.get_client("s3")
            response = client.list_buckets()
            buckets = response.get("Buckets", [])

            results = []
            for bucket in buckets:
                bucket_name = bucket["Name"]
                # Get regions for each bucket
                try:
                    region_resp = client.get_bucket_location(Bucket=bucket_name)
                    region = region_resp.get("LocationConstraint") or "us-east-1"
                except ClientError as e:
                    logger.error(f"Error getting bucket region for {bucket_name}: {e}")
                    region = "unknown"

                results.append({
                    "bucket": bucket_name,
                    "region": region,
                })

            return results
        except ClientError as e:
            logger.error(f"Error listing buckets: {e}")
            return []

    @BaseAWSScanner.with_retry()
    def get_bucket_storage_metrics(self, bucket_name: str, region: str) -> Dict:
        """
        Get storage size and object count metrics from CloudWatch.
        """
        try:
            cloudwatch = self.client_provider.get_client("cloudwatch", region_name=region)
            end = datetime.now(UTC)
            start = end - timedelta(days=1)

            metrics = {}

            # StandardStorage size (bytes)
            size_resp = cloudwatch.get_metric_statistics(
                Namespace="AWS/S3",
                MetricName="BucketSizeBytes",
                Dimensions=[
                    {"Name": "BucketName", "Value": bucket_name},
                    {"Name": "StorageType", "Value": "StandardStorage"}
                ],
                StartTime=start,
                EndTime=end,
                Period=86400,  # daily
                Statistics=["Average"],
            )
            datapoints = size_resp.get("Datapoints", [])
            if datapoints:
                metrics["StandardStorageBytes"] = datapoints[-1]["Average"]

            # NumberOfObjects
            obj_resp = cloudwatch.get_metric_statistics(
                Namespace="AWS/S3",
                MetricName="NumberOfObjects",
                Dimensions=[
                    {"Name": "BucketName", "Value": bucket_name},
                    {"Name": "StorageType", "Value": "AllStorageTypes"}
                ],
                StartTime=start,
                EndTime=end,
                Period=86400,
                Statistics=["Average"],
            )
            datapoints = obj_resp.get("Datapoints", [])
            if datapoints:
                metrics["ObjectCount"] = datapoints[-1]["Average"]

            return metrics

        except ClientError as e:
            logger.error(f"Error getting metrics for bucket {bucket_name}: {e}")
            return {}

    @BaseAWSScanner.with_retry()
    def scan_all_buckets(self) -> Dict:
        """
        Scan all buckets in account with storage metrics.
        """
        buckets = self.list_buckets()
        results = []

        for b in buckets:
            storage = self.get_bucket_storage_metrics(b["bucket"], b["region"])
            is_public = self._check_public_buckets(b["bucket"])
            results.append({
                "bucket": b["bucket"],
                "region": b["region"],
                "metrics": storage,
                "security" : is_public
            })

        return {
            "total_buckets": len(results),
            "buckets": results
        }

    def list_all_buckets(self) -> Dict:
        """
        Scan all buckets and return in format expected by architecture analyzer.
        """
        buckets = self.list_buckets()
        results = []

        for b in buckets:
            storage = self.get_bucket_storage_metrics(b["bucket"], b["region"])
            security_info = self._check_public_buckets(b["bucket"])
            encryption_enabled = self._check_bucket_encryption(b["bucket"])

            results.append({
                "Name": b["bucket"],
                "Region": b["region"],
                "encryption_enabled": encryption_enabled,
                "public_access": security_info["is_public"],
                "size_bytes": storage.get("StandardStorageBytes", 0),
                "object_count": storage.get("ObjectCount", 0)
            })

        return {
            "total_buckets": len(results),
            "buckets": results
        }

    def _check_public_buckets (self, bucket_name : str):
        """
        Check if a bucket is public or not.
        """
        client = self.client_provider.get_client("s3")
        is_public = False
        reasons = []

        try:
            response = client.get_public_access_block(Bucket=bucket_name)
            conf = response.get("PublicAccessBlockConfiguration", {})
            if conf.get("BlockPublicAcls") and conf.get("BlockPublicPolicy") and conf.get("IgnorePublicAcls") and conf.get("RestrictPublicBuckets"):
                pass
            else:
                pass
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                reasons.append("No Public Access Block configuration found (High Risk)")
            else:
                logger.warning(f"Could not check Public Access Block for {bucket_name}: {e}")
        try:
            response = client.get_bucket_acl(Bucket=bucket_name)
            for grant in response.get('Grants', []):
                grantee = grant.get('Grantee', {})
                if grantee.get('Type') == 'Group':
                    uri = grantee.get('URI', '')
                    if 'AllUsers' in uri or 'AuthenticatedUsers' in uri:
                        is_public = True
                        reasons.append(f"ACL allows {uri.split('/')[-1]}")
        except ClientError as e:
            logger.warning(f" Error checking ACL for {bucket_name}: {e}")

        try:
            policy_status = client.get_bucket_policy_status(Bucket=bucket_name)
            if policy_status.get('PolicyStatus', {}).get('IsPublic'):
                is_public = True
                reasons.append("Bucket Policy allows public access")
        except ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchBucketPolicy':
                logger.warning(f"Could not check Bucket Policy Status for {bucket_name}: {e}")

        return {
            "is_public": is_public,
            "reasons": reasons
        }

    def _check_bucket_encryption(self, bucket_name: str) -> bool:
        """
        Check if bucket has encryption enabled.

        Returns:
            bool: True if encryption enabled, False otherwise
        """
        try:
            client = self.client_provider.get_client("s3")
            response = client.get_bucket_encryption(Bucket=bucket_name)
            return True  # If no exception, encryption is configured
        except ClientError as e:
            if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                return False
            else:
                logger.warning(f"Could not check encryption for {bucket_name}: {e}")
                return False  # Assume not encrypted if can't check
