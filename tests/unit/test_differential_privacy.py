"""
Unit tests for Differential Privacy
"""

import pytest
import numpy as np
import pandas as pd
from src.privacy.differential_privacy import DifferentialPrivacy


class TestDifferentialPrivacy:
    """Test cases for DifferentialPrivacy class"""

    def test_init(self):
        """Test DifferentialPrivacy initialization"""
        dp = DifferentialPrivacy(epsilon=1.0, delta=1e-5)
        assert dp.epsilon == 1.0
        assert dp.delta == 1e-5

    def test_init_defaults(self):
        """Test default parameter values"""
        dp = DifferentialPrivacy()
        assert dp.epsilon == 1.0
        assert dp.delta == 1e-5

    def test_laplace_noise_shape(self):
        """Test that Laplace noise preserves shape"""
        dp = DifferentialPrivacy(epsilon=1.0)
        data = pd.Series([1, 2, 3, 4, 5])
        noisy = dp.add_laplace_noise(data, sensitivity=1.0)
        assert len(noisy) == len(data)

    def test_gaussian_noise_shape(self):
        """Test that Gaussian noise preserves shape"""
        dp = DifferentialPrivacy(epsilon=1.0, delta=1e-5)
        data = pd.Series([1, 2, 3, 4, 5])
        noisy = dp.add_gaussian_noise(data, sensitivity=1.0)
        assert len(noisy) == len(data)

    def test_noise_changes_values(self):
        """Test that noise actually modifies values"""
        dp = DifferentialPrivacy(epsilon=1.0)
        data = pd.Series([100.0] * 10)
        noisy = dp.add_laplace_noise(data, sensitivity=1.0)
        assert not data.equals(noisy)

    def test_private_mean(self):
        """Test private mean computation"""
        dp = DifferentialPrivacy(epsilon=1.0)
        data = np.array([1, 2, 3, 4, 5])
        result = dp.private_mean(data)
        assert isinstance(result, float)
        assert abs(result - 3.0) < 10.0

    def test_private_variance(self):
        """Test private variance computation"""
        dp = DifferentialPrivacy(epsilon=1.0)
        data = np.array([1, 2, 3, 4, 5])
        result = dp.private_variance(data)
        assert isinstance(result, float)
        assert result >= 0

    def test_private_count(self):
        """Test private count computation"""
        dp = DifferentialPrivacy(epsilon=1.0)
        data = np.array([1, 2, 3, 4, 5])
        result = dp.private_count(data)
        assert isinstance(result, float)
        assert abs(result - 5) < 20

    def test_compute_private_statistics(self):
        """Test computing multiple private statistics at once"""
        dp = DifferentialPrivacy(epsilon=1.0)
        data = pd.Series([10, 20, 30, 40, 50])
        stats = dp.compute_private_statistics(data, stats=['mean', 'variance', 'count'])
        assert 'mean' in stats
        assert 'variance' in stats
        assert 'count' in stats

    def test_privatize_dataframe_preserves_columns(self, sample_patients):
        """Test that privatize_dataframe preserves columns"""
        dp = DifferentialPrivacy(epsilon=1.0)
        private_df = dp.privatize_dataframe(
            sample_patients,
            numeric_columns=['age', 'income']
        )
        assert list(private_df.columns) == list(sample_patients.columns)

    def test_privatize_dataframe_preserves_shape(self, sample_patients):
        """Test that privatize_dataframe preserves shape"""
        dp = DifferentialPrivacy(epsilon=1.0)
        private_df = dp.privatize_dataframe(
            sample_patients,
            numeric_columns=['age', 'income']
        )
        assert private_df.shape == sample_patients.shape

    def test_privatize_modifies_numeric_columns(self, sample_patients):
        """Test that numeric columns are modified"""
        dp = DifferentialPrivacy(epsilon=1.0)
        private_df = dp.privatize_dataframe(
            sample_patients,
            numeric_columns=['age', 'income']
        )
        assert not private_df['age'].equals(sample_patients['age'])
        assert not private_df['income'].equals(sample_patients['income'])

    def test_non_privatized_columns_unchanged(self, sample_patients):
        """Test that non-targeted columns stay the same"""
        dp = DifferentialPrivacy(epsilon=1.0)
        private_df = dp.privatize_dataframe(
            sample_patients,
            numeric_columns=['age']
        )
        assert private_df['patient_id'].equals(sample_patients['patient_id'])

    def test_categorical_privatization(self):
        """Test randomized response on categorical data"""
        dp = DifferentialPrivacy(epsilon=1.0)
        df = pd.DataFrame({
            'id': range(100),
            'category': ['A', 'B', 'C'] * 33 + ['A']
        })
        private_df = dp.privatize_dataframe(
            df,
            numeric_columns=[],
            categorical_columns=['category']
        )
        assert set(private_df['category'].unique()).issubset({'A', 'B', 'C'})
        assert len(private_df) == len(df)

    def test_epsilon_affects_noise_magnitude(self):
        """Test that smaller epsilon adds more noise"""
        data = pd.Series([100.0] * 100)

        dp_high_privacy = DifferentialPrivacy(epsilon=0.1)
        dp_low_privacy = DifferentialPrivacy(epsilon=10.0)

        noisy_high = dp_high_privacy.add_laplace_noise(data, sensitivity=1.0)
        noisy_low = dp_low_privacy.add_laplace_noise(data, sensitivity=1.0)

        var_high = (noisy_high - data).var()
        var_low = (noisy_low - data).var()

        assert var_high > var_low

    @pytest.mark.parametrize("epsilon", [0.1, 0.5, 1.0, 5.0, 10.0])
    def test_various_epsilon_values(self, epsilon):
        """Test privacy with various epsilon values"""
        dp = DifferentialPrivacy(epsilon=epsilon)
        data = np.array([1, 2, 3, 4, 5])
        result = dp.private_mean(data)
        assert isinstance(result, float)
