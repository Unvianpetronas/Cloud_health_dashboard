from typing import Dict, List
from datetime import datetime, timedelta, UTC
from .client import AWSClientProvider


class CostExplorerScanner:
    """
    Wrapper cho AWS Cost Explorer.
    Cho phép query cost theo service, account, forecast và rightsizing recommendations.
    """

    def __init__(self, client_provider: AWSClientProvider):
        self.client = client_provider.get_client("ce")

    def get_total_cost(self, start_date: str, end_date: str, granularity: str = "MONTHLY") -> Dict:
        """
        Tổng chi phí trong khoảng thời gian.
        """
        response = self.client.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity=granularity,
            Metrics=["UnblendedCost"]
        )
        return response

    def get_cost_by_service(self, start_date: str, end_date: str, granularity: str = "MONTHLY") -> Dict:
        """
        Chi phí theo từng service (DynamoDB, EC2, S3, CloudWatch, v.v...).
        """
        response = self.client.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity=granularity,
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}]
        )
        return response

    def get_cost_by_account(self, start_date: str, end_date: str, granularity: str = "MONTHLY") -> Dict:
        """
        Chi phí theo từng AWS account.
        """
        response = self.client.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity=granularity,
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}]
        )
        return response

    def get_cost_forecast(self, days_ahead: int = 30, metric: str = "UNBLENDED_COST") -> Dict:
        """
        Dự báo chi phí cho X ngày tới.
        """
        start = datetime.now(UTC).date().isoformat()
        end = (datetime.now(UTC) + timedelta(days=days_ahead)).date().isoformat()

        response = self.client.get_cost_forecast(
            TimePeriod={"Start": start, "End": end},
            Granularity="DAILY",
            Metric=metric
        )
        return response

    def get_rightsizing_recommendations(self, service: str = "AmazonEC2") -> Dict:
        """
        Gợi ý rightsizing cho service (mặc định: EC2).
        """
        response = self.client.get_rightsizing_recommendation(
            Service=service
        )
        return response
