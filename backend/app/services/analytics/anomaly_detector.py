import numpy as np
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def detect_anomalies(metrics: List[Dict[str, Any]], threshold: float = 2.0) -> Dict[str, Any]:
    """
    Detect anomalies in cost metrics using Z-score.
    Args:
        metrics: List of dicts with at least {"timestamp": str, "cost": float}
        threshold: Z-score threshold for anomaly detection (default=2.0)
    Returns:
        dict: Summary with mean, std_dev, anomalies list, and alert flag
    """
    if not metrics or not isinstance(metrics, list):
        logger.warning("Invalid or empty metrics input")
        return {"mean_cost": 0.0, "std_dev": 0.0, "anomalies": [], "alert": False}

    valid_costs = []
    for m in metrics:
        try:
            valid_costs.append(float(m["cost"]))
        except (KeyError, ValueError, TypeError):
            logger.debug(f"Skipping invalid metric: {m}")
            continue

    if not valid_costs:
        logger.info("No valid cost data found")
        return {"mean_cost": 0.0, "std_dev": 0.0, "anomalies": [], "alert": False}

    costs = np.array(valid_costs)
    mean, std = np.mean(costs), np.std(costs)

    if std == 0:
        logger.warning("Standard deviation is zero — all costs identical.")
        std = 1  # Prevent division by zero

    anomalies = [
        {
            "timestamp": m.get("timestamp", "unknown"),
            "cost": float(m["cost"]),
            "z_score": round((float(m["cost"]) - mean) / std, 2)
        }
        for m in metrics
        if "cost" in m and abs((float(m["cost"]) - mean) / std) > threshold
    ]

    result = {
        "mean_cost": round(mean, 2),
        "std_dev": round(std, 2),
        "max_cost": round(np.max(costs), 2),
        "min_cost": round(np.min(costs), 2),
        "anomalies": anomalies,
        "alert": bool(anomalies)
    }

    logger.info(f"Anomaly detection complete: {len(anomalies)} anomalies found out of {len(metrics)} records.")
    return result
