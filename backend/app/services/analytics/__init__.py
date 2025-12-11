"""
architecture_analyzer
=====================
AWS Architecture Analyzer - 6 Pillars Well-Architected Framework.

Usage:
    from architecture_analyzer import ArchitectureAnalyzer

    analyzer = ArchitectureAnalyzer(client_id="client-123")
    results = await analyzer.analyze_full_architecture(...)
"""

from .analyzer import ArchitectureAnalyzer, PreComputedData, get_rating

__version__ = "3.0.0"
__all__ = ['ArchitectureAnalyzer', 'PreComputedData', 'get_rating']
