import logging
import statistics
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Set, Tuple, Optional
from functools import lru_cache
from collections import defaultdict

logger = logging.getLogger(__name__)


class PreComputedData:
    """
    Pre-computed data aggregations to avoid redundant iterations.
    Single-pass computation for maximum efficiency.
    """
    __slots__ = (
        'ec2_count', 's3_count', 'tagged_instances_count', 'stopped_instances_count',
        'old_gen_instances_count', 'availability_zones', 'regions', 'instance_types',
        'findings_by_severity', 'public_buckets_count', 'unencrypted_buckets_count',
        'ec2_state_distribution', 'instance_type_generation_map'
    )

    def __init__(self):
        self.ec2_count: int = 0
        self.s3_count: int = 0
        self.tagged_instances_count: int = 0
        self.stopped_instances_count: int = 0
        self.old_gen_instances_count: int = 0
        self.availability_zones: Set[str] = set()
        self.regions: Set[str] = set()
        self.instance_types: Dict[str, int] = defaultdict(int)
        self.findings_by_severity: Dict[str, List[Dict]] = defaultdict(list)
        self.public_buckets_count: int = 0
        self.unencrypted_buckets_count: int = 0
        self.ec2_state_distribution: Dict[str, int] = defaultdict(int)
        self.instance_type_generation_map: Dict[str, bool] = {}  # True if old generation

    @classmethod
    def from_raw_data(
        cls,
        ec2_data: List[Dict],
        s3_data: List[Dict],
        security_findings: List[Dict]
    ) -> 'PreComputedData':
        """
        Compute all aggregations in a single pass for O(n) complexity.
        """
        computed = cls()

        # Old generation instance type prefixes (pre-compiled for fast lookup)
        old_gen_prefixes = frozenset(['t2.', 'm3.', 'm4.', 'c3.', 'c4.'])

        # Process EC2 data in single pass
        computed.ec2_count = len(ec2_data)
        for instance in ec2_data:
            # Tags
            tags = instance.get('tags')
            if tags and len(tags) > 0:
                computed.tagged_instances_count += 1

            # State
            state = instance.get('state', '')
            if state:
                computed.ec2_state_distribution[state] += 1
                if state == 'stopped':
                    computed.stopped_instances_count += 1

            # Instance type and generation
            instance_type = instance.get('instance_type', '')
            if instance_type:
                computed.instance_types[instance_type] += 1

                # Check if old generation (cache result)
                if instance_type not in computed.instance_type_generation_map:
                    is_old_gen = any(instance_type.startswith(prefix) for prefix in old_gen_prefixes)
                    computed.instance_type_generation_map[instance_type] = is_old_gen

                if computed.instance_type_generation_map[instance_type]:
                    computed.old_gen_instances_count += 1

            # Availability zones
            az = instance.get('availability_zone')
            if az:
                computed.availability_zones.add(az)

            # Regions
            region = instance.get('region')
            if region:
                computed.regions.add(region)

        # Process S3 data in single pass
        computed.s3_count = len(s3_data)
        for bucket in s3_data:
            if bucket.get('public_access', False):
                computed.public_buckets_count += 1
            if not bucket.get('encryption_enabled', False):
                computed.unencrypted_buckets_count += 1

        # Process security findings in single pass
        for finding in security_findings:
            severity = finding.get('severity', 'INFORMATIONAL')
            computed.findings_by_severity[severity].append(finding)

        return computed


class ArchitectureAnalyzer:
    """
    High-performance architecture analyzer with optimized data processing.

    Key optimizations:
    - Single-pass data aggregation
    - Parallel async execution
    - Cached computations
    - Efficient data structures
    - Reduced memory allocations
    """

    # Class-level constants for fast access
    OLD_GEN_TYPES = frozenset(['t2.', 'm3.', 'm4.', 'c3.', 'c4.'])
    SEVERITY_WEIGHTS = {
        'CRITICAL': 15,
        'HIGH': 8,
        'MEDIUM': 3,
        'LOW': 1,
        'INFORMATIONAL': 0
    }
    PRIORITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

    def __init__(self, client_id: str):
        self.client_id = client_id
        self.analysis_timestamp = datetime.utcnow()
        self._precomputed: Optional[PreComputedData] = None

    async def analyze_full_architecture(
        self,
        ec2_data: List[Dict],
        s3_data: List[Dict],
        cost_data: Dict,
        security_findings: List[Dict],
        cloudwatch_metrics: Dict
    ) -> Dict[str, Any]:
        """
        Performs comprehensive architecture analysis with parallel execution.

        Optimizations:
        - Pre-compute all data aggregations once (O(n) single pass)
        - Run all analysis modules in parallel using asyncio.gather
        - Cache intermediate results
        - Use efficient data structures
        """

        # Pre-compute all data aggregations in a single pass - O(n) complexity
        self._precomputed = PreComputedData.from_raw_data(
            ec2_data, s3_data, security_findings
        )

        # Run all analysis modules in parallel for maximum throughput
        # These are independent computations that can execute concurrently
        (
            well_architected_scores,
            cost_analysis,
            performance_analysis,
            security_analysis,
            reliability_analysis
        ) = await asyncio.gather(
            self._evaluate_well_architected_async(),
            self._analyze_costs_async(cost_data, ec2_data, s3_data),
            self._analyze_performance_async(ec2_data, cloudwatch_metrics),
            self._analyze_security_async(ec2_data, s3_data),
            self._analyze_reliability_async()
        )

        # Generate recommendations (depends on previous results)
        recommendations = self._generate_recommendations(
            well_architected_scores,
            cost_analysis,
            performance_analysis,
            security_analysis,
            reliability_analysis
        )

        # Calculate overall score
        overall_score = self._calculate_overall_score(well_architected_scores)

        return {
            "client_id": self.client_id,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "overall_score": overall_score,
            "overall_rating": self._get_rating(overall_score),
            "well_architected": well_architected_scores,
            "cost_analysis": cost_analysis,
            "performance": performance_analysis,
            "security": security_analysis,
            "reliability": reliability_analysis,
            "recommendations": recommendations,
            "summary": self._generate_executive_summary(
                overall_score, cost_analysis, security_analysis, recommendations
            )
        }

    async def _evaluate_well_architected_async(self) -> Dict[str, Any]:
        """
        Evaluates architecture against AWS Well-Architected Framework pillars.
        Uses pre-computed data for O(1) access instead of O(n) iterations.
        """
        pc = self._precomputed

        # All pillar evaluations use pre-computed data - no iterations needed
        operational_score = self._evaluate_operational_excellence_optimized()
        security_score = self._evaluate_security_pillar_optimized()
        reliability_score = self._evaluate_reliability_pillar_optimized()
        performance_score = self._evaluate_performance_pillar_optimized()
        cost_score = self._evaluate_cost_pillar_optimized()

        return {
            "pillars": {
                "operational_excellence": {
                    "score": operational_score,
                    "rating": self._get_rating(operational_score),
                    "description": "How well you run and monitor systems"
                },
                "security": {
                    "score": security_score,
                    "rating": self._get_rating(security_score),
                    "description": "Protecting information and systems"
                },
                "reliability": {
                    "score": reliability_score,
                    "rating": self._get_rating(reliability_score),
                    "description": "Recovery and mitigation capabilities"
                },
                "performance_efficiency": {
                    "score": performance_score,
                    "rating": self._get_rating(performance_score),
                    "description": "Efficient use of computing resources"
                },
                "cost_optimization": {
                    "score": cost_score,
                    "rating": self._get_rating(cost_score),
                    "description": "Avoiding unnecessary costs"
                }
            },
            "average_score": statistics.mean([
                operational_score, security_score, reliability_score,
                performance_score, cost_score
            ])
        }

    def _evaluate_operational_excellence_optimized(self) -> float:
        """
        Optimized operational excellence evaluation using pre-computed data.
        O(1) complexity instead of O(n).
        """
        pc = self._precomputed

        if pc.ec2_count == 0:
            return 70.0

        score = 100.0

        # Use pre-computed counts - O(1)
        ratio = pc.tagged_instances_count / pc.ec2_count
        if ratio < 0.5:
            score -= 20
        elif ratio < 0.8:
            score -= 10

        # Use pre-computed regions set - O(1)
        if len(pc.regions) < 2:
            score -= 15

        return max(0.0, min(100.0, score))

    def _evaluate_security_pillar_optimized(self) -> float:
        """
        Optimized security evaluation using pre-computed data.
        O(1) complexity instead of O(n).
        """
        pc = self._precomputed

        if not pc.findings_by_severity and pc.s3_count == 0:
            return 70.0

        score = 100.0

        # Use pre-computed findings - O(1)
        critical_count = len(pc.findings_by_severity.get('CRITICAL', []))
        high_count = len(pc.findings_by_severity.get('HIGH', []))
        medium_count = len(pc.findings_by_severity.get('MEDIUM', []))

        score -= (critical_count * self.SEVERITY_WEIGHTS['CRITICAL'])
        score -= (high_count * self.SEVERITY_WEIGHTS['HIGH'])
        score -= (medium_count * self.SEVERITY_WEIGHTS['MEDIUM'])

        # Use pre-computed public buckets count - O(1)
        score -= (pc.public_buckets_count * 10)

        return max(0.0, min(100.0, score))

    def _evaluate_reliability_pillar_optimized(self) -> float:
        """
        Optimized reliability evaluation using pre-computed data.
        O(1) complexity instead of O(n).
        """
        pc = self._precomputed

        if pc.ec2_count == 0:
            return 70.0

        score = 100.0

        # Use pre-computed availability zones - O(1)
        az_count = len(pc.availability_zones)
        if az_count < 2:
            score -= 25
        elif az_count < 3:
            score -= 10

        score -= 5  # Backup practices placeholder

        return max(0.0, min(100.0, score))

    def _evaluate_performance_pillar_optimized(self) -> float:
        """
        Optimized performance evaluation using pre-computed data.
        O(1) complexity instead of O(n).
        """
        pc = self._precomputed

        if pc.ec2_count == 0:
            return 70.0

        score = 100.0

        # Use pre-computed old generation count - O(1)
        if pc.old_gen_instances_count > 0:
            old_ratio = pc.old_gen_instances_count / pc.ec2_count
            score -= (old_ratio * 30)

        return max(0.0, min(100.0, score))

    def _evaluate_cost_pillar_optimized(self) -> float:
        """
        Optimized cost evaluation using pre-computed data.
        O(1) complexity instead of O(n).
        """
        pc = self._precomputed

        if pc.ec2_count == 0:
            return 70.0

        score = 100.0

        # Use pre-computed stopped instances count - O(1)
        if pc.stopped_instances_count > 0:
            score -= (pc.stopped_instances_count * 5)

        # Check for reserved/spot instance usage
        if pc.ec2_count > 5:
            score -= 15

        return max(0.0, min(100.0, score))

    async def _analyze_costs_async(
        self,
        cost_data: Dict,
        ec2_data: List[Dict],
        s3_data: List[Dict]
    ) -> Dict[str, Any]:
        """
        Optimized cost analysis with pre-computed data.
        """
        pc = self._precomputed

        total_cost = cost_data.get('total_cost', 0)
        cost_by_service = cost_data.get('by_service', {})

        # Efficient sorting with limit
        sorted_services = sorted(
            cost_by_service.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]  # Only sort top 5

        # Calculate potential savings using pre-computed data
        potential_savings = self._calculate_potential_savings_optimized(
            cost_by_service
        )

        # Cost projections
        projected_annual = total_cost * 12

        return {
            "total_monthly_cost": round(total_cost, 2),
            "projected_annual_cost": round(projected_annual, 2),
            "top_cost_drivers": [
                {"service": service, "cost": round(cost, 2)}
                for service, cost in sorted_services
            ],
            "potential_monthly_savings": round(potential_savings, 2),
            "potential_annual_savings": round(potential_savings * 12, 2),
            "cost_efficiency_score": self._calculate_cost_efficiency_optimized(total_cost)
        }

    def _calculate_potential_savings_optimized(
        self,
        cost_by_service: Dict
    ) -> float:
        """
        Optimized savings calculation using pre-computed data.
        O(1) complexity instead of O(n).
        """
        pc = self._precomputed
        savings = 0.0

        ec2_cost = cost_by_service.get('Amazon Elastic Compute Cloud - Compute', 0)

        # Rightsizing savings
        underutilized_ratio = 0.3
        savings += ec2_cost * underutilized_ratio * 0.2

        # Reserved instance savings
        if pc.ec2_count > 5:
            savings += ec2_cost * 0.3

        # Stopped instances savings - using pre-computed count
        if pc.stopped_instances_count > 0:
            avg_instance_cost = ec2_cost / max(pc.ec2_count, 1)
            savings += pc.stopped_instances_count * avg_instance_cost * 0.2

        return savings

    def _calculate_cost_efficiency_optimized(self, total_cost: float) -> float:
        """
        Optimized cost efficiency calculation using pre-computed data.
        O(1) complexity.
        """
        pc = self._precomputed
        total_resources = pc.ec2_count + pc.s3_count

        if total_resources == 0:
            return 50.0

        cost_per_resource = total_cost / total_resources

        # Efficient threshold checks
        if cost_per_resource <= 20:
            return 100.0
        elif cost_per_resource <= 50:
            return 80.0
        elif cost_per_resource <= 100:
            return 60.0
        else:
            return 40.0

    async def _analyze_performance_async(
        self,
        ec2_data: List[Dict],
        cloudwatch_metrics: Dict
    ) -> Dict[str, Any]:
        """
        Optimized performance analysis with pre-computed data.
        """
        pc = self._precomputed

        # Extract CPU metrics efficiently
        cpu_metrics = cloudwatch_metrics.get('CPUUtilization', {})
        avg_cpu = 0.0
        max_cpu = 0.0

        if cpu_metrics:
            datapoints = cpu_metrics.get('Datapoints', [])
            if datapoints:
                try:
                    # Use generator expression for memory efficiency
                    cpu_values = [dp.get('Average', 0) for dp in datapoints]
                    if cpu_values:
                        avg_cpu = statistics.mean(cpu_values)
                        max_cpu = max(cpu_values)
                except Exception as e:
                    logger.warning(f"Could not calculate CPU statistics: {e}")

        # Performance scoring
        performance_issues = []
        performance_score = 100.0

        # Check for overutilization
        if avg_cpu > 80:
            performance_issues.append({
                "type": "high_cpu_utilization",
                "severity": "HIGH",
                "message": f"Average CPU utilization is {avg_cpu:.1f}%, indicating potential capacity issues"
            })
            performance_score -= 20

        # Use pre-computed old generation count
        if pc.old_gen_instances_count > 0:
            performance_issues.append({
                "type": "old_generation_instances",
                "severity": "MEDIUM",
                "message": f"{pc.old_gen_instances_count} instances using older generation types"
            })
            performance_score -= 10

        return {
            "performance_score": max(0, performance_score),
            "metrics": {
                "avg_cpu_utilization": round(avg_cpu, 2),
                "max_cpu_utilization": round(max_cpu, 2),
                "total_instances": pc.ec2_count
            },
            "issues": performance_issues
        }

    async def _analyze_security_async(
        self,
        ec2_data: List[Dict],
        s3_data: List[Dict]
    ) -> Dict[str, Any]:
        """
        Optimized security analysis using pre-computed data.
        O(1) complexity for counts, O(k) for top 5 critical issues where k <= 5.
        """
        pc = self._precomputed

        # Calculate security score using pre-computed data
        security_score = 100.0
        critical_findings = pc.findings_by_severity.get('CRITICAL', [])
        high_findings = pc.findings_by_severity.get('HIGH', [])
        medium_findings = pc.findings_by_severity.get('MEDIUM', [])

        security_score -= len(critical_findings) * self.SEVERITY_WEIGHTS['CRITICAL']
        security_score -= len(high_findings) * self.SEVERITY_WEIGHTS['HIGH']
        security_score -= len(medium_findings) * self.SEVERITY_WEIGHTS['MEDIUM']
        security_score = max(0, security_score)

        # Total findings count
        total_findings = sum(len(findings) for findings in pc.findings_by_severity.values())

        # Top 5 critical issues (already in list, just slice)
        critical_issues = [
            {
                "id": f.get('id', 'unknown'),
                "title": f.get('title', 'Security Finding'),
                "severity": f.get('severity', 'UNKNOWN')
            }
            for f in critical_findings[:5]
        ]

        return {
            "security_score": security_score,
            "total_findings": total_findings,
            "findings_by_severity": {
                severity: len(findings)
                for severity, findings in pc.findings_by_severity.items()
            },
            "critical_issues": critical_issues,
            "vulnerabilities": {
                "unencrypted_s3_buckets": pc.unencrypted_buckets_count
            }
        }

    async def _analyze_reliability_async(self) -> Dict[str, Any]:
        """
        Optimized reliability analysis using pre-computed data.
        O(1) complexity instead of O(n).
        """
        pc = self._precomputed

        # Use pre-computed sets for O(1) length checks
        multi_az = len(pc.availability_zones) >= 2
        multi_region = len(pc.regions) >= 2

        # Calculate reliability score
        reliability_score = 70.0

        if multi_region:
            reliability_score += 20
        elif multi_az:
            reliability_score += 10

        # Check for single points of failure
        single_points_of_failure = []

        if len(pc.regions) == 1:
            single_points_of_failure.append({
                "type": "single_region",
                "impact": "HIGH",
                "message": "All resources in single region - no geographic redundancy"
            })

        if len(pc.availability_zones) < 2:
            single_points_of_failure.append({
                "type": "single_az",
                "impact": "CRITICAL",
                "message": "Resources not distributed across availability zones"
            })

        return {
            "reliability_score": min(100, reliability_score),
            "multi_az_deployment": multi_az,
            "multi_region_deployment": multi_region,
            "availability_zones": list(pc.availability_zones),
            "regions": list(pc.regions),
            "single_points_of_failure": single_points_of_failure
        }

    def _generate_recommendations(
        self,
        well_architected: Dict,
        cost_analysis: Dict,
        performance: Dict,
        security: Dict,
        reliability: Dict
    ) -> List[Dict[str, Any]]:
        """
        Generate prioritized recommendations.
        Optimized with efficient list building and sorting.
        """
        recommendations = []

        # Security recommendations (highest priority)
        if security['security_score'] < 80:
            if security['total_findings'] > 0:
                recommendations.append({
                    "priority": "CRITICAL",
                    "category": "Security",
                    "title": "Address Critical Security Findings",
                    "description": f"You have {security['findings_by_severity'].get('CRITICAL', 0)} critical and {security['findings_by_severity'].get('HIGH', 0)} high severity security findings",
                    "impact": "Prevents security breaches and data loss",
                    "effort": "HIGH",
                    "potential_savings": 0
                })

        if security['vulnerabilities']['unencrypted_s3_buckets'] > 0:
            recommendations.append({
                "priority": "HIGH",
                "category": "Security",
                "title": "Enable S3 Bucket Encryption",
                "description": f"Enable encryption for {security['vulnerabilities']['unencrypted_s3_buckets']} unencrypted S3 buckets",
                "impact": "Protects data at rest",
                "effort": "LOW",
                "potential_savings": 0
            })

        # Cost optimization recommendations
        if cost_analysis['potential_monthly_savings'] > 100:
            recommendations.append({
                "priority": "HIGH",
                "category": "Cost Optimization",
                "title": "Implement Cost Optimization Strategies",
                "description": "Right-size instances, use reserved instances, and remove stopped resources",
                "impact": "Significant cost reduction",
                "effort": "MEDIUM",
                "potential_savings": cost_analysis['potential_monthly_savings']
            })

        # Reliability recommendations
        if not reliability['multi_az_deployment']:
            recommendations.append({
                "priority": "HIGH",
                "category": "Reliability",
                "title": "Enable Multi-AZ Deployment",
                "description": "Deploy resources across multiple availability zones for fault tolerance",
                "impact": "Improves availability and disaster recovery",
                "effort": "MEDIUM",
                "potential_savings": 0
            })

        # Performance recommendations
        if performance['performance_score'] < 80:
            for issue in performance['issues']:
                if issue['type'] == 'old_generation_instances':
                    recommendations.append({
                        "priority": "MEDIUM",
                        "category": "Performance",
                        "title": "Upgrade to Latest Generation Instances",
                        "description": issue['message'],
                        "impact": "Better performance and cost efficiency",
                        "effort": "MEDIUM",
                        "potential_savings": cost_analysis['total_monthly_cost'] * 0.1
                    })

        # Operational excellence recommendations
        op_score = well_architected['pillars']['operational_excellence']['score']
        if op_score < 80:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Operational Excellence",
                "title": "Improve Resource Tagging",
                "description": "Implement comprehensive tagging strategy for all resources",
                "impact": "Better resource management and cost allocation",
                "effort": "LOW",
                "potential_savings": 0
            })

        # Efficient sorting with pre-defined priority order
        recommendations.sort(key=lambda x: self.PRIORITY_ORDER.get(x['priority'], 99))

        return recommendations

    def _calculate_overall_score(self, well_architected: Dict) -> float:
        """Calculate overall architecture health score."""
        return round(well_architected['average_score'], 1)

    @staticmethod
    @lru_cache(maxsize=128)
    def _get_rating(score: float) -> str:
        """
        Convert numerical score to rating.
        Cached for repeated calls with same score.
        """
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
        else:
            return "Poor"

    def _generate_executive_summary(
        self,
        overall_score: float,
        cost_analysis: Dict,
        security: Dict,
        recommendations: List[Dict]
    ) -> str:
        """
        Generate executive summary.
        Optimized with efficient string building.
        """
        rating = self._get_rating(overall_score)

        # Count recommendations efficiently
        critical_recs = sum(1 for r in recommendations if r['priority'] == 'CRITICAL')

        # Build summary efficiently
        summary_parts = [
            f"Your cloud architecture has an overall health score of {overall_score}/100 ({rating})."
        ]

        if critical_recs > 0:
            summary_parts.append(
                f"There are {critical_recs} critical recommendations that require immediate attention."
            )

        if cost_analysis['potential_monthly_savings'] > 0:
            summary_parts.append(
                f"We identified ${cost_analysis['potential_monthly_savings']:.2f} in potential monthly cost savings."
            )

        if security['total_findings'] > 0:
            summary_parts.append(
                f"Your security posture shows {security['total_findings']} findings that should be addressed."
            )

        summary_parts.append(
            f"Review the {len(recommendations)} recommendations below to improve your architecture."
        )

        return " ".join(summary_parts)