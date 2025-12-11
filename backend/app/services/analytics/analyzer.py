"""
architecture_analyzer/analyzer.py
=================================
Main ArchitectureAnalyzer class with PreComputedData and recommendations.
"""

import logging
import statistics
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Set, Optional
from functools import lru_cache
from collections import defaultdict

from .pillars import PILLAR_CLASSES

logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTS
# ============================================================================

OLD_GEN_PREFIXES = frozenset([
    't1.', 't2.', 'm1.', 'm2.', 'm3.', 'm4.',
    'c1.', 'c3.', 'c4.', 'r3.', 'r4.', 'i2.', 'd2.', 'g2.'
])

SUSTAINABLE_REGIONS = frozenset([
    'eu-north-1', 'eu-west-1', 'us-west-2',
    'ca-central-1', 'eu-central-1', 'eu-west-3'
])

COST_ALLOCATION_TAGS = frozenset([
    'Environment', 'Project', 'Owner', 'CostCenter', 'Team', 'Application'
])

PRIORITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


# ============================================================================
# PRE-COMPUTED DATA
# ============================================================================

class PreComputedData:
    """
    Pre-computed data aggregations for O(n) single-pass processing.
    """

    __slots__ = (
        'ec2_count', 's3_count', 'tagged_instances_count', 'stopped_instances_count',
        'old_gen_instances_count', 'graviton_instances_count',
        'instances_without_detailed_monitoring', 'instances_without_imdsv2',
        'availability_zones', 'regions', 'instances_per_az',
        'public_buckets_count', 'unencrypted_buckets_count',
        'buckets_without_versioning', 'buckets_without_logging',
        'findings_by_severity',
        'unused_ebs_volumes_count', 'unencrypted_ebs_volumes_count',
        'instances_without_tags_for_cost_allocation',
    )

    def __init__(self):
        self.ec2_count: int = 0
        self.s3_count: int = 0
        self.tagged_instances_count: int = 0
        self.stopped_instances_count: int = 0
        self.old_gen_instances_count: int = 0
        self.graviton_instances_count: int = 0
        self.instances_without_detailed_monitoring: int = 0
        self.instances_without_imdsv2: int = 0
        self.availability_zones: Set[str] = set()
        self.regions: Set[str] = set()
        self.instances_per_az: Dict[str, int] = defaultdict(int)
        self.public_buckets_count: int = 0
        self.unencrypted_buckets_count: int = 0
        self.buckets_without_versioning: int = 0
        self.buckets_without_logging: int = 0
        self.findings_by_severity: Dict[str, List[Dict]] = defaultdict(list)
        self.unused_ebs_volumes_count: int = 0
        self.unencrypted_ebs_volumes_count: int = 0
        self.instances_without_tags_for_cost_allocation: int = 0

    @classmethod
    def from_raw_data(
            cls,
            ec2_data: List[Dict],
            s3_data: List[Dict],
            security_findings: List[Dict],
            ebs_data: Optional[List[Dict]] = None
    ) -> 'PreComputedData':
        """Single-pass O(n) data aggregation."""
        pc = cls()

        # Process EC2
        pc.ec2_count = len(ec2_data)
        instance_type_cache = {}

        for inst in ec2_data:
            # Tags
            tags = inst.get('tags', [])
            if tags:
                pc.tagged_instances_count += 1
                tag_keys = {t.get('Key', '') for t in tags if isinstance(t, dict)}
                if not tag_keys.intersection(COST_ALLOCATION_TAGS):
                    pc.instances_without_tags_for_cost_allocation += 1
            else:
                pc.instances_without_tags_for_cost_allocation += 1

            # State
            if inst.get('state') == 'stopped':
                pc.stopped_instances_count += 1

            # Instance type
            itype = inst.get('instance_type', '')
            if itype:
                if itype not in instance_type_cache:
                    is_old = any(itype.startswith(p) for p in OLD_GEN_PREFIXES)
                    instance_type_cache[itype] = is_old
                if instance_type_cache[itype]:
                    pc.old_gen_instances_count += 1

                # Graviton check
                family = itype.split('.')[0] if '.' in itype else itype
                if family.endswith('g') or family.endswith('gd'):
                    pc.graviton_instances_count += 1

            # Location
            az = inst.get('availability_zone')
            if az:
                pc.availability_zones.add(az)
                pc.instances_per_az[az] += 1

            region = inst.get('region')
            if region:
                pc.regions.add(region)

            # Security checks
            monitoring = inst.get('monitoring', {})
            if monitoring.get('state') != 'enabled':
                pc.instances_without_detailed_monitoring += 1

            metadata = inst.get('metadata_options', {})
            if metadata.get('http_tokens') != 'required':
                pc.instances_without_imdsv2 += 1

        # Process S3
        pc.s3_count = len(s3_data)
        for bucket in s3_data:
            if bucket.get('public_access'):
                pc.public_buckets_count += 1
            if not bucket.get('encryption_enabled'):
                pc.unencrypted_buckets_count += 1
            if not bucket.get('versioning_enabled'):
                pc.buckets_without_versioning += 1
            if not bucket.get('logging_enabled'):
                pc.buckets_without_logging += 1

        # Process security findings
        for finding in security_findings:
            severity = finding.get('severity', 'INFORMATIONAL')
            pc.findings_by_severity[severity].append(finding)

        # Process EBS (optional)
        if ebs_data:
            for vol in ebs_data:
                if not vol.get('attachments'):
                    pc.unused_ebs_volumes_count += 1
                if not vol.get('encrypted'):
                    pc.unencrypted_ebs_volumes_count += 1

        return pc

    def get_az_imbalance_ratio(self) -> float:
        """Calculate AZ distribution imbalance (0=balanced, 1=all in one AZ)."""
        if not self.instances_per_az:
            return 0.0
        counts = list(self.instances_per_az.values())
        if not counts or max(counts) == 0:
            return 0.0
        return (max(counts) - min(counts)) / max(counts)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

@lru_cache(maxsize=128)
def get_rating(score: float) -> str:
    """Convert score to rating."""
    if score >= 90:
        return "Excellent"
    elif score >= 80:
        return "Very Good"
    elif score >= 70:
        return "Good"
    elif score >= 60:
        return "Fair"
    elif score >= 50:
        return "Needs Improvement"
    return "Poor"



class ArchitectureAnalyzer:
    """
    AWS Architecture Analyzer - 6 Pillars Well-Architected Framework.

    Usage (unchanged):
        analyzer = ArchitectureAnalyzer(client_id="client-123")
        results = await analyzer.analyze_full_architecture(
            ec2_data=instances,
            s3_data=buckets,
            cost_data=costs,
            security_findings=findings,
            cloudwatch_metrics=metrics
        )
    """

    def __init__(self, client_id: str):
        self.client_id = client_id
        self.analysis_timestamp = datetime.utcnow()
        self._pc: Optional[PreComputedData] = None

    async def analyze_full_architecture(
            self,
            ec2_data: List[Dict],
            s3_data: List[Dict],
            cost_data: Dict,
            security_findings: List[Dict],
            cloudwatch_metrics: Dict,
            ebs_data: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Main analysis entry point."""

        # Pre-compute all aggregations
        self._pc = PreComputedData.from_raw_data(
            ec2_data, s3_data, security_findings, ebs_data
        )

        # Evaluate all 6 pillars
        well_architected = self._evaluate_well_architected()

        # Additional analysis
        cost_analysis = self._analyze_costs(cost_data)
        performance = self._analyze_performance(cloudwatch_metrics)
        security = self._analyze_security()
        reliability = self._analyze_reliability()
        sustainability = self._analyze_sustainability()

        # Generate recommendations
        recommendations = self._generate_recommendations(
            well_architected, cost_analysis, security, reliability
        )

        overall_score = round(well_architected['average_score'], 1)

        return {
            "client_id": self.client_id,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "overall_score": overall_score,
            "overall_rating": get_rating(overall_score),
            "well_architected": well_architected,
            "cost_analysis": cost_analysis,
            "performance": performance,
            "security": security,
            "reliability": reliability,
            "sustainability": sustainability,
            "recommendations": recommendations,
            "summary": self._generate_summary(
                overall_score, cost_analysis, security, recommendations
            )
        }

    def _evaluate_well_architected(self) -> Dict[str, Any]:
        """Evaluate all 6 pillars."""
        pillars_results = {}
        scores = []

        for name, pillar_class in PILLAR_CLASSES.items():
            pillar = pillar_class(self._pc)
            score = pillar.evaluate()
            pillars_results[name] = {
                "score": score,
                "rating": get_rating(score),
                "description": pillar.description
            }
            scores.append(score)

        return {
            "pillars": pillars_results,
            "average_score": statistics.mean(scores) if scores else 0
        }

    def _analyze_costs(self, cost_data: Dict) -> Dict[str, Any]:
        """Cost analysis."""
        total = cost_data.get('total_cost', 0)
        by_service = cost_data.get('by_service', {})

        # Top drivers
        sorted_services = sorted(by_service.items(), key=lambda x: x[1], reverse=True)[:5]

        # Potential savings
        ec2_cost = by_service.get('Amazon Elastic Compute Cloud - Compute', 0)
        savings = ec2_cost * 0.3 * 0.2  # Rightsizing
        if self._pc.ec2_count > 5:
            savings += ec2_cost * 0.3  # RI potential

        return {
            "total_monthly_cost": round(total, 2),
            "projected_annual_cost": round(total * 12, 2),
            "top_cost_drivers": [
                {"service": s, "cost": round(c, 2)} for s, c in sorted_services
            ],
            "potential_monthly_savings": round(savings, 2),
            "potential_annual_savings": round(savings * 12, 2)
        }

    def _analyze_performance(self, metrics: Dict) -> Dict[str, Any]:
        """Performance analysis."""
        cpu = metrics.get('CPUUtilization', {})
        datapoints = cpu.get('Datapoints', [])

        avg_cpu = 0.0
        if datapoints:
            values = [d.get('Average', 0) for d in datapoints]
            if values:
                avg_cpu = statistics.mean(values)

        issues = []
        if avg_cpu > 80:
            issues.append({"type": "high_cpu", "severity": "HIGH",
                           "message": f"Avg CPU {avg_cpu:.1f}%"})
        if self._pc.old_gen_instances_count > 0:
            issues.append({"type": "old_gen", "severity": "MEDIUM",
                           "message": f"{self._pc.old_gen_instances_count} old gen instances"})

        return {
            "avg_cpu_utilization": round(avg_cpu, 2),
            "total_instances": self._pc.ec2_count,
            "issues": issues
        }

    def _analyze_security(self) -> Dict[str, Any]:
        """Security analysis."""
        total_findings = sum(len(f) for f in self._pc.findings_by_severity.values())

        return {
            "total_findings": total_findings,
            "findings_by_severity": {s: len(f) for s, f in self._pc.findings_by_severity.items()},
            "vulnerabilities": {
                "public_s3_buckets": self._pc.public_buckets_count,
                "unencrypted_s3_buckets": self._pc.unencrypted_buckets_count,
                "unencrypted_ebs_volumes": self._pc.unencrypted_ebs_volumes_count
            }
        }

    def _analyze_reliability(self) -> Dict[str, Any]:
        """Reliability analysis."""
        multi_az = len(self._pc.availability_zones) >= 2
        multi_region = len(self._pc.regions) >= 2

        spofs = []
        if len(self._pc.regions) == 1 and self._pc.ec2_count > 0:
            spofs.append({"type": "single_region", "impact": "HIGH"})
        if not multi_az and self._pc.ec2_count > 0:
            spofs.append({"type": "single_az", "impact": "CRITICAL"})

        return {
            "multi_az_deployment": multi_az,
            "multi_region_deployment": multi_region,
            "availability_zones": list(self._pc.availability_zones),
            "regions": list(self._pc.regions),
            "instances_per_az": dict(self._pc.instances_per_az),
            "single_points_of_failure": spofs
        }

    def _analyze_sustainability(self) -> Dict[str, Any]:
        """Sustainability analysis."""
        graviton_pct = (self._pc.graviton_instances_count / self._pc.ec2_count * 100
                        if self._pc.ec2_count > 0 else 0)
        modern_pct = ((1 - self._pc.old_gen_instances_count / self._pc.ec2_count) * 100
                      if self._pc.ec2_count > 0 else 100)

        sustainable_regions = [r for r in self._pc.regions if r in SUSTAINABLE_REGIONS]

        return {
            "graviton_adoption": f"{graviton_pct:.1f}%",
            "modern_instance_ratio": f"{modern_pct:.1f}%",
            "sustainable_regions_used": sustainable_regions,
            "idle_resources": self._pc.stopped_instances_count
        }

    def _generate_recommendations(
            self,
            well_architected: Dict,
            cost_analysis: Dict,
            security: Dict,
            reliability: Dict
    ) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations."""
        recs = []
        pc = self._pc

        if pc.ec2_count == 0 and pc.s3_count == 0:
            recs.append({
                "priority": "HIGH",
                "category": "Getting Started",
                "title": "Deploy Your First Resources",
                "description": "No monitored resources found.",
                "pillar": "operational_excellence"
            })
            return recs

        # Security - Public S3
        if pc.public_buckets_count > 0:
            recs.append({
                "priority": "CRITICAL",
                "category": "Security",
                "title": "Block Public S3 Access",
                "description": f"{pc.public_buckets_count} public bucket(s) - data exposure risk",
                "pillar": "security"
            })

        # Security - Findings
        critical = len(pc.findings_by_severity.get('CRITICAL', []))
        high = len(pc.findings_by_severity.get('HIGH', []))
        if critical > 0 or high > 0:
            recs.append({
                "priority": "CRITICAL",
                "category": "Security",
                "title": "Address Security Findings",
                "description": f"{critical} critical, {high} high severity findings",
                "pillar": "security"
            })

        # Reliability - Single AZ
        if len(pc.availability_zones) < 2 and pc.ec2_count > 0:
            recs.append({
                "priority": "CRITICAL",
                "category": "Reliability",
                "title": "Enable Multi-AZ Deployment",
                "description": "Single AZ = critical SPOF",
                "pillar": "reliability"
            })

        # Security - Encryption
        if pc.unencrypted_buckets_count > 0:
            recs.append({
                "priority": "HIGH",
                "category": "Security",
                "title": "Enable S3 Encryption",
                "description": f"{pc.unencrypted_buckets_count} unencrypted bucket(s)",
                "pillar": "security"
            })

        # Cost
        savings = cost_analysis.get('potential_monthly_savings', 0)
        if savings > 50:
            recs.append({
                "priority": "HIGH",
                "category": "Cost Optimization",
                "title": "Implement Cost Savings",
                "description": f"Potential: ${savings:.2f}/month",
                "pillar": "cost_optimization",
                "potential_savings": savings
            })

        # Performance - Old gen
        if pc.old_gen_instances_count > 0:
            recs.append({
                "priority": "MEDIUM",
                "category": "Performance",
                "title": "Upgrade Old Gen Instances",
                "description": f"{pc.old_gen_instances_count} old generation instances",
                "pillar": "performance_efficiency"
            })

        # Sustainability - Graviton
        if pc.graviton_instances_count == 0 and pc.ec2_count > 0:
            recs.append({
                "priority": "MEDIUM",
                "category": "Sustainability",
                "title": "Adopt Graviton Instances",
                "description": "60% energy efficiency gain, 20% cost savings",
                "pillar": "sustainability"
            })

        # Operational - Tagging
        if pc.ec2_count > 0:
            ratio = pc.tagged_instances_count / pc.ec2_count
            if ratio < 0.8:
                recs.append({
                    "priority": "MEDIUM",
                    "category": "Operational Excellence",
                    "title": "Improve Resource Tagging",
                    "description": f"Only {ratio * 100:.0f}% tagged",
                    "pillar": "operational_excellence"
                })

        # Sort by priority
        recs.sort(key=lambda x: PRIORITY_ORDER.get(x.get('priority', 'LOW'), 99))
        return recs

    def _generate_summary(
            self,
            overall_score: float,
            cost_analysis: Dict,
            security: Dict,
            recommendations: List[Dict]
    ) -> str:
        """Generate executive summary."""
        rating = get_rating(overall_score)
        critical = sum(1 for r in recommendations if r.get('priority') == 'CRITICAL')

        parts = [f"Architecture health: {overall_score}/100 ({rating})."]

        if critical > 0:
            parts.append(f"️ {critical} CRITICAL issues require immediate action.")

        savings = cost_analysis.get('potential_monthly_savings', 0)
        if savings > 0:
            parts.append(f" ${savings:.2f}/month potential savings.")

        findings = security.get('total_findings', 0)
        if findings > 0:
            parts.append(f" {findings} security findings to review.")

        parts.append(f" {len(recommendations)} recommendations.")

        return " ".join(parts)
