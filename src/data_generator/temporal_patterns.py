# src/data_generator/temporal_patterns.py

import numpy as np
import pandas as pd
from datetime import timedelta


class TemporalPatternGenerator:
    """Simulates temporal trends and anomalies in patient data"""

    def __init__(self, anomaly_rate=0.1):
        self.anomaly_rate = anomaly_rate

    def apply_trends(self, df: pd.DataFrame, metric: str, trend: str = 'increase') -> pd.DataFrame:
        df = df.sort_values(by='visit_date').copy()
        trend_factor = 0.01 if trend == 'increase' else -0.01
        for i in range(1, len(df)):
            df.loc[df.index[i], metric] = df.loc[df.index[i - 1], metric] * (1 + trend_factor + np.random.normal(0, 0.005))
        return df

    def inject_anomalies(self, df: pd.DataFrame, metrics: list) -> pd.DataFrame:
        for metric in metrics:
            if metric in df.columns:
                n_anomalies = int(len(df) * self.anomaly_rate)
                anomaly_indices = np.random.choice(df.index, n_anomalies, replace=False)
                for idx in anomaly_indices:
                    df.at[idx, metric] *= np.random.uniform(1.5, 2.5)  # Sudden spike
        return df

    def add_cyclic_patterns(self, df: pd.DataFrame, metric: str, amplitude: float = 5, period_days: int = 90) -> pd.DataFrame:
        df = df.sort_values(by='visit_date').copy()
        for i, row in df.iterrows():
            days = (row['visit_date'] - df['visit_date'].min()).days
            df.at[i, metric] += amplitude * np.sin(2 * np.pi * days / period_days)
        return df