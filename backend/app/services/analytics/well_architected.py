"""
Comprehensive Architecture Analyzer
Analyzes cloud architecture across multiple dimensions:
- AWS Well-Architected Framework (5 pillars)
- Cost optimization opportunities
- Performance metrics and bottlenecks
- Security posture
- Reliability and fault tolerance
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import statistics


class ArchitectureAnalyzer:
    """
    Main architecture analysis engine that combines multiple evaluation dimensions
    to provide comprehensive insights to customers.
    """

    def __init__(self, client_id: str):
        self.client_id = client_id
        self.analysis_timestamp = datetime.utcnow()

    async def analyze_full_architecture(
            self,
            ec2_data: List[Dict],
            s3_data: List[Dict],
            cost_data: Dict,
            security_findings: List[Dict],
            cloudwatch_metrics: Dict
    ) -> Dict[str, Any]:
        """
        Performs comprehensive architecture analysis across all dimensions.

        Returns a complete architecture report with scores, recommendations,
        and actionable insights for customers.
        """

        # Run all analysis modules
        well_architected_scores = self._evaluate_well_architected(
            ec2_data, s3_data, security_findings
        )

        cost_analysis = self._analyze_costs(cost_data, ec2_data, s3_data)

        performance_analysis = self._analyze_performance(
            ec2_data, cloudwatch_metrics
        )

        security_analysis = self._analyze_security(security_findings, ec2_data, s3_data)

        reliability_analysis = self._analyze_reliability(ec2_data, s3_data)

        recommendations = self._generate_recommendations(
            well_architected_scores,
            cost_analysis,
            performance_analysis,
            security_analysis,
            reliability_analysis
        )

        # Calculate overall architecture health score
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

    def _evaluate_well_architected(
            self,
            ec2_data: List[Dict],
            s3_data: List[Dict],
            security_findings: List[Dict]
    ) -> Dict[str, Any]:
        """
        Evaluates architecture against AWS Well-Architected Framework pillars.

        Pillars:
        1. Operational Excellence
        2. Security
        3. Reliability
        4. Performance Efficiency
        5. Cost Optimization
        """

        # Count resources
        total_instances = len(ec2_data)
        total_buckets = len(s3_data)
        critical_findings = len([f for f in security_findings if f.get('severity') == 'CRITICAL'])
        high_findings = len([f for f in security_findings if f.get('severity') == 'HIGH'])

        # Pillar 1: Operational Excellence (0-100)
        operational_score = self._evaluate_operational_excellence(ec2_data)

        # Pillar 2: Security (0-100)
        security_score = self._evaluate_security_pillar(
            security_findings, ec2_data, s3_data
        )

        # Pillar 3: Reliability (0-100)
        reliability_score = self._evaluate_reliability_pillar(ec2_data)

        # Pillar 4: Performance Efficiency (0-100)
        performance_score = self._evaluate_performance_pillar(ec2_data)

        # Pillar 5: Cost Optimization (0-100)
        cost_score = self._evaluate_cost_pillar(ec2_data, s3_data)

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

    def _evaluate_operational_excellence(self, ec2_data: List[Dict]) -> float:
        """Evaluate operational excellence based on tagging, monitoring, etc."""
        if not ec2_data:
            return 70.0  # Neutral score if no data

        score = 100.0

        # Check tagging practices
        tagged_instances = sum(
            1 for instance in ec2_data
            if instance.get('tags') and len(instance.get('tags', [])) > 0
        )
        tagging_ratio = tagged_instances / len(ec2_data) if ec2_data else 0

        # Tagging is crucial for operational excellence
        if tagging_ratio < 0.5:
            score -= 20
        elif tagging_ratio < 0.8:
            score -= 10

        # Check for instances in multiple regions (disaster recovery consideration)
        regions = set(instance.get('region', 'us-east-1') for instance in ec2_data)
        if len(regions) == 1:
            score -= 15  # Single region is a risk

        return max(0, min(100, score))

    def _evaluate_security_pillar(
            self,
            security_findings: List[Dict],
            ec2_data: List[Dict],
            s3_data: List[Dict]
    ) -> float:
        """Evaluate security posture."""
        score = 100.0

        # Deduct points for security findings
        critical_count = sum(1 for f in security_findings if f.get('severity') == 'CRITICAL')
        high_count = sum(1 for f in security_findings if f.get('severity') == 'HIGH')
        medium_count = sum(1 for f in security_findings if f.get('severity') == 'MEDIUM')

        score -= (critical_count * 15)  # -15 per critical finding
        score -= (high_count * 8)  # -8 per high finding
        score -= (medium_count * 3)  # -3 per medium finding

        # Check for public S3 buckets (security risk)
        public_buckets = sum(
            1 for bucket in s3_data
            if bucket.get('public_access', False)
        )
        if public_buckets > 0:
            score -= (public_buckets * 10)

        return max(0, min(100, score))

    def _evaluate_reliability_pillar(self, ec2_data: List[Dict]) -> float:
        """Evaluate reliability and fault tolerance."""
        if not ec2_data:
            return 70.0

        score = 100.0

        # Check for multi-AZ deployment
        availability_zones = set()
        for instance in ec2_data:
            az = instance.get('availability_zone', '')
            if az:
                availability_zones.add(az)

        if len(availability_zones) < 2:
            score -= 25  # Single AZ is not fault tolerant
        elif len(availability_zones) < 3:
            score -= 10

        # Check for backup/snapshot configurations (placeholder - would need actual data)
        # Assume moderate backup practices for now
        score -= 5

        return max(0, min(100, score))

    def _evaluate_performance_pillar(self, ec2_data: List[Dict]) -> float:
        """Evaluate performance efficiency."""
        if not ec2_data:
            return 70.0

        score = 100.0

        # Check for modern instance types
        old_generation_types = ['t2.', 'm3.', 'm4.', 'c3.', 'c4.']
        old_instances = sum(
            1 for instance in ec2_data
            if any(instance.get('instance_type', '').startswith(old_type)
                   for old_type in old_generation_types)
        )

        if old_instances > 0:
            old_ratio = old_instances / len(ec2_data)
            score -= (old_ratio * 30)  # Older instances are less efficient

        return max(0, min(100, score))

    def _evaluate_cost_pillar(self, ec2_data: List[Dict], s3_data: List[Dict]) -> float:
        """Evaluate cost optimization practices."""
        if not ec2_data:
            return 70.0

        score = 100.0

        # Check for stopped instances (wasted EBS costs)
        stopped_instances = sum(
            1 for instance in ec2_data
            if instance.get('state') == 'stopped'
        )
        if stopped_instances > 0:
            score -= (stopped_instances * 5)

        # Check for on-demand vs reserved/spot instances
        # (In real implementation, would check for reserved instance usage)
        # Assume all on-demand for now (not cost-optimized)
        if len(ec2_data) > 5:  # If significant workload
            score -= 15  # Penalty for not using reserved instances

        return max(0, min(100, score))

    def _analyze_costs(
            self,
            cost_data: Dict,
            ec2_data: List[Dict],
            s3_data: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze costs and identify optimization opportunities."""

        total_cost = cost_data.get('total_cost', 0)
        cost_by_service = cost_data.get('by_service', {})

        # Identify top cost drivers
        sorted_services = sorted(
            cost_by_service.items(),
            key=lambda x: x[1],
            reverse=True
        )
        top_cost_drivers = sorted_services[:5]

        # Calculate potential savings
        potential_savings = self._calculate_potential_savings(
            ec2_data, s3_data, cost_by_service
        )

        # Cost trend analysis
        monthly_cost = total_cost
        projected_annual = monthly_cost * 12

        return {
            "total_monthly_cost": round(total_cost, 2),
            "projected_annual_cost": round(projected_annual, 2),
            "top_cost_drivers": [
                {"service": service, "cost": round(cost, 2)}
                for service, cost in top_cost_drivers
            ],
            "potential_monthly_savings": round(potential_savings, 2),
            "potential_annual_savings": round(potential_savings * 12, 2),
            "cost_efficiency_score": self._calculate_cost_efficiency(
                total_cost, len(ec2_data), len(s3_data)
            )
        }

    def _calculate_potential_savings(
            self,
            ec2_data: List[Dict],
            s3_data: List[Dict],
            cost_by_service: Dict
    ) -> float:
        """Calculate potential monthly savings from optimization."""
        savings = 0.0

        # Savings from rightsizing (estimate 20% savings on underutilized instances)
        ec2_cost = cost_by_service.get('Amazon Elastic Compute Cloud - Compute', 0)
        underutilized_ratio = 0.3  # Assume 30% underutilization
        savings += ec2_cost * underutilized_ratio * 0.2

        # Savings from reserved instances (estimate 30% savings)
        if len(ec2_data) > 5:
            savings += ec2_cost * 0.3

        # Savings from stopped instances
        stopped_count = sum(1 for i in ec2_data if i.get('state') == 'stopped')
        if stopped_count > 0:
            avg_instance_cost = ec2_cost / max(len(ec2_data), 1)
            # EBS costs for stopped instances (~20% of instance cost)
            savings += stopped_count * avg_instance_cost * 0.2

        return savings

    def _calculate_cost_efficiency(
            self,
            total_cost: float,
            ec2_count: int,
            s3_count: int
    ) -> float:
        """Calculate cost efficiency score (0-100)."""
        # Simple heuristic: cost per resource
        total_resources = ec2_count + s3_count
        if total_resources == 0:
            return 50.0

        cost_per_resource = total_cost / total_resources

        # Lower cost per resource = higher efficiency
        # Assuming $50/resource is average, $20 is excellent, $100 is poor
        if cost_per_resource <= 20:
            return 100.0
        elif cost_per_resource <= 50:
            return 80.0
        elif cost_per_resource <= 100:
            return 60.0
        else:
            return 40.0

    def _analyze_performance(
            self,
            ec2_data: List[Dict],
            cloudwatch_metrics: Dict
    ) -> Dict[str, Any]:
        """Analyze performance metrics."""

        # Extract CPU utilization if available
        cpu_metrics = cloudwatch_metrics.get('CPUUtilization', [])

        avg_cpu = 0
        max_cpu = 0
        if cpu_metrics:
            datapoints = cpu_metrics[0].get('Datapoints', [])
            if datapoints:
                cpu_values = [dp.get('Average', 0) for dp in datapoints]
                avg_cpu = statistics.mean(cpu_values) if cpu_values else 0
                max_cpu = max(cpu_values) if cpu_values else 0

        # Performance scoring
        performance_issues = []
        performance_score = 100.0

        # Check for overutilized resources
        if avg_cpu > 80:
            performance_issues.append({
                "type": "high_cpu_utilization",
                "severity": "HIGH",
                "message": f"Average CPU utilization is {avg_cpu:.1f}%, indicating potential capacity issues"
            })
            performance_score -= 20

        # Check for old instance types
        old_gen_count = sum(
            1 for i in ec2_data
            if any(i.get('instance_type', '').startswith(t) for t in ['t2.', 'm3.', 'm4.'])
        )
        if old_gen_count > 0:
            performance_issues.append({
                "type": "old_generation_instances",
                "severity": "MEDIUM",
                "message": f"{old_gen_count} instances using older generation types"
            })
            performance_score -= 10

        return {
            "performance_score": max(0, performance_score),
            "metrics": {
                "avg_cpu_utilization": round(avg_cpu, 2),
                "max_cpu_utilization": round(max_cpu, 2),
                "total_instances": len(ec2_data)
            },
            "issues": performance_issues
        }

    def _analyze_security(
            self,
            security_findings: List[Dict],
            ec2_data: List[Dict],
            s3_data: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze security posture."""

        # Categorize findings by severity
        findings_by_severity = {
            "CRITICAL": [],
            "HIGH": [],
            "MEDIUM": [],
            "LOW": [],
            "INFORMATIONAL": []
        }

        for finding in security_findings:
            severity = finding.get('severity', 'INFORMATIONAL')
            findings_by_severity[severity].append(finding)

        # Calculate security score
        security_score = 100.0
        security_score -= len(findings_by_severity['CRITICAL']) * 15
        security_score -= len(findings_by_severity['HIGH']) * 8
        security_score -= len(findings_by_severity['MEDIUM']) * 3
        security_score = max(0, security_score)

        # Check for unencrypted resources
        unencrypted_buckets = sum(
            1 for bucket in s3_data
            if not bucket.get('encryption_enabled', False)
        )

        return {
            "security_score": security_score,
            "total_findings": len(security_findings),
            "findings_by_severity": {
                severity: len(findings)
                for severity, findings in findings_by_severity.items()
            },
            "critical_issues": [
                {
                    "id": f.get('id', 'unknown'),
                    "title": f.get('title', 'Security Finding'),
                    "severity": f.get('severity', 'UNKNOWN')
                }
                for f in findings_by_severity['CRITICAL'][:5]  # Top 5 critical
            ],
            "vulnerabilities": {
                "unencrypted_s3_buckets": unencrypted_buckets
            }
        }

    def _analyze_reliability(
            self,
            ec2_data: List[Dict],
            s3_data: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze reliability and fault tolerance."""

        # Check multi-AZ deployment
        availability_zones = set()
        regions = set()

        for instance in ec2_data:
            if instance.get('availability_zone'):
                availability_zones.add(instance['availability_zone'])
            if instance.get('region'):
                regions.add(instance['region'])

        multi_az = len(availability_zones) >= 2
        multi_region = len(regions) >= 2

        # Calculate reliability score
        reliability_score = 70.0  # Base score

        if multi_region:
            reliability_score += 20
        elif multi_az:
            reliability_score += 10

        # Check for single points of failure
        single_points_of_failure = []

        if len(regions) == 1:
            single_points_of_failure.append({
                "type": "single_region",
                "impact": "HIGH",
                "message": "All resources in single region - no geographic redundancy"
            })

        if len(availability_zones) < 2:
            single_points_of_failure.append({
                "type": "single_az",
                "impact": "CRITICAL",
                "message": "Resources not distributed across availability zones"
            })

        return {
            "reliability_score": min(100, reliability_score),
            "multi_az_deployment": multi_az,
            "multi_region_deployment": multi_region,
            "availability_zones": list(availability_zones),
            "regions": list(regions),
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
        """Generate prioritized recommendations based on analysis."""

        recommendations = []

        # Security recommendations (highest priority)
        if security['security_score'] < 80:
            if security['total_findings'] > 0:
                recommendations.append({
                    "priority": "CRITICAL",
                    "category": "Security",
                    "title": "Address Critical Security Findings",
                    "description": f"You have {security['findings_by_severity']['CRITICAL']} critical and {security['findings_by_severity']['HIGH']} high severity security findings",
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

        # Sort by priority
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 99))

        return recommendations

    def _calculate_overall_score(self, well_architected: Dict) -> float:
        """Calculate overall architecture health score."""
        return round(well_architected['average_score'], 1)

    def _get_rating(self, score: float) -> str:
        """Convert numerical score to rating."""
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
        """Generate executive summary for customers."""

        rating = self._get_rating(overall_score)
        critical_recs = len([r for r in recommendations if r['priority'] == 'CRITICAL'])
        high_recs = len([r for r in recommendations if r['priority'] == 'HIGH'])

        summary = f"Your cloud architecture has an overall health score of {overall_score}/100 ({rating}). "

        if critical_recs > 0:
            summary += f"There are {critical_recs} critical recommendations that require immediate attention. "

        if cost_analysis['potential_monthly_savings'] > 0:
            summary += f"We identified ${cost_analysis['potential_monthly_savings']:.2f} in potential monthly cost savings. "

        if security['total_findings'] > 0:
            summary += f"Your security posture shows {security['total_findings']} findings that should be addressed. "

        summary += f"Review the {len(recommendations)} recommendations below to improve your architecture."

        return summary