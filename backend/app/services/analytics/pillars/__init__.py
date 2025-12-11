"""
AWS Well-Architected Framework - 6 Pillars
"""

from .base import BasePillar
from .operational_excellence import OperationalExcellencePillar
from .security import SecurityPillar
from .reliability import ReliabilityPillar
from .performance import PerformancePillar
from .cost_optimize import CostOptimizationPillar
from .sustainability import SustainabilityPillar

# Registry for iteration
PILLAR_CLASSES = {
    'operational_excellence': OperationalExcellencePillar,
    'security': SecurityPillar,
    'reliability': ReliabilityPillar,
    'performance_efficiency': PerformancePillar,
    'cost_optimization': CostOptimizationPillar,
    'sustainability': SustainabilityPillar,
}

__all__ = [
    'BasePillar',
    'OperationalExcellencePillar',
    'SecurityPillar',
    'ReliabilityPillar',
    'PerformancePillar',
    'CostOptimizationPillar',
    'SustainabilityPillar',
    'PILLAR_CLASSES',
]
