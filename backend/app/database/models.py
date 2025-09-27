
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from boto3.dynamodb.conditions import Key, Attr
import uuid
import logging


from dynamodb import DynamoDBConnection
from app.config import settings

logger = logging.getLogger(__name__)


class BaseModel:
    def __init__(self):
        self.db = DynamoDBConnection()


class MetricsModel(BaseModel):
    def __init__(self):
        super().__init__()
        self.table = self.db.get_table(settings.METRICS_TABLE)

    async def store_metric(self, service: str, metric_name: str, value: float,
                           timestamp: Optional[datetime] = None, unit: str = "Count",
                           dimensions: Optional[Dict] = None) -> bool:
        """Store a metric in DynamoDB"""
        try:
            if timestamp is None:
                timestamp = datetime.now()

            item = {
                'pk': f"{service}#{metric_name}",
                'sk': timestamp.isoformat(),
                'gsi1_pk': f"{metric_name}#{timestamp.isoformat()}",
                'value': float(value),
                'unit': unit,
                'service': service,
                'metric_name': metric_name,
                'dimensions': dimensions or {},
                'created_at': timestamp.isoformat(),
                'ttl': int((timestamp + timedelta(days=settings.METRICS_TTL_DAYS)).timestamp())
            }

            self.table.put_item(Item=item)
            logger.debug(f"Stored metric: {service}#{metric_name} = {value}")
            return True

        except Exception as e:
            logger.error(f"Error storing metric: {e}")
            return False

    async def get_metrics(self, service: str, metric_name: str,
                          start_time: datetime, end_time: datetime) -> List[Dict]:
        """Get metrics for a specific service and metric name"""
        try:
            response = self.table.query(
                KeyConditionExpression=Key('pk').eq(f"{service}#{metric_name}") &
                                       Key('sk').between(start_time.isoformat(),
                                                         end_time.isoformat()),
                ScanIndexForward=True
            )
            return response.get('Items', [])

        except Exception as e:
            logger.error(f"Error fetching metrics: {e}")
            return []

    async def get_latest_metrics(self, service: str, metric_name: str,
                                 limit: int = 10) -> List[Dict]:
        """Get latest metrics for a service/metric combination"""
        try:
            response = self.table.query(
                KeyConditionExpression=Key('pk').eq(f"{service}#{metric_name}"),
                ScanIndexForward=False,
                Limit=limit
            )
            return response.get('Items', [])

        except Exception as e:
            logger.error(f"Error fetching latest metrics: {e}")
            return []


class CostsModel(BaseModel):
    def __init__(self):
        super().__init__()
        self.table = self.db.get_table(settings.COSTS_TABLE)

    async def store_cost_data(self, service: str, date: str, cost: float,
                              usage_quantity: Optional[float] = None,
                              usage_unit: Optional[str] = None,
                              granularity: str = "DAILY") -> bool:
        """Store cost data in DynamoDB"""
        try:
            item = {
                'pk': service,
                'sk': f"{date}#{granularity}",
                'cost': float(cost),
                'date': date,
                'granularity': granularity,
                'currency': 'USD',
                'created_at': datetime.now().isoformat(),
                'ttl': int((datetime.now() + timedelta(days=settings.COSTS_TTL_DAYS)).timestamp())
            }

            if usage_quantity is not None:
                item['usage_quantity'] = usage_quantity
            if usage_unit:
                item['usage_unit'] = usage_unit

            self.table.put_item(Item=item)
            logger.debug(f"Stored cost data: {service} = ${cost}")
            return True

        except Exception as e:
            logger.error(f"Error storing cost data: {e}")
            return False

    async def get_cost_data(self, service: str, start_date: str,
                            end_date: str, granularity: str = "DAILY") -> List[Dict]:
        """Get cost data for a service within date range"""
        try:
            response = self.table.query(
                KeyConditionExpression=Key('pk').eq(service) &
                                       Key('sk').between(f"{start_date}#{granularity}",
                                                         f"{end_date}#{granularity}"),
                ScanIndexForward=True
            )
            return response.get('Items', [])

        except Exception as e:
            logger.error(f"Error fetching cost data: {e}")
            return []


class SecurityFindingModel(BaseModel):
    def __init__(self):
        super().__init__()
        self.table = self.db.get_table(settings.SECURITY_TABLE)

    async def store_finding(self, finding_type: str, finding_id: str,
                            severity: str, status: str, title: str,
                            description: str, service: str,
                            resource_id: Optional[str] = None) -> bool:
        """Store security finding"""
        try:
            item = {
                'pk': finding_type,
                'sk': finding_id,
                'severity': severity,
                'status': status,
                'title': title,
                'description': description,
                'service': service,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            if resource_id:
                item['resource_id'] = resource_id

            self.table.put_item(Item=item)
            logger.debug(f"Stored security finding: {finding_type}#{finding_id}")
            return True

        except Exception as e:
            logger.error(f"Error storing security finding: {e}")
            return False

    async def get_findings_by_type(self, finding_type: str) -> List[Dict]:

        try:
            response = self.table.query(
                KeyConditionExpression=Key('pk').eq(finding_type)
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error fetching findings: {e}")
            return []

class RecommendationModel(BaseModel):
    def __init__(self):
        super().__init__()
        self.table = self.db.get_table(settings.RECOMMENDATIONS_TABLE)

    async def store_recommendation(self, rec_type: str, title: str, description: str,
                                   impact: str, effort: str, confidence: float,
                                   service: str, estimated_savings: Optional[float] = None,
                                   resource_id: Optional[str] = None) -> Optional[str]:
        """Store recommendation and return its ID"""
        try:
            timestamp = datetime.now()
            rec_id = f"rec-{uuid.uuid4().hex[:8]}"

            item = {
                'pk': rec_type,
                'sk': f"{timestamp.isoformat()}#{rec_id}",
                'id': rec_id,
                'title': title,
                'description': description,
                'impact': impact,
                'effort': effort,
                'confidence': confidence,
                'service': service,
                'implemented': False,
                'created_at': timestamp.isoformat(),
                'updated_at': timestamp.isoformat()
            }

            if estimated_savings is not None:
                item['estimated_savings'] = estimated_savings
            if resource_id:
                item['resource_id'] = resource_id

            self.table.put_item(Item=item)
            logger.debug(f"Stored recommendation: {rec_type}#{rec_id}")
            return rec_id

        except Exception as e:
            logger.error(f"Error storing recommendation: {e}")
            return None

    async def get_recommendations_by_type(self, rec_type: str) -> List[Dict]:
        try:
            response = self.table.query(
                KeyConditionExpression=Key('pk').eq(rec_type),
                ScanIndexForward=False  # Latest first
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error fetching recommendations: {e}")
            return []