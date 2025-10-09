

import pandas as pd
from sklearn.ensemble import IsolationForest

class AnomalyDetector:
    def __init__(self, metric_data: pd.DataFrame):
        self.metric_data = metric_data
        self.model = IsolationForest(contamination=0.05, random_state=42)

    def detect_anomalies(self):
        """Detect unusual patterns in the data."""
        self.metric_data["anomaly_score"] = self.model.fit_predict(self.metric_data[["value"]])
        anomalies = self.metric_data[self.metric_data["anomaly_score"] == -1]
        return anomalies
