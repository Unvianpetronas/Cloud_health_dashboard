import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def assess_well_architected(
        pillars: Dict[str, Any],
        normalize_scores: bool = False,
        weights: Dict[str, float] = None
) -> Dict[str, Any]:
    """
    Đánh giá theo 5 trụ cột AWS WAF (Operational, Security, Reliability, Performance, Cost).
    Input:
        pillars: {"operational": 80, "security": 70, "reliability": 60, "performance": 75, "cost": 85}
        normalize_scores: True để normalize thành %
        weights: dict trọng số (vd: {"security": 1.5, "cost": 1.0})
    """
    if not pillars or not isinstance(pillars, dict):
        logger.warning("Invalid or empty pillars input")
        return {
            "total_score": 0.0, "status": "Needs Improvement",
            "risk_level": "High Risk", "pillar_breakdown": {}, "recommendations": {}
        }

    valid_pillars = {}
    for pillar, score in pillars.items():
        try:
            score_val = float(score)
            if 0 <= score_val <= 100:
                valid_pillars[pillar] = score_val
            else:
                logger.warning(f"Score out of range for pillar {pillar}: {score}")
        except (ValueError, TypeError):
            logger.warning(f"Non-numeric score for pillar {pillar}: {score}")
            continue

    if not valid_pillars:
        logger.info("No valid pillar scores")
        return {
            "total_score": 0.0, "status": "Needs Improvement",
            "risk_level": "High Risk", "pillar_breakdown": {}, "recommendations": {}
        }

    weights = weights or {p: 1.0 for p in valid_pillars}
    weighted_scores = [valid_pillars[p] * weights.get(p, 1.0) for p in valid_pillars]
    total_score = sum(weighted_scores) / sum(weights.values())

    # Status & Risk logic
    status = (
        "Excellent" if total_score >= 80 else
        "Good" if total_score >= 65 else
        "Needs Improvement"
    )
    risk_level = (
        "Low Risk" if total_score >= 80 else
        "Moderate Risk" if total_score >= 65 else
        "High Risk"
    )

    # Optional normalization
    pillar_breakdown = valid_pillars
    if normalize_scores:
        total = sum(valid_pillars.values())
        if total > 0:
            pillar_breakdown = {p: round((v / total) * 100, 2) for p, v in valid_pillars.items()}
        else:
            logger.warning("Total score is zero, cannot normalize")

    # Recommendations
    recommendations = {
        "operational": "Automate deployments, improve observability with CloudWatch",
        "security": "Enable IAM least privilege and encryption at rest",
        "reliability": "Add redundancy and test recovery processes",
        "performance": "Use caching and right-size instances",
        "cost": "Review usage and apply savings plans"
    }

    result = {
        "total_score": round(total_score, 2),
        "status": status,
        "risk_level": risk_level,
        "pillar_breakdown": pillar_breakdown,
        "recommendations": {p: recommendations.get(p, "N/A") for p in valid_pillars}
    }

    logger.info(f"Well-architected assessment: total={total_score:.2f}, status={status}, risk={risk_level}")
    return result


class WellArchitectedEvaluator:
    """Wrapper class cho dễ mở rộng, dùng trong analytics service."""
    def __init__(self, assessments: Dict[str, Any]):
        self.assessments = assessments if isinstance(assessments, dict) else {}

    def calculate_scores(self):
        return assess_well_architected(self.assessments, normalize_scores=True)["pillar_breakdown"]

    def overall_rating(self):
        return assess_well_architected(self.assessments)["status"]

    def full_report(self):
        return assess_well_architected(self.assessments, normalize_scores=True)
