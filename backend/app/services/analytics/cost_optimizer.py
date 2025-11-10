import numpy as np
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def suggest_cost_optimization(
        instances: List[Dict[str, Any]],
        low_usage_threshold: float = 0.5,
        min_cost_threshold: float = 50.0,
        saving_rate: float = 0.3
) -> Dict[str, Any]:
    """
    Gợi ý tối ưu chi phí dựa trên usage và cost.
    Input: [{"id": "i-123", "usage": 0.3, "cost": 100}, ...]
    Output: {
        "recommendations": [...],
        "total_saving": float,
        "confidence_score": float,
        "saving_percent": float
    }
    """
    if not instances or not isinstance(instances, list):
        logger.warning("Invalid or empty instances input")
        return {"recommendations": [], "total_saving": 0.0, "confidence_score": 0.0}

    recommendations = []
    for inst in instances:
        try:
            usage = float(inst.get("usage", 0))
            cost = float(inst.get("cost", 0))
            inst_id = inst.get("id", "unknown")

            if usage < low_usage_threshold and cost > min_cost_threshold:
                # Chọn hành động phù hợp
                if usage < 0.2:
                    action = "Stop or terminate unused instance"
                else:
                    action = "Downsize instance type"

                saving = round(cost * saving_rate, 2)
                recommendations.append({
                    "instance_id": inst_id,
                    "current_cost": cost,
                    "usage": usage,
                    "suggested_action": action,
                    "expected_saving": saving
                })
        except (ValueError, TypeError):
            logger.warning(f"Invalid data in instance: {inst}")
            continue

    total_saving = sum(r["expected_saving"] for r in recommendations)
    total_cost = sum(float(inst.get("cost", 0)) for inst in instances)
    saving_percent = round((total_saving / total_cost) * 100, 2) if total_cost > 0 else 0

    # Confidence score heuristic
    confidence_score = (
        round(min(0.95, 0.7 + (len(recommendations) / max(len(instances), 1)) * 0.25), 2)
        if recommendations else 0.0
    )

    result = {
        "recommendations": recommendations,
        "total_saving": round(total_saving, 2),
        "saving_percent": saving_percent,
        "confidence_score": confidence_score,
        "num_instances": len(instances),
        "optimized_instances": len(recommendations),
        "optimization_ratio": round(len(recommendations) / len(instances), 2) if instances else 0.0
    }

    logger.info(
        f"Cost optimization completed: {len(recommendations)} recommendations "
        f"({saving_percent}% saving potential)"
    )
    return result
