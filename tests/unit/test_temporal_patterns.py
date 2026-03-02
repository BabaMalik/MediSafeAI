"""
Unit tests for TemporalPatternGenerator
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.data_generator.temporal_patterns import TemporalPatternGenerator


@pytest.fixture
def sample_time_series():
    """Create a sample time series DataFrame"""
    dates = [datetime(2025, 1, 1) + timedelta(days=30 * i) for i in range(12)]
    return pd.DataFrame({
        'visit_date': dates,
        'blood_glucose': [100.0] * 12,
        'systolic_bp': [120.0] * 12,
    })


class TestTemporalPatternGenerator:
    """Test cases for TemporalPatternGenerator"""

    def test_init_default(self):
        """Test default initialization"""
        gen = TemporalPatternGenerator()
        assert gen.anomaly_rate == 0.1

    def test_init_custom(self):
        """Test custom anomaly rate"""
        gen = TemporalPatternGenerator(anomaly_rate=0.2)
        assert gen.anomaly_rate == 0.2

    def test_apply_increasing_trend(self, sample_time_series):
        """Test that increasing trend raises values over time"""
        gen = TemporalPatternGenerator()
        result = gen.apply_trends(sample_time_series, 'blood_glucose', trend='increase')

        assert isinstance(result, pd.DataFrame)
        # Last value should generally be higher than first
        assert result['blood_glucose'].iloc[-1] > result['blood_glucose'].iloc[0]

    def test_apply_decreasing_trend(self, sample_time_series):
        """Test that decreasing trend lowers values over time"""
        gen = TemporalPatternGenerator()
        result = gen.apply_trends(sample_time_series, 'blood_glucose', trend='decrease')

        assert isinstance(result, pd.DataFrame)
        # Last value should generally be lower than first
        assert result['blood_glucose'].iloc[-1] < result['blood_glucose'].iloc[0]

    def test_trend_preserves_shape(self, sample_time_series):
        """Test that trends preserve DataFrame shape"""
        gen = TemporalPatternGenerator()
        result = gen.apply_trends(sample_time_series, 'blood_glucose')
        assert result.shape == sample_time_series.shape

    def test_trend_preserves_other_columns(self, sample_time_series):
        """Test that trends don't modify other columns"""
        gen = TemporalPatternGenerator()
        result = gen.apply_trends(sample_time_series, 'blood_glucose')
        pd.testing.assert_series_equal(result['systolic_bp'], sample_time_series['systolic_bp'])

    def test_inject_anomalies(self, sample_time_series):
        """Test anomaly injection"""
        gen = TemporalPatternGenerator(anomaly_rate=0.5)  # High rate for testing
        original_values = sample_time_series['blood_glucose'].copy()
        result = gen.inject_anomalies(sample_time_series, ['blood_glucose'])

        # At least some values should be different (anomalies injected)
        assert not result['blood_glucose'].equals(original_values)

    def test_inject_anomalies_increases_values(self, sample_time_series):
        """Test that anomalies spike values upward (multiplier > 1)"""
        gen = TemporalPatternGenerator(anomaly_rate=1.0)  # All points anomalous
        result = gen.inject_anomalies(sample_time_series.copy(), ['blood_glucose'])

        # All values should be increased (multiplied by 1.5-2.5)
        assert (result['blood_glucose'] >= sample_time_series['blood_glucose']).all()

    def test_inject_anomalies_preserves_shape(self, sample_time_series):
        """Test that anomaly injection preserves shape"""
        gen = TemporalPatternGenerator()
        result = gen.inject_anomalies(sample_time_series, ['blood_glucose'])
        assert result.shape == sample_time_series.shape

    def test_inject_anomalies_skips_missing_columns(self, sample_time_series):
        """Test that missing columns are safely skipped"""
        gen = TemporalPatternGenerator()
        result = gen.inject_anomalies(sample_time_series, ['nonexistent_column'])
        pd.testing.assert_frame_equal(result, sample_time_series)

    def test_cyclic_patterns(self, sample_time_series):
        """Test adding cyclic patterns"""
        gen = TemporalPatternGenerator()
        result = gen.add_cyclic_patterns(
            sample_time_series, 'blood_glucose',
            amplitude=5, period_days=90
        )

        assert isinstance(result, pd.DataFrame)
        # Values should vary around the original
        assert not result['blood_glucose'].equals(sample_time_series['blood_glucose'])

    def test_cyclic_patterns_amplitude(self, sample_time_series):
        """Test that cyclic pattern respects amplitude"""
        gen = TemporalPatternGenerator()
        amplitude = 10.0
        result = gen.add_cyclic_patterns(
            sample_time_series, 'blood_glucose',
            amplitude=amplitude, period_days=90
        )

        max_diff = abs(result['blood_glucose'] - sample_time_series['blood_glucose']).max()
        assert max_diff <= amplitude + 0.01  # Allow small floating point error

    def test_multiple_metrics_anomalies(self, sample_time_series):
        """Test injecting anomalies into multiple metrics"""
        gen = TemporalPatternGenerator(anomaly_rate=0.5)
        original_glucose = sample_time_series['blood_glucose'].copy()
        original_bp = sample_time_series['systolic_bp'].copy()
        result = gen.inject_anomalies(sample_time_series, ['blood_glucose', 'systolic_bp'])

        # At least one column should be modified
        changed_glucose = not result['blood_glucose'].equals(original_glucose)
        changed_bp = not result['systolic_bp'].equals(original_bp)
        assert changed_glucose or changed_bp
