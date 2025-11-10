from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.services.analytics.cost_optimizer import suggest_cost_optimization
from app.services.analytics.anomaly_detector import detect_anomalies
from app.services.analytics.performance_analyzer import analyze_performance
from app.services.analytics.well_architected import assess_well_architected

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# ======================
# 🧩 Request Models
# ======================

class CostOptimizationRequest(BaseModel):
    instances: List[Dict[str, Any]] = Field(
        ..., description="List of instance data for cost optimization"
    )

class AnomalyDetectionRequest(BaseModel):
    metrics: List[Dict[str, Any]] = Field(
        ..., description="List of metrics data for anomaly detection"
    )

class PerformanceRequest(BaseModel):
    metrics: List[Dict[str, Any]] = Field(
        ..., description="List of metrics data for performance analysis"
    )

class WellArchitectedRequest(BaseModel):
    pillars: Dict[str, Any] = Field(
        ..., description="Pillar scores for well-architected assessment"
    )

# ======================
# 🚀 API Endpoints
# ======================

@router.post("/cost-optimization")
def cost_optimization(request: CostOptimizationRequest):
    """Endpoint gợi ý giảm chi phí dựa trên usage và cost."""
    try:
        return suggest_cost_optimization(request.instances)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in cost optimization: {str(e)}")

@router.post("/anomaly-detection")
def anomaly_detection(request: AnomalyDetectionRequest):
    """Endpoint phát hiện bất thường dựa trên z-score."""
    try:
        return detect_anomalies(request.metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in anomaly detection: {str(e)}")

@router.post("/performance")
def performance(request: PerformanceRequest):
    """Endpoint phân tích hiệu suất và phát hiện bottleneck."""
    try:
        return analyze_performance(request.metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in performance analysis: {str(e)}")

@router.post("/well-architected")
def well_architected(request: WellArchitectedRequest):
    """Endpoint đánh giá hệ thống theo 5 trụ cột AWS Well-Architected."""
    try:
        return assess_well_architected(request.pillars)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in well-architected assessment: {str(e)}")
