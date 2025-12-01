from typing import Dict
from datetime import datetime, timedelta, UTC
from botocore.exceptions import ClientError

from .client import AWSClientProvider
from .base_scanner import BaseAWSScanner

import logging

logger = logging.getLogger(__name__)


class CostExplorerScanner(BaseAWSScanner):
    """
    Wrapper cho AWS Cost Explorer.
    Cho phép query cost theo service, account, forecast và rightsizing recommendations.
    """

    def __init__(self, client_provider: AWSClientProvider):
        # Cost Explorer là service global (không theo region)
        self.client = client_provider.get_client("ce")

    # --------- helpers ---------

    def _is_ce_not_enabled(self, error: ClientError) -> bool:
        """Check nếu Cost Explorer chưa được enable trong account."""
        code = error.response.get("Error", {}).get("Code", "")
        return code == "SubscriptionRequiredException"

    # --------- main methods ---------

    @BaseAWSScanner.with_retry()
    def get_total_cost(self, start_date: str, end_date: str, granularity: str = "MONTHLY") -> Dict:
        """
        Tổng chi phí trong khoảng thời gian.
        """
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={"Start": start_date, "End": end_date},
                Granularity=granularity,
                Metrics=["UnblendedCost"]
            )
            # đảm bảo luôn có key expected
            response.setdefault("ResultsByTime", [])
            return response

        except ClientError as e:
            if self._is_ce_not_enabled(e):
                logger.warning("Cost Explorer is not enabled for this account (total cost).")
                # giống style GuardDuty: trả về cấu trúc rỗng + message
                return {
                    "ResultsByTime": [],
                    "message": "Cost Explorer is not enabled for this account."
                }

            logger.error(f"Fail to get total cost: {e}")
            raise

    @BaseAWSScanner.with_retry()
    def get_cost_by_service(self, start_date: str, end_date: str, granularity: str = "MONTHLY") -> Dict:
        """
        Chi phí theo từng service (DynamoDB, EC2, S3, CloudWatch, v.v...).
        """
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={"Start": start_date, "End": end_date},
                Granularity=granularity,
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}]
            )
            response.setdefault("ResultsByTime", [])
            response.setdefault("GroupDefinitions", [{"Type": "DIMENSION", "Key": "SERVICE"}])
            return response

        except ClientError as e:
            if self._is_ce_not_enabled(e):
                logger.warning("Cost Explorer is not enabled for this account (by service).")
                return {
                    "ResultsByTime": [],
                    "GroupDefinitions": [{"Type": "DIMENSION", "Key": "SERVICE"}],
                    "message": "Cost Explorer is not enabled for this account."
                }

            logger.error(f"Fail to get cost by service: {e}")
            raise

    @BaseAWSScanner.with_retry()
    def get_cost_by_account(self, start_date: str, end_date: str, granularity: str = "MONTHLY") -> Dict:
        """
        Chi phí theo từng AWS account.
        """
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={"Start": start_date, "End": end_date},
                Granularity=granularity,
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}]
            )
            response.setdefault("ResultsByTime", [])
            response.setdefault("GroupDefinitions", [{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}])
            return response

        except ClientError as e:
            if self._is_ce_not_enabled(e):
                logger.warning("Cost Explorer is not enabled for this account (by account).")
                return {
                    "ResultsByTime": [],
                    "GroupDefinitions": [{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}],
                    "message": "Cost Explorer is not enabled for this account."
                }

            logger.error(f"Fail to get cost by account: {e}")
            raise

    @BaseAWSScanner.with_retry()
    def get_cost_forecast(self, days_ahead: int = 30, metric: str = "UNBLENDED_COST") -> Dict:
        """
        Dự báo chi phí cho X ngày tới.
        """
        try:
            start = datetime.now(UTC).date().isoformat()
            end = (datetime.now(UTC) + timedelta(days=days_ahead)).date().isoformat()

            response = self.client.get_cost_forecast(
                TimePeriod={"Start": start, "End": end},
                Granularity="DAILY",
                Metric=metric
            )
            response.setdefault("ForecastResultsByTime", [])
            return response

        except ClientError as e:
            if self._is_ce_not_enabled(e):
                logger.warning("Cost Explorer is not enabled for this account (forecast).")
                return {
                    "ForecastResultsByTime": [],
                    "message": "Cost Explorer is not enabled for this account."
                }

            logger.error(f"Fail to get cost forecast: {e}")
            raise

    @BaseAWSScanner.with_retry()
    def get_rightsizing_recommendations(self, service: str = "AmazonEC2") -> Dict:
        """
        Gợi ý rightsizing cho service (mặc định: EC2).
        """
        try:
            response = self.client.get_rightsizing_recommendation(
                Service=service
            )
            response.setdefault("RightsizingRecommendations", [])
            return response

        except ClientError as e:
            if self._is_ce_not_enabled(e):
                logger.warning("Cost Explorer is not enabled for this account (rightsizing).")
                return {
                    "RightsizingRecommendations": [],
                    "message": "Cost Explorer is not enabled for this account."
                }

            logger.error(f"Fail to get rightsizing recommendations: {e}")
            raise