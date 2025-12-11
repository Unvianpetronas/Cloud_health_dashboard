from .base import BasePillar


class OperationalExcellencePillar(BasePillar):
    name = "operational_excellence"
    description = "How well you run and monitor systems"

    def evaluate(self) -> float:
        pc = self._pc

        if pc.ec2_count == 0 and pc.s3_count == 0:
            return 50.0

        score = 100.0

        # Tagging coverage
        if pc.ec2_count > 0:
            ratio = pc.tagged_instances_count / pc.ec2_count
            if ratio < 0.3:
                score -= 30
            elif ratio < 0.5:
                score -= 20
            elif ratio < 0.8:
                score -= 10
            elif ratio < 0.95:
                score -= 5

        # Cost allocation tags
        if pc.ec2_count > 0:
            no_cost_tags = pc.instances_without_tags_for_cost_allocation / pc.ec2_count
            if no_cost_tags > 0.5:
                score -= 15
            elif no_cost_tags > 0.2:
                score -= 8

        # Multi-region
        if len(pc.regions) < 2:
            score -= 15

        # Detailed monitoring
        if pc.ec2_count > 0:
            no_mon = pc.instances_without_detailed_monitoring / pc.ec2_count
            if no_mon > 0.5:
                score -= 10
            elif no_mon > 0.2:
                score -= 5

        # Stopped instances (lifecycle management)
        if pc.ec2_count > 0:
            stopped = pc.stopped_instances_count / pc.ec2_count
            if stopped > 0.3:
                score -= 15
            elif stopped > 0.2:
                score -= 10
            elif stopped > 0.1:
                score -= 5

        return self.clamp(score)
