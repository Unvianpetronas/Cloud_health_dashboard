from typing import Dict, List
from botocore.exceptions import ClientError
from .client import AWSClientProvider
import logging
from datetime import datetime, timedelta, UTC

logger = logging.getLogger(__name__)

class S3Scanner:
    """
    Quét thông tin về S3 buckets: tên, region, storage usage.
    Hữu ích cho monitoring và cost optimization.
    """

    def __init__(self, client_provider: AWSClientProvider):
        self.client_provider = client_provider

    def list_buckets(self) -> List[Dict]:
        """
        Liệt kê tất cả buckets + region.
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
                    logger.error(f"Lỗi khi lấy region của bucket {bucket_name}: {e}")
                    region = "unknown"

                results.append({
                    "bucket": bucket_name,
                    "region": region,
                })

            return results
        except ClientError as e:
            logger.error(f"Lỗi khi list buckets: {e}")
            return []

    def get_bucket_storage_metrics(self, bucket_name: str, region: str) -> Dict:
        """
        Lấy metric về storage size & object count từ CloudWatch.
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
            logger.error(f"Lỗi khi lấy metric cho bucket {bucket_name}: {e}")
            return {}

    def scan_all_buckets(self) -> Dict:
        """
        Quét toàn bộ buckets trong account + thêm storage metrics.
        """
        buckets = self.list_buckets()
        results = []

        for b in buckets:
            storage = self.get_bucket_storage_metrics(b["bucket"], b["region"])
            results.append({
                "bucket": b["bucket"],
                "region": b["region"],
                "metrics": storage
            })

        return {
            "total_buckets": len(results),
            "buckets": results
        }
