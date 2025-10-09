

import pandas as pd

class CostOptimizer:
    def __init__(self, usage_data: pd.DataFrame):
        self.usage_data = usage_data

    def identify_underutilized_resources(self):
        """Detects resources with low utilization."""
        return self.usage_data[self.usage_data["cpu_utilization"] < 20]

    def suggest_rightsizing(self):
        """Suggests resizing recommendations based on utilization."""
        underused = self.identify_underutilized_resources()
        return [{"resource_id": r["id"], "recommendation": "Downsize"} for _, r in underused.iterrows()]
