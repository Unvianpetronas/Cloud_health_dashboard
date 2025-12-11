from .base import BasePillar


class CostOptimizationPillar(BasePillar):
    name = "cost_optimization"
    description = "Avoiding unnecessary costs"

    def evaluate(self) -> float:
        pc = self._pc

        if pc.ec2_count == 0 and pc.s3_count == 0:
            return 50.0

        score = 100.0

        # Stopped instances
        if pc.ec2_count > 0:
            stopped = pc.stopped_instances_count / pc.ec2_count
            if stopped > 0.3:
                score -= 25
            elif stopped > 0.2:
                score -= 15
            elif stopped > 0.1:
                score -= 10
            elif stopped > 0:
                score -= 5

        # Reserved Instances / Savings Plans (assume none)
        if pc.ec2_count >= 10:
            score -= 20
        elif pc.ec2_count >= 5:
            score -= 10

        # Unused EBS volumes
        score -= min(pc.unused_ebs_volumes_count * 5, 20)

        # Cost allocation tags
        if pc.ec2_count > 0:
            no_tags = pc.instances_without_tags_for_cost_allocation / pc.ec2_count
            if no_tags > 0.5:
                score -= 10
            elif no_tags > 0.2:
                score -= 5

        # Old gen cost inefficiency
        if pc.ec2_count > 0 and pc.old_gen_instances_count > 0:
            if pc.old_gen_instances_count / pc.ec2_count > 0.3:
                score -= 10

        return self.clamp(score)
