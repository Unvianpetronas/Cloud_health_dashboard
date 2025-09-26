from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict
from .client import AWSClientProvider

class EC2Scanner:
    """
    Một class đơn giản để tìm tất cả các máy chủ EC2 trong một tài khoản AWS.
    Nó tự động quét tất cả các khu vực một cách song song để có tốc độ nhanh nhất.
    """
    def __init__(self, client_provider: AWSClientProvider):
        """
        Khởi tạo scanner với một client provider đã được xác thực.

        Args:
            client_provider (AWSClientProvider): Factory để tạo các AWS client.
        """
        self.client_provider = client_provider

    def _get_instances_in_one_region(self, region: str) -> List[Dict]:
        """
        Hàm "Công nhân": Lấy tất cả các máy chủ trong một khu vực duy nhất.
        Đây là một hàm nội bộ (private).
        """
        try:
            # Tạo một client chỉ dành riêng cho khu vực này
            regional_client = self.client_provider.get_client('ec2', region_name=region)
            paginator = regional_client.get_paginator('describe_instances')
            instances = []
            for page in paginator.paginate():
                for reservation in page['Reservations']:
                    instances.extend(reservation['Instances'])
            return instances
        except Exception:
            # Bỏ qua nếu có lỗi (ví dụ: khu vực không được kích hoạt)
            return []

    def scan_all_regions(self) -> Dict:
        """
        Hàm "Quản lý": Điều phối việc quét song song trên tất cả các khu vực.
        Đây là hàm chính mà bạn sẽ gọi từ bên ngoài.
        """
        # 1. Lấy danh sách tất cả các khu vực có thể có
        base_client = self.client_provider.get_client('ec2')
        all_regions = [region['RegionName'] for region in base_client.describe_regions()['Regions']]

        all_found_instances = []

        # 2. Gửi "công nhân" đến tất cả các khu vực cùng một lúc
        with ThreadPoolExecutor(max_workers=len(all_regions)) as executor:
            # Tạo một nhiệm vụ cho mỗi khu vực
            future_to_region = {
                executor.submit(self._get_instances_in_one_region, region): region
                for region in all_regions
            }

            # 3. Đợi và thu thập kết quả từ tất cả "công nhân"
            for future in future_to_region:
                instances_in_region = future.result()
                if instances_in_region:
                    all_found_instances.extend(instances_in_region)

        # 4. Trả về báo cáo cuối cùng
        return {
            "total_instances_found": len(all_found_instances),
            "instances": all_found_instances,
            "regions_scanned": len(all_regions)
        }


