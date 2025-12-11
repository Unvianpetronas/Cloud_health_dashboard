from .base import BasePillar

class PerformancePillar(BasePillar):
    name = "performance"
    description = "Efficient use of computing resources"

    def evaluate(self) -> float:
        pc = self._pc
        score = 100.0

        if pc.old_gen_instances_count > 0:
            ratio = pc.old_gen_instances_count / pc.ec2_count
            if ratio > 1:
                score -= 40
            elif ratio > 0.5:
                score -= 25
            elif ratio > 0.25:
                score -= 15

        if pc.graviton_instances_count > 0:
            ratio = pc.graviton_instances_count / pc.ec2_count
            if ratio == 0:
                score -= 15
            elif ratio < 0.3 and pc.ec2_count >= 10:
                score -= 10

        if pc.instances_without_detailed_monitoring > 0:
            ratio = pc.instances_without_detailed_monitoring / pc.ec2_count
            if ratio > 0.5:
                score -= 10
            elif ratio > 0.2:
                score -= 5

        return self.clamp(score)
