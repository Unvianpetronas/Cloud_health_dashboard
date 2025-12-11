"""
Pillar 6: Sustainability (Added 2021)
Focus: Minimizing environmental impact.
"""

from .base import BasePillar

SUSTAINABLE_REGIONS = frozenset([
    'eu-north-1',  # Stockholm - 100% renewable
    'eu-west-1',  # Ireland - wind
    'us-west-2',  # Oregon - hydro
    'ca-central-1',  # Canada - hydro
    'eu-central-1',  # Frankfurt
    'eu-west-3',  # Paris - nuclear
])


class SustainabilityPillar(BasePillar):
    name = "sustainability"
    description = "Minimizing environmental impact"

    def evaluate(self) -> float:
        pc = self._pc

        if pc.ec2_count == 0:
            return 50.0

        score = 100.0

        # Graviton adoption (60% more energy efficient)
        graviton_ratio = pc.graviton_instances_count / pc.ec2_count
        if graviton_ratio == 0:
            score -= 20
        elif graviton_ratio < 0.3:
            score -= 15
        elif graviton_ratio < 0.5:
            score -= 10

        # Instance generation
        if pc.old_gen_instances_count > 0:
            old_ratio = pc.old_gen_instances_count / pc.ec2_count
            if old_ratio >= 1.0:
                score -= 20
            elif old_ratio > 0.5:
                score -= 15
            elif old_ratio > 0.2:
                score -= 10

        # Sustainable region selection
        sustainable_used = any(r in SUSTAINABLE_REGIONS for r in pc.regions)
        if not sustainable_used:
            score -= 15

        # Resource utilization (idle)
        stopped = pc.stopped_instances_count / pc.ec2_count
        if stopped > 0.3:
            score -= 10
        elif stopped > 0.2:
            score -= 5

        # AZ for scaling efficiency
        if len(pc.availability_zones) < 2:
            score -= 10

        # Unused storage
        score -= min(pc.unused_ebs_volumes_count * 2, 10)

        return self.clamp(score)
