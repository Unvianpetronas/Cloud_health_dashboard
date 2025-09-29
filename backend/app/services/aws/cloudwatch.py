import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from botocore.exceptions import ClientError
from .client import AWSClientProvider

logger = logging.getLogger(__name__)

class CloudWatchScanner:
    """
    Một class đơn giản để lấy metrics từ AWS CloudWatch.
    Nó có thể quét song song nhiều region để thu thập dữ liệu nhanh hơn.
    """

    def __init__(self, client_provider: AWSClientProvider):
        """
        Khởi tạo scanner với một client provider đã được xác thực.

        Args:
            client_provider (AWSClientProvider): Factory để tạo các AWS client.
        """
        self.client_provider = client_provider

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
        Hàm "Công nhân": Lấy dữ liệu metric từ một region duy nhất.
        Đây là một hàm nội bộ (private).
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
            logger.error(f"Lỗi khi lấy metric {metric_name} ở region {region}: {e}")
            return {"region": region, "datapoints": [], "label": metric_name}
        except Exception as e:
            logger.error(f"Lỗi không xác định ở region {region}: {e}")
            return {"region": region, "datapoints": [], "label": metric_name}

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
        Hàm "Quản lý": Điều phối việc quét song song trên tất cả các region.
        Đây là hàm chính mà bạn sẽ gọi từ bên ngoài.
        """
        # 1. Lấy danh sách tất cả các region
        base_client = self.client_provider.get_client("ec2")
        all_regions = [r["RegionName"] for r in base_client.describe_regions()["Regions"]]

        all_metrics = []

        # 2. Gửi "công nhân" đến tất cả các region cùng một lúc
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

            # 3. Thu thập kết quả từ tất cả "công nhân"
            for future in future_to_region:
                result = future.result()
                if result["datapoints"]:
                    all_metrics.append(result)

        # 4. Trả về báo cáo cuối cùng
        return {
            "metric": metric_name,
            "namespace": namespace,
            "regions_scanned": len(all_regions),
            "results": all_metrics
        }
