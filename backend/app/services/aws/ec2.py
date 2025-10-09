from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from .client import AWSClientProvider
import logging


logger =logging.getLogger(__name__)


class EC2Scanner:

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
        if not all_found_instances:
            return {
                "total_instances_found": 0,
                "instances": [],
                "regions_scanned": len(all_regions),
                "message": "No EC2 instances found in any region",
                "has_instances": False
            }

        return {
            "total_instances_found": len(all_found_instances),
            "instances": all_found_instances,
            "regions_scanned": len(all_regions),
            "has_instances": True
        }


    def Scan_specific_region(self,region: str) -> Dict[str, Any]:
        instances = self._get_instances_in_one_region(region)
        return {
            "region": region,
            "total_instances": len(instances),
            "instances": instances,
            "by_state": self._group_by_state(instances)
        }


    def get_running_instances(self) -> Dict[str, Any]:
        all_instances = self.scan_all_regions()
        running = [
            inst for inst in all_instances['instances']
            if inst.get('State', {}).get('Name') == 'running'
        ]
        return {
            'total_running' : len(running),
            'instances' : running,
            'by_region' : self._group_by_region(running)
        }

    def _group_by_region(self, instances: List[Dict]) -> Dict[str, int]:
        """Group instance count by region"""
        region_count = {}
        for inst in instances:
            region = inst.get('Region', 'unknown')
            region_count[region] = region_count.get(region, 0) + 1
        return region_count

    def _group_by_state(self, instances: List[Dict]) -> Dict[str, int]:
        state_count = {}
        for inst in instances:
            state = inst.get('State', {}).get('Name', 'unknown')
            state_count[state] = state_count.get(state, 0) + 1
        return state_count

    def estimate_monthly_cost(self) -> Dict[str, Any]:
        HOURLY_PRICES = {
            't2.micro': 0.0116,
            't2.small': 0.023,
            't2.medium': 0.0464,
            't3.micro': 0.0104,
            't3.small': 0.0208,
            't3.medium': 0.0416,
            'm5.large': 0.096,
            'm5.xlarge': 0.192,
        }

        instances = self.get_running_instances()['instances']
        total_estimated_cost = 0
        cost_breakdown = []

        if not instances:
            return {
                "total_estimated_cost": 0.0,
                "cost_breakdown": [],
                "running_instances": 0,
                "message": "No running EC2 instances to calculate costs",
                "has_cost_data": False
            }

        for inst in instances:
            inst_id = inst.get('InstanceId')
            inst_type = inst.get('InstanceType')
            region = inst.get('Region')
            launch_time = inst.get('LaunchTime')


            if launch_time:
                now = datetime.now(launch_time.tzinfo)
                runtime_hours = (now - launch_time).total_seconds() / 3600
                first_day_this_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                if launch_time >= first_day_this_month.replace(tzinfo=launch_time.tzinfo):
                    estimated_hours = runtime_hours
                else:
                    estimated_hours = self._estimate_monthly_hours(inst_id, region)
            else:
                estimated_hours = 730

            hourly_cost = HOURLY_PRICES.get(inst_type, 0.05)
            estimated_cost = hourly_cost * estimated_hours

            total_estimated_cost += estimated_cost

            cost_breakdown.append({
                'instance_id': inst_id,
                'instance_type': inst_type,
                'region': region,
                'estimated_hours': round(estimated_hours, 2),
                'hourly_rate': hourly_cost,
                'estimated_cost': round(estimated_cost, 2),
                'assumption': 'actual_runtime' if launch_time else 'full_month_estimate'
            })

        return {
            "total_estimated_cost": round(total_estimated_cost, 2),
            "cost_breakdown": cost_breakdown,
            "running_instances": len(instances),
            "calculation_method": "based on launch time and current state",
            "limitations": [
                "Does not account for stop/start cycles",
                "Assumes continuous runtime since launch",
                "Actual costs may vary by region and usage patterns"
            ]
        }

    def _estimate_monthly_hours(self, instance_id: str, region: str) -> float:
        try:
            ce_client = self.client_provider.get_client('ce', region_name=region)

            from datetime import datetime
            import calendar

            today = datetime.now()
            first_day = today.replace(day=1)
            _, last_day_num = calendar.monthrange(today.year, today.month)
            last_day = today.replace(day=last_day_num)

            response = ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': first_day.strftime('%Y-%m-%d'),
                    'End': last_day.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UsageQuantity'],
                Filter={
                    'Dimensions': {
                        'Key': 'RESOURCE_ID',
                        'Values': [instance_id]
                    }
                }
            )

            if response['ResultsByTime']:
                usage = float(response['ResultsByTime'][0]['Total']['UsageQuantity']['Amount'])
                return usage

            return 730

        except Exception as e:
            logger.warning(f"Could not get actual usage for {instance_id}: {e}")
            return 730


    def get_instance_summary(self) -> Dict[str, Any]:
        all_data = self.scan_all_regions()
        instances = all_data['instances']

        if not instances:
            return {
                "total_instances": 0,
                "by_state": {},
                "by_type": {},
                "by_region": {},
                "regions_with_instances": 0,
                "has_instances": False,
                "message": "No EC2 instances found in any region"
            }

        state_counts = {}
        for inst in instances:
            state = inst.get('State', {}).get('Name', 'unknown')
            state_counts[state] = state_counts.get(state, 0) + 1

        type_counts = {}
        for inst in instances:
            inst_type = inst.get('InstanceType', 'unknown')
            type_counts[inst_type] = type_counts.get(inst_type, 0) + 1

        region_counts = {}
        for inst in instances:
            region = inst.get('Region', 'unknown')
            region_counts[region] = region_counts.get(region, 0) + 1

        return {
            "total_instances": len(instances),
            "by_state": state_counts,
            "by_type": type_counts,
            "by_region": region_counts,
            "regions_with_instances": len([r for r, c in region_counts.items() if c > 0]),
            "has_instances": True
        }


