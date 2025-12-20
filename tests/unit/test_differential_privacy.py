"""
Unit tests for Differential Privacy
"""

import pytest
import numpy as np
import pandas as pd
from src.privacy.differential_privacy import DifferentialPrivacy


class TestDifferentialPrivacy:
    """Test cases for DifferentialPrivacy class"""

    def test_init(self, privacy_epsilon, privacy_delta):
        """Test DifferentialPrivacy initialization"""
        dp = DifferentialPrivacy(epsilon=privacy_epsilon, delta=privacy_delta)

        assert dp.epsilon == privacy_epsilon
        assert dp.delta == privacy_delta

    def test_laplace_noise_shape(self):
        """Test that Laplace noise has correct shape"""
        dp = DifferentialPrivacy(epsilon=1.0)
        data = np.array([1, 2, 3, 4, 5])

        noisy_data = dp.add_laplace_noise(data, sensitivity=1.0)

        assert noisy_data.shape == data.shape

    def test_gaussian_noise_shape(self):
        """Test that Gaussian noise has correct shape"""
        dp = DifferentialPrivacy(epsilon=1.0, delta=1e-5)
        data = np.array([1, 2, 3, 4, 5])

        noisy_data = dp.add_gaussian_noise(data, sensitivity=1.0)

        assert noisy_data.shape == data.shape

    def test_noise_changes_values(self):
        """Test that noise actually changes the values"""
        dp = DifferentialPrivacy(epsilon=1.0)
        data = np.array([100.0] * 10)

        noisy_data = dp.add_laplace_noise(data, sensitivity=1.0)

        # At least some values should be different
        assert not np.array_equal(data, noisy_data)

    def test_private_mean(self):
        """Test private mean computation"""
        dp = DifferentialPrivacy(epsilon=1.0)
        data = np.array([1, 2, 3, 4, 5])

        private_mean = dp.private_mean(data)

        # Private mean should be close to true mean (2.0)
        # Allow for noise
        assert abs(private_mean - 3.0) < 5.0  # Very loose bound due to noise

    def test_private_variance(self):
        """Test private variance computation"""
        dp = DifferentialPrivacy(epsilon=1.0)
        data = np.array([1, 2, 3, 4, 5])

        private_var = dp.private_variance(data)

        # Should return a positive value
        assert private_var > 0

    def test_private_count(self):
        """Test private count computation"""
        dp = DifferentialPrivacy(epsilon=1.0)
        data = np.array([1, 2, 3, 4, 5])

        private_count = dp.private_count(data)

        # Count should be close to 5
        assert abs(private_count - 5) < 10  # Allow for noise

    def test_privatize_dataframe_columns(self, sample_patients):
        """Test that privatize_dataframe preserves columns"""
        dp = DifferentialPrivacy(epsilon=1.0)

        private_df = dp.privatize_dataframe(
            sample_patients,
            numeric_columns=['age', 'income']
        )

        # Should have same columns
        assert list(private_df.columns) == list(sample_patients.columns)

    def test_privatize_dataframe_shape(self, sample_patients):
        """Test that privatize_dataframe preserves shape"""
        dp = DifferentialPrivacy(epsilon=1.0)

        private_df = dp.privatize_dataframe(
            sample_patients,
            numeric_columns=['age', 'income']
        )

        # Should have same shape
        assert private_df.shape == sample_patients.shape

    def test_privatize_numeric_columns(self, sample_patients):
        """Test that numeric columns are actually modified"""
        dp = DifferentialPrivacy(epsilon=1.0)

        private_df = dp.privatize_dataframe(
            sample_patients,
            numeric_columns=['age', 'income']
        )

        # At least some values should be different
        assert not private_df['age'].equals(sample_patients['age'])
        assert not private_df['income'].equals(sample_patients['income'])

    def test_non_privatized_columns_unchanged(self, sample_patients):
        """Test that non-privatized columns remain unchanged"""
        dp = DifferentialPrivacy(epsilon=1.0)

        private_df = dp.privatize_dataframe(
            sample_patients,
            numeric_columns=['age']
        )

        # Patient IDs should be unchanged
        assert private_df['patient_id'].equals(sample_patients['patient_id'])

    def test_randomized_response_categorical(self):
        """Test randomized response for categorical data"""
        dp = DifferentialPrivacy(epsilon=1.0)
        data = pd.Series(['A', 'B', 'A', 'B', 'A'] * 20)

        private_data = dp.randomized_response(data, categories=['A', 'B'])

        # Result should only contain valid categories
        assert set(private_data.unique()).issubset({'A', 'B'})
        # Should have same length
        assert len(private_data) == len(data)

    def test_epsilon_sensitivity(self):
        """Test that smaller epsilon adds more noise"""
        data = np.array([100.0] * 100)

        dp_high_privacy = DifferentialPrivacy(epsilon=0.1)
        dp_low_privacy = DifferentialPrivacy(epsilon=10.0)

        noisy_high = dp_high_privacy.add_laplace_noise(data, sensitivity=1.0)
        noisy_low = dp_low_privacy.add_laplace_noise(data, sensitivity=1.0)

        # Higher privacy (lower epsilon) should have more variance
        var_high = np.var(noisy_high - data)
        var_low = np.var(noisy_low - data)

        assert var_high > var_low

    @pytest.mark.parametrize("epsilon", [0.1, 0.5, 1.0, 5.0, 10.0])
    def test_various_epsilon_values(self, epsilon):
        """Test privacy with various epsilon values"""
        dp = DifferentialPrivacy(epsilon=epsilon)
        data = np.array([1, 2, 3, 4, 5])

        private_mean = dp.private_mean(data)

        # Should complete without error
        assert isinstance(private_mean, (int, float))

    def test_invalid_epsilon(self):
        """Test that invalid epsilon raises error"""
        with pytest.raises(ValueError):
            DifferentialPrivacy(epsilon=0)

        with pytest.raises(ValueError):
            DifferentialPrivacy(epsilon=-1)

    def test_invalid_delta(self):
        """Test that invalid delta raises error"""
        with pytest.raises(ValueError):
            DifferentialPrivacy(epsilon=1.0, delta=0)

        with pytest.raises(ValueError):
            DifferentialPrivacy(epsilon=1.0, delta=-1)

        with pytest.raises(ValueError):
            DifferentialPrivacy(epsilon=1.0, delta=1.0)  # delta must be < 1
