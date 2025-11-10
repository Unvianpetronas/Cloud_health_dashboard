import logging
from typing import Any, Dict, List
from .cost_optimizer import suggest_cost_optimization  # Import hàm từ code cải tiến
from .anomaly_detector import detect_anomalies
from .performance_analyzer import analyze_performance
from .well_architected import assess_well_architected

# Optional: Import class nếu muốn OOP (từ code cũ/cải tiến)
try:
    from .performance_analyzer import PerformanceAnalyzer as PerfAnalyzerClass
    from .well_architected import WellArchitectedEvaluator as WAEvaluatorClass
    CLASSES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Optional classes not available: {e}")
    PerfAnalyzerClass = None
    WAEvaluatorClass = None
    CLASSES_AVAILABLE = False

logger = logging.getLogger(__name__)

# Wrapper class để aggregate tất cả services (dễ sử dụng trong router)
class AnalyticsService:
    """
    Aggregator cho tất cả analytics services.
    """
    def __init__(self) -> None:
        self.logger: logging.Logger = logger

    def cost_optimization(self, instances: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            return suggest_cost_optimization(instances)
        except Exception as e:
            self.logger.exception("Error in cost optimization")
            return {"error": str(e)}

    def anomaly_detection(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            return detect_anomalies(metrics)
        except Exception as e:
            self.logger.exception("Error in anomaly detection")
            return {"error": str(e)}

    def performance_analysis(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            return analyze_performance(metrics)
        except Exception as e:
            self.logger.exception("Error in performance analysis")
            return {"error": str(e)}

    def well_architected_assessment(self, pillars: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return assess_well_architected(pillars)
        except Exception as e:
            self.logger.exception("Error in well-architected assessment")
            return {"error": str(e)}

    # Optional: Methods cho class nếu available
    def get_performance_analyzer_class(self, metrics_df):
        if CLASSES_AVAILABLE:
            return PerfAnalyzerClass(metrics_df)
        else:
            raise ImportError("PerformanceAnalyzer class not available")

    def get_well_architected_evaluator_class(self, assessments):
        if CLASSES_AVAILABLE:
            return WAEvaluatorClass(assessments)
        else:
            raise ImportError("WellArchitectedEvaluator class not available")

# Instance global để dùng trong router
analytics_service = AnalyticsService()