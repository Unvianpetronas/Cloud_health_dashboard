import numpy as np
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def analyze_performance(
        metrics: List[Dict[str, Any]],
        cpu_threshold: float = 75.0,
        memory_threshold: float = 75.0,
        latency_threshold: float = 200.0
) -> Dict[str, Any]:
    """
    Phân tích hiệu suất trung bình và phát hiện bottleneck nâng cao.
    Input: [{"cpu": 70, "memory": 80, "latency": 220}, ...]
    Output: {
        "avg_cpu": float, "avg_memory": float, "avg_latency": float,
        "cpu_std": float, "memory_std": float, "latency_std": float,
        "bottleneck": str, "recommendation": str
    }
    """
    if not metrics or not isinstance(metrics, list):
        logger.warning("Invalid or empty metrics input")
        return {
            "avg_cpu": 0.0, "avg_memory": 0.0, "avg_latency": 0.0,
            "cpu_std": 0.0, "memory_std": 0.0, "latency_std": 0.0,
            "bottleneck": "None", "recommendation": "No data available"
        }

    cpu_values, mem_values, lat_values = [], [], []

    for m in metrics:
        if not isinstance(m, dict):
            logger.warning(f"Invalid metric entry: {m}")
            continue
        try:
            cpu_values.append(float(m.get("cpu", 0)))
            mem_values.append(float(m.get("memory", 0)))
            lat_values.append(float(m.get("latency", 0)))
        except (ValueError, TypeError):
            logger.warning(f"Non-numeric values in metric: {m}")
            continue

    if not cpu_values or not mem_values or not lat_values:
        logger.info("No valid metrics data found")
        return {
            "avg_cpu": 0.0, "avg_memory": 0.0, "avg_latency": 0.0,
            "cpu_std": 0.0, "memory_std": 0.0, "latency_std": 0.0,
            "bottleneck": "None", "recommendation": "No data available"
        }

    avg_cpu, avg_mem, avg_lat = np.mean(cpu_values), np.mean(mem_values), np.mean(lat_values)
    cpu_std, mem_std, lat_std = np.std(cpu_values), np.std(mem_values), np.std(lat_values)

    overload_scores = {
        "CPU": (avg_cpu / cpu_threshold) if avg_cpu > cpu_threshold else 0,
        "Memory": (avg_mem / memory_threshold) if avg_mem > memory_threshold else 0,
        "Latency": (avg_lat / latency_threshold) if avg_lat > latency_threshold else 0,
    }

    bottleneck = max(overload_scores, key=overload_scores.get)
    bottleneck = bottleneck if overload_scores[bottleneck] > 0 else "None"

    recommendations = {
        "CPU": "Consider scaling up CPU or optimizing compute tasks",
        "Memory": "Optimize memory usage or increase RAM allocation",
        "Latency": "Check network or database performance",
        "None": "System performance is stable"
    }

    result = {
        "avg_cpu": round(avg_cpu, 2),
        "avg_memory": round(avg_mem, 2),
        "avg_latency": round(avg_lat, 2),
        "cpu_std": round(cpu_std, 2),
        "memory_std": round(mem_std, 2),
        "latency_std": round(lat_std, 2),
        "bottleneck": bottleneck,
        "recommendation": recommendations[bottleneck]
    }

    logger.info(
        f"Performance analysis completed: CPU={avg_cpu:.1f}%, MEM={avg_mem:.1f}%, LAT={avg_lat:.1f}ms → Bottleneck={bottleneck}"
    )
    return result
