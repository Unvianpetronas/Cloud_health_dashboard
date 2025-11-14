import logging
from typing import List, Dict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from botocore.exceptions import ClientError
from .client import AWSClientProvider
from .base_scanner import BaseAWSScanner

logger = logging.getLogger(__name__)

class CloudWatchScanner(BaseAWSScanner):
    """
    A simple class to get metrics from AWS CloudWatch.
    Can scan multiple regions in parallel to collect data faster.
    """

    def __init__(self, client_provider: AWSClientProvider):
        """
        Initialize scanner with an authenticated client provider.

        Args:
            client_provider (AWSClientProvider): Factory to create AWS clients.
        """
        self.client_provider = client_provider

    @BaseAWSScanner.with_retry()
    def _get_metric_data_in_one_region(
            self,
            region: str,
            namespace: str,
            metric_name: str,
            dimensions: List[Dict],
            start_time: datetime,
            end_time: datetime,
            period: int = 300,
            stat: str = "Average"
    ) -> Dict:
        """
        Worker function: Get metric data from a single region.
        This is an internal (private) function.
        """
        try:
            client = self.client_provider.get_client("cloudwatch", region_name=region)
            response = client.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=[stat],
            )
            return {
                "region": region,
                "datapoints": response.get("Datapoints", []),
                "label": response.get("Label", metric_name)
            }
        except ClientError as e:
            logger.error(f"Error getting metric {metric_name} in region {region}: {e}")
            return {"region": region, "datapoints": [], "label": metric_name}
        except Exception as e:
            logger.error(f"Unknown error in region {region}: {e}")
            return {"region": region, "datapoints": [], "label": metric_name}

    @BaseAWSScanner.with_retry()
    def scan_all_regions(
            self,
            namespace: str,
            metric_name: str,
            dimensions: List[Dict],
            start_time: datetime,
            end_time: datetime,
            period: int = 300,
            stat: str = "Average"
    ) -> Dict:
        """
        Manager function: Coordinates parallel scanning across all regions.
        This is the main function you'll call from outside.
        """
        # 1. Get list of all regions
        base_client = self.client_provider.get_client("ec2")
        all_regions = [r["RegionName"] for r in base_client.describe_regions()["Regions"]]

        all_metrics = []

        # 2. Send workers to all regions at once
        with ThreadPoolExecutor(max_workers=len(all_regions)) as executor:
            future_to_region = {
                executor.submit(
                    self._get_metric_data_in_one_region,
                    region,
                    namespace,
                    metric_name,
                    dimensions,
                    start_time,
                    end_time,
                    period,
                    stat
                ): region
                for region in all_regions
            }

            # 3. Collect results from all workers
            for future in future_to_region:
                result = future.result()
                if result["datapoints"]:
                    all_metrics.append(result)

        # 4. Return final report
        return {
            "metric": metric_name,
            "namespace": namespace,
            "regions_scanned": len(all_regions),
            "results": all_metrics
        }

    @BaseAWSScanner.with_retry()
    def get_metric_statistics(
            self,
            region: str,
            namespace: str,
            metric_name: str,
            dimension: Dict,
            period: int = 3600
    ) -> Dict:
        """
        Get metric statistics for a single region with a single dimension.
        This is a convenience method for architecture analysis.

        Args:
            region: AWS region
            namespace: CloudWatch namespace (e.g., 'AWS/EC2')
            metric_name: Name of the metric (e.g., 'CPUUtilization')
            dimension: Single dimension dict (e.g., {'Name': 'InstanceId', 'Value': 'i-1234'})
            period: Period in seconds (default: 3600 = 1 hour)

        Returns:
            Dict with metric data
        """
        from datetime import datetime, timedelta, UTC

        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(seconds=period)

        # Convert single dimension dict to list format
        dimensions = [dimension] if dimension else []

        try:
            client = self.client_provider.get_client("cloudwatch", region_name=region)
            response = client.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=["Average", "Maximum", "Minimum"],
            )
            return {
                "region": region,
                "datapoints": response.get("Datapoints", []),
                "label": response.get("Label", metric_name)
            }
        except ClientError as e:
            logger.error(f"Error getting metric {metric_name} in region {region}: {e}")
            return {"region": region, "datapoints": [], "label": metric_name}
        except Exception as e:
            logger.error(f"Unknown error in region {region}: {e}")
            return {"region": region, "datapoints": [], "label": metric_name}
