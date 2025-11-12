import logging
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
from botocore.exceptions import ClientError

from .base_scanner import BaseAWSScanner
from .client import AWSClientProvider

logger = logging.getLogger(__name__)

class SecurityHubScanner:
    """
    Một class đơn giản để quét các findings từ AWS Security Hub.
    Nó có thể lấy findings từ nhiều region song song (nếu Security Hub được bật).
    """

    def __init__(self, client_provider: AWSClientProvider):
        """
        Khởi tạo scanner với một client provider đã được xác thực.

        Args:
            client_provider (AWSClientProvider): Factory để tạo các AWS client.
        """
        self.client_provider = client_provider
    @BaseAWSScanner.with_retry()
    def _get_findings_in_one_region(self, region: str) -> List[Dict]:
        """
        Hàm "worker": Lấy tất cả Security Hub findings từ một region.
        """
        try:
            client = self.client_provider.get_client("securityhub", region_name=region)
            paginator = client.get_paginator("get_findings")
            findings = []
            for page in paginator.paginate():
                findings.extend(page.get("Findings", []))
            return findings
        except ClientError as e:
            logger.error(f"Lỗi khi lấy findings ở region {region}: {e}")
            return []
        except Exception as e:
            logger.error(f"Lỗi không xác định ở region {region}: {e}")
            return []

    @BaseAWSScanner.with_retry()
    def scan_all_regions(self) -> Dict:
        """
        Hàm "Quản lý": Quét Security Hub findings trên tất cả các region có sẵn.
        """
        # 1. Lấy danh sách region
        base_client = self.client_provider.get_client("ec2")
        all_regions = [r["RegionName"] for r in base_client.describe_regions()["Regions"]]

        all_findings = []

        # 2. Gửi worker song song
        with ThreadPoolExecutor(max_workers=len(all_regions)) as executor:
            future_to_region = {
                executor.submit(self._get_findings_in_one_region, region): region
                for region in all_regions
            }

            for future in future_to_region:
                findings_in_region = future.result()
                if findings_in_region:
                    all_findings.extend(findings_in_region)

        # 3. Trả về kết quả
        return {
            "total_findings": len(all_findings),
            "findings": all_findings,
            "regions_scanned": len(all_regions),
        }
