# src/privacy/differential_privacy.py
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Union, Optional


class DifferentialPrivacy:
    """Implements differential privacy techniques for healthcare data"""

    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5):
        """
        Initialize differential privacy parameters

        Args:
            epsilon: Privacy budget (lower = more privacy)
            delta: Probability of privacy violation
        """
        if epsilon <= 0:
            raise ValueError("Epsilon must be positive")
        if delta < 0 or delta >= 1:
            raise ValueError("Delta must be in range [0, 1)")

        self.epsilon = epsilon
        self.delta = delta

    def add_laplace_noise(self, data: pd.Series, sensitivity: float) -> pd.Series:
        """
        Add Laplace noise to numeric data
        """
        scale = sensitivity / self.epsilon
        noise = np.random.laplace(0, scale, size=len(data))
        return data + noise

    def add_gaussian_noise(self, data: pd.Series, sensitivity: float) -> pd.Series:
        """
        Add Gaussian noise to numeric data
        """
        sigma = np.sqrt(2 * np.log(1.25 / self.delta)) * sensitivity / self.epsilon
        noise = np.random.normal(0, sigma, size=len(data))
        return data + noise

    def privatize_dataframe(self,
                            df: pd.DataFrame,
                            numeric_columns: List[str],
                            categorical_columns: List[str] = None,
                            sensitivities: Dict[str, float] = None) -> pd.DataFrame:
        """
        Apply differential privacy to an entire DataFrame
        """
        private_df = df.copy()

        if sensitivities is None:
            sensitivities = {}
            for col in numeric_columns:
                if col in df.columns:
                    col_range = df[col].max() - df[col].min()
                    sensitivities[col] = float(col_range / 10.0) if col_range > 0 else 1.0

        for col in numeric_columns:
            if col in df.columns:
                sensitivity = sensitivities.get(col, 1.0)
                if self.delta > 0 and len(df[col]) > 10:
                    private_df[col] = self.add_gaussian_noise(df[col], sensitivity)
                else:
                    private_df[col] = self.add_laplace_noise(df[col], sensitivity)

        if categorical_columns:
            for col in categorical_columns:
                if col in df.columns:
                    private_df[col] = self._randomized_response(df[col])

        return private_df

    def _randomized_response(self, series: pd.Series) -> pd.Series:
        """
        Apply randomized response to categorical data
        """
        all_values = series.unique()
        if len(all_values) <= 1:
            return series

        p = np.exp(self.epsilon) / (np.exp(self.epsilon) + len(all_values) - 1)
        result = series.copy()

        for i in range(len(result)):
            if np.random.random() > p:
                result.iloc[i] = np.random.choice(all_values)

        return result

    def compute_private_statistics(self,
                                   data: pd.Series,
                                   stats: List[str] = ['mean', 'variance'],
                                   sensitivity: float = None) -> Dict[str, float]:
        """
        Compute differentially private statistics
        """
        results = {}
        if sensitivity is None:
            col_range = data.max() - data.min()
            sensitivity = float(col_range / data.count()) if data.count() > 0 else 1.0

        if 'mean' in stats:
            mean_sensitivity = sensitivity / len(data) if len(data) > 0 else sensitivity
            noise = np.random.laplace(0, mean_sensitivity / self.epsilon)
            results['mean'] = float(data.mean() + noise)

        if 'variance' in stats or 'std' in stats:
            variance_sensitivity = sensitivity ** 2
            noise = np.random.laplace(0, variance_sensitivity / self.epsilon)
            true_variance = data.var()
            results['variance'] = float(max(0, true_variance + noise))

            if 'std' in stats:
                results['std'] = np.sqrt(results['variance'])

        if 'count' in stats:
            count_noise = np.random.laplace(0, 1.0 / self.epsilon)
            results['count'] = float(max(0, len(data) + count_noise))

        return results

    def private_mean(self, data, sensitivity: float = None) -> float:
        series = pd.Series(data) if not isinstance(data, pd.Series) else data
        result = self.compute_private_statistics(series, stats=['mean'], sensitivity=sensitivity)
        return result['mean']

    def private_variance(self, data, sensitivity: float = None) -> float:
        series = pd.Series(data) if not isinstance(data, pd.Series) else data
        result = self.compute_private_statistics(series, stats=['variance'], sensitivity=sensitivity)
        return result['variance']

    def private_count(self, data, sensitivity: float = None) -> float:
        series = pd.Series(data) if not isinstance(data, pd.Series) else data
        result = self.compute_private_statistics(series, stats=['count'], sensitivity=sensitivity)
        return result['count']
