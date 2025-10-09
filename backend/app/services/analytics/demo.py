import pandas as pd
from backend.app.services.analytics import (
    CostOptimizer,
    AnomalyDetector,
    PerformanceAnalyzer,
    WellArchitectedEvaluator,
)

# Fake data
usage_data = pd.DataFrame([
    {"id": "vm-1", "cpu_utilization": 15},
    {"id": "vm-2", "cpu_utilization": 70},
    {"id": "vm-3", "cpu_utilization": 10},
])

metric_data = pd.DataFrame([
    {"timestamp": "2025-10-09", "value": 45},
    {"timestamp": "2025-10-09", "value": 90},
    {"timestamp": "2025-10-09", "value": 30},
])

perf_metrics = pd.DataFrame([
    {"service": "api", "latency": 150, "cpu_usage": 70, "memory_usage": 40},
    {"service": "db", "latency": 300, "cpu_usage": 85, "memory_usage": 60},
])

# Run modules
print("=== COST OPTIMIZER ===")
print(CostOptimizer(usage_data).suggest_rightsizing())

print("\n=== ANOMALY DETECTOR ===")
print(AnomalyDetector(metric_data).detect_anomalies())

print("\n=== PERFORMANCE ANALYZER ===")
print(PerformanceAnalyzer(perf_metrics).performance_summary())

print("\n=== WELL-ARCHITECTED EVALUATOR ===")
assessments = {"Operational Excellence": 85, "Security": 90, "Reliability": 75, "Performance Efficiency": 80, "Cost Optimization": 88}
print(WellArchitectedEvaluator(assessments).calculate_scores())
print("Overall:", WellArchitectedEvaluator(assessments).overall_rating())
