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
        """
        Check nếu Cost Explorer chưa được enable trong account.
        DataUnavailableException có thể có nhiều nguyên nhân:
        - Cost Explorer chưa enable
        - Account mới, chưa có data
        - Đang trong quá trình ingest data (24-48 hours)
        """
        code = error.response.get("Error", {}).get("Code", "")
        message = error.response.get("Error", {}).get("Message", "")

        # Check error code
        if code in ["SubscriptionRequiredException", "DataUnavailableException"]:
            return True

        # Check message content
        if "not enabled" in message.lower() or "not ingested yet" in message.lower():
            return True

        return False

    def _get_not_enabled_response(self, operation: str) -> Dict:
        """Trả về response structure nhất quán khi Cost Explorer chưa enabled."""
        return {
            "enabled": False,
            "message": "Cost Explorer is not enabled or data is not available yet. "
                       "Please enable Cost Explorer in AWS Console and wait 24-48 hours for data ingestion.",
            "operation": operation,
            "recommendation": "To enable: AWS Console → Billing Dashboard → Cost Explorer → Enable Cost Explorer"
        }

    # --------- main methods ---------

    def get_total_cost(self, start_date: str, end_date: str, granularity: str = "MONTHLY") -> Dict:
        """
        Tổng chi phí trong khoảng thời gian.
        Không dùng retry decorator để có thể handle gracefully.
        """
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={"Start": start_date, "End": end_date},
                Granularity=granularity,
                Metrics=["UnblendedCost"]
            )
            # đảm bảo luôn có key expected
            response.setdefault("ResultsByTime", [])
            response["enabled"] = True
            return response

        except ClientError as e:
            if self._is_ce_not_enabled(e):
                logger.warning("Cost Explorer is not enabled or data unavailable (total cost).")
                return self._get_not_enabled_response("get_total_cost")

            logger.error(f"Fail to get total cost: {e}")
            raise

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
            response["enabled"] = True
            return response

        except ClientError as e:
            if self._is_ce_not_enabled(e):
                logger.warning("Cost Explorer is not enabled or data unavailable (by service).")
                return self._get_not_enabled_response("get_cost_by_service")

            logger.error(f"Fail to get cost by service: {e}")
            raise

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
            response["enabled"] = True
            return response

        except ClientError as e:
            if self._is_ce_not_enabled(e):
                logger.warning("Cost Explorer is not enabled or data unavailable (by account).")
                return self._get_not_enabled_response("get_cost_by_account")

            logger.error(f"Fail to get cost by account: {e}")
            raise

    def get_cost_forecast(self, days_ahead: int = 30, metric: str = "UNBLENDED_COST") -> Dict:
        """
        Dự báo chi phí cho X ngày tới.
        Requires at least 30 days of historical data.
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
            response["enabled"] = True
            return response

        except ClientError as e:
            if self._is_ce_not_enabled(e):
                logger.warning("Cost Explorer is not enabled or insufficient data for forecast.")
                response = self._get_not_enabled_response("get_cost_forecast")
                response["message"] += " (Forecast requires at least 30 days of historical data)"
                return response

            logger.error(f"Fail to get cost forecast: {e}")
            raise

    def get_rightsizing_recommendations(self, service: str = "AmazonEC2") -> Dict:
        """
        Gợi ý rightsizing cho service (mặc định: EC2).
        """
        try:
            response = self.client.get_rightsizing_recommendation(
                Service=service
            )
            response.setdefault("RightsizingRecommendations", [])
            response["enabled"] = True
            return response

        except ClientError as e:
            if self._is_ce_not_enabled(e):
                logger.warning("Cost Explorer is not enabled or data unavailable (rightsizing).")
                return self._get_not_enabled_response("get_rightsizing_recommendations")

            logger.error(f"Fail to get rightsizing recommendations: {e}")
            raise