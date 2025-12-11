from .base import BasePillar

class SecurityPillar(BasePillar):
    name = "security"
    description = "How well you protect your systems and data"

    SEVERITY_WEIGHTS = {
        'CRITICAL': 20,
        'HIGH': 10,
        'MEDIUM': 5,
        'LOW': 2,
        'INFORMATIONAL': 1,
        'UNDEFINED': 1
    }
    def evaluate(self) -> float:
        pc = self._pc

        if pc.ec2_count == 0 and pc.s3_count == 0 and not pc.findings_by_severity :
            return 50.0

        score = 100.0

        for severity, findings in pc.findings_by_severity.items():
            score -= self.SEVERITY_WEIGHTS.get(severity, 0) * len(findings)

        # EC2 without imdsv2
        if pc.ec2_count > 0:
            ratio = pc.instances_without_imdsv2/ pc.ec2_count
            if ratio > 0.5:
                score -= 15
            elif ratio > 0.2:
                score -= 10


        # Public buckets
        if pc.public_buckets_count > 0:
            score -= pc.public_buckets_count * 15

        # Unencrypted buckets
        if pc.unencrypted_buckets_count > 0:
            score -= pc.unencrypted_buckets_count * 8

        # Unencrypted EBS
        if pc.unencrypted_ebs_volumes_count > 0:
            score -= pc.unencrypted_ebs_volumes_count *5

        # S3 versioning
        score -= min(pc.buckets_without_versioning * 3, 15)

        score -= min(pc.buckets_without_logging * 2, 10)


        return self.clamp(score)
