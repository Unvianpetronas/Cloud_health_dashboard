from .base import BasePillar


class ReliabilityPillar(BasePillar):
    name = "reliability"
    description = "Recovery and mitigation capabilities"

    def evaluate(self) -> float:
        pc = self._pc

        if pc.ec2_count == 0:
            return 50.0

        score = 100.0

        # AZ Distribution - KEY FIX: Check actual distribution
        az_count = len(pc.availability_zones)

        if az_count < 2:
            score -= 35  # CRITICAL: Single AZ = complete SPOF
        else:
            # Check if instances are ACTUALLY distributed
            imbalance = pc.get_az_imbalance_ratio()

            if az_count == 2:
                if imbalance > 0.7:
                    score -= 25  # e.g., 90-10 split = NOT fault tolerant
                elif imbalance > 0.5:
                    score -= 15  # Moderately uneven
                else:
                    score -= 10  # 2 AZs but OK (best practice is 3)
            elif az_count >= 3:
                if imbalance > 0.6:
                    score -= 10  # Poor utilization of 3+ AZs

        # Multi-region (DR)
        if len(pc.regions) < 2:
            score -= 20

        # Backup indicators (S3 versioning)
        if pc.s3_count > 0:
            versioning_ratio = 1 - (pc.buckets_without_versioning / pc.s3_count)
            if versioning_ratio < 0.5:
                score -= 10
            elif versioning_ratio < 0.8:
                score -= 5

        # Backup gap placeholder
        score -= 5

        return self.clamp(score)
