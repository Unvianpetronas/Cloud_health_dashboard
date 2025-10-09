
class WellArchitectedEvaluator:
    def __init__(self, assessments):
        self.assessments = assessments

    def calculate_scores(self):
        """Aggregate scores for each AWS WAF pillar."""
        total = sum(self.assessments.values())
        scores = {pillar: (score / total) * 100 for pillar, score in self.assessments.items()}
        return scores

    def overall_rating(self):
        """Determine overall system rating."""
        avg_score = sum(self.assessments.values()) / len(self.assessments)
        if avg_score >= 80:
            return "Excellent"
        elif avg_score >= 60:
            return "Good"
        else:
            return "Needs Improvement"
