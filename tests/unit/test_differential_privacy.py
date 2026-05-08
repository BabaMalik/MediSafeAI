"""
Unit tests for DifferentialPrivacy module
"""

import pytest
import pandas as pd
import numpy as np
from src.privacy.differential_privacy import DifferentialPrivacy


class TestDifferentialPrivacy:
    """Test cases for DifferentialPrivacy class"""

    def test_init_defaults(self):
        """Test DifferentialPrivacy initialization with defaults"""
        dp = DifferentialPrivacy()
        assert dp.epsilon == 1.0
        assert dp.delta == 1e-5

    def test_init_custom(self):
        """Test DifferentialPrivacy initialization with custom params"""
        dp = DifferentialPrivacy(epsilon=0.5, delta=1e-6)
        assert dp.epsilon == 0.5
        assert dp.delta == 1e-6

    def test_privatize_dataframe_preserves_columns(self, sample_patients):
        """Test that privatize_dataframe preserves all columns"""
        dp = DifferentialPrivacy()
        numeric_cols = ['age', 'income']
        private_df = dp.privatize_dataframe(sample_patients, numeric_columns=numeric_cols)

        assert list(private_df.columns) == list(sample_patients.columns)

    def test_privatize_dataframe_preserves_shape(self, sample_patients):
        """Test that privatize_dataframe preserves DataFrame shape"""
        dp = DifferentialPrivacy()
        numeric_cols = ['age', 'income']
        private_df = dp.privatize_dataframe(sample_patients, numeric_columns=numeric_cols)

        assert private_df.shape == sample_patients.shape

    def test_privatize_modifies_numeric_columns(self, sample_patients):
        """Test that noise is actually added to numeric columns"""
        dp = DifferentialPrivacy(epsilon=0.1) # Small epsilon = lots of noise
        numeric_cols = ['age', 'income']
        private_df = dp.privatize_dataframe(sample_patients, numeric_columns=numeric_cols)

        for col in numeric_cols:
            assert not private_df[col].equals(sample_patients[col])

    def test_epsilon_affects_noise_magnitude(self, sample_patients):
        """Test that smaller epsilon produces larger noise (on average)"""
        # We'll use a large dataset and check mean absolute difference
        numeric_cols = ['age']

        dp_strong = DifferentialPrivacy(epsilon=0.01) # Strong privacy, more noise
        dp_weak = DifferentialPrivacy(epsilon=10.0)   # Weak privacy, less noise

        df_strong = dp_strong.privatize_dataframe(sample_patients, numeric_columns=numeric_cols)
        df_weak = dp_weak.privatize_dataframe(sample_patients, numeric_cols)

        noise_strong = (df_strong['age'] - sample_patients['age']).abs().mean()
        noise_weak = (df_weak['age'] - sample_patients['age']).abs().mean()

        assert noise_strong > noise_weak

    def test_private_mean(self):
        """Test private mean computation"""
        data = np.random.normal(100, 10, 1000)
        dp = DifferentialPrivacy(epsilon=1.0)

        true_mean = data.mean()
        private_mean = dp.private_mean(data)

        # Private mean should be "close" to true mean
        assert abs(private_mean - true_mean) < 5.0

    def test_invalid_epsilon(self):
        """Test that invalid epsilon raises error"""
        with pytest.raises(ValueError):
            DifferentialPrivacy(epsilon=0)
        with pytest.raises(ValueError):
            DifferentialPrivacy(epsilon=-1)

    def test_invalid_delta(self):
        """Test that invalid delta raises error"""
        with pytest.raises(ValueError):
            DifferentialPrivacy(delta=1.0)
        with pytest.raises(ValueError):
            DifferentialPrivacy(delta=1.5)
        with pytest.raises(ValueError):
            DifferentialPrivacy(delta=-0.1)
