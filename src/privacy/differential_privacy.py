
# This component implements differential privacy to protect patient information while maintaining analytical utility.

# src/privacy/differential_privacy.py
import numpy as np
import pandas as pd
from typing import List, Dict, Union, Tuple


class DifferentialPrivacy:
    """Implements differential privacy techniques for healthcare data"""

    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5):
        """
        Initialize differential privacy parameters

        Args:
            epsilon: Privacy budget (lower = more privacy)
            delta: Probability of privacy violation
        """
        self.epsilon = epsilon
        self.delta = delta

    def add_laplace_noise(self, data: pd.Series, sensitivity: float) -> pd.Series:
        """
        Add Laplace noise to numeric data

        Args:
            data: Series of numeric values
            sensitivity: Maximum change one individual can have on the output

        Returns:
            Series with noise added
        """
        scale = sensitivity / self.epsilon
        noise = np.random.laplace(0, scale, size=len(data))
        return data + noise

    def add_gaussian_noise(self, data: pd.Series, sensitivity: float) -> pd.Series:
        """
        Add Gaussian noise to numeric data (for relaxed DP with delta > 0)

        Args:
            data: Series of numeric values
            sensitivity: Maximum change one individual can have on the output

        Returns:
            Series with noise added
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

        Args:
            df: DataFrame to privatize
            numeric_columns: List of numeric columns to add noise to
            categorical_columns: List of categorical columns to apply anonymization
            sensitivities: Dict mapping column names to their sensitivity values

        Returns:
            Privacy-protected DataFrame
        """
        # Make a copy to avoid modifying the original
        private_df = df.copy()

        # Use default sensitivities if not provided
        if sensitivities is None:
            # Default: estimate sensitivity as 1/10th of the range for each column
            sensitivities = {}
            for col in numeric_columns:
                if col in df.columns:
                    sensitivities[col] = (df[col].max() - df[col].min()) / 10.0

        # Apply noise to numeric columns
        for col in numeric_columns:
            if col in df.columns:
                sensitivity = sensitivities.get(col, 1.0)  # Default sensitivity

                # Choose noise mechanism based on epsilon and data characteristics
                if self.delta > 0 and df[col].count() > 100:
                    private_df[col] = self.add_gaussian_noise(df[col], sensitivity)
                else:
                    private_df[col] = self.add_laplace_noise(df[col], sensitivity)

        # Handle categorical columns if specified
        if categorical_columns:
            for col in categorical_columns:
                if col in df.columns:
                    # For categorical data, we can use randomized response
                    private_df[col] = self._randomized_response(df[col])

        return private_df

    def _randomized_response(self, series: pd.Series) -> pd.Series:
        """
        Apply randomized response to categorical data

        Args:
            series: Categorical data series

        Returns:
            Privacy-protected categorical series
        """
        # Get all possible values
        all_values = series.unique()

        # Probability of keeping original value
        p = np.exp(self.epsilon) / (np.exp(self.epsilon) + len(all_values) - 1)

        # Apply randomized response
        result = series.copy()

        for i in range(len(result)):
            if np.random.random() > p:
                # Pick a random value
                result.iloc[i] = np.random.choice(all_values)

        return result

    def compute_private_statistics(self,
                                   data: pd.Series,
                                   stats: List[str] = ['mean', 'variance'],
                                   sensitivity: float = None) -> Dict[str, float]:
        """
        Compute differentially private statistics

        Args:
            data: Series of numeric values
            stats: List of statistics to compute
            sensitivity: Data sensitivity

        Returns:
            Dictionary of private statistics
        """
        results = {}

        # Estimate sensitivity if not provided
        if sensitivity is None:
            sensitivity = (data.max() - data.min()) / data.count()

        if 'mean' in stats:
            # For mean, sensitivity is range/n
            mean_sensitivity = sensitivity / len(data)
            noise = np.random.laplace(0, mean_sensitivity / self.epsilon)
            results['mean'] = data.mean() + noise

        if 'variance' in stats or 'std' in stats:
            # For variance, sensitivity calculation is more complex
            # Using simplified approach here
            variance_sensitivity = sensitivity ** 2
            noise = np.random.laplace(0, variance_sensitivity / self.epsilon)
            true_variance = data.var()
            results['variance'] = max(0, true_variance + noise)  # Ensure non-negative

            if 'std' in stats:
                results['std'] = np.sqrt(results['variance'])

        if 'median' in stats:
            # For median, can use the exponential mechanism
            results['median'] = self._private_median(data, sensitivity)

        if 'count' in stats:
            # For count, sensitivity is 1
            count_noise = np.random.laplace(0, 1.0 / self.epsilon)
            results['count'] = max(0, len(data) + count_noise)  # Ensure non-negative

        return results

    def _private_median(self, data: pd.Series, sensitivity: float) -> float:
        """
        Compute differentially private median using the exponential mechanism

        Args:
            data: Series of numeric values
            sensitivity: Data sensitivity

        Returns:
            Private approximation of median
        """
        # Simplification: Sample from data with exponential weights
        sorted_data = sorted(data)
        n = len(sorted_data)

        if n == 0:
            return np.nan

        # Calculate scores based on distance from median
        true_median = np.median(sorted_data)

        # Calculate utility scores (negative distance from median)
        utilities = [-abs(x - true_median) for x in sorted_data]

        # Scale by epsilon and sensitivity
        scaled_utilities = [u * self.epsilon / (2 * sensitivity) for u in utilities]

        # Convert to probabilities (softmax)
        max_utility = max(scaled_utilities)
        exp_utilities = [np.exp(u - max_utility) for u in scaled_utilities]
        probabilities = [u / sum(exp_utilities) for u in exp_utilities]

        # Sample according to these probabilities
        return np.random.choice(sorted_data, p=probabilities)