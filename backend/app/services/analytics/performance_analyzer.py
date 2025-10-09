

import pandas as pd

class PerformanceAnalyzer:
    def __init__(self, metrics: pd.DataFrame):
        self.metrics = metrics

    def average_latency(self):
        """Calculate average latency across services."""
        return self.metrics["latency"].mean()

    def performance_summary(self):
        """Generate a simple performance summary."""
        return {
            "avg_latency": self.average_latency(),
            "max_cpu": self.metrics["cpu_usage"].max(),
            "min_memory": self.metrics["memory_usage"].min()
        }
