from abc import ABC, abstractmethod


class BasePillar(ABC):
    """Abstract base class for all 6 pillars."""

    name: str = "base"
    description: str = "Base pillar"

    def __init__(self, precomputed):
        """
        Args:
            precomputed: PreComputedData instance from analyzer.py
        """
        self._pc = precomputed

    @abstractmethod
    def evaluate(self) -> float:
        """Return score 0-100."""
        pass

    @staticmethod
    def clamp(score: float) -> float:
        return max(0.0, min(100.0, score))
