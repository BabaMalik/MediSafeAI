"""
Unit tests for DiseaseProgressionModel
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.data_generator.disease_progression import DiseaseProgressionModel


class TestDiseaseProgressionModel:
    """Test cases for DiseaseProgressionModel"""

    def test_init_defaults(self):
        """Test default initialization"""
        model = DiseaseProgressionModel()
        assert model.base_deterioration_rate == 0.03
        assert model.intervention_effectiveness == 0.7

    def test_init_custom(self):
        """Test custom initialization"""
        model = DiseaseProgressionModel(base_deterioration_rate=0.05, intervention_effectiveness=0.5)
        assert model.base_deterioration_rate == 0.05
        assert model.intervention_effectiveness == 0.5

    def test_simulate_with_num_visits(self, sample_patient_record):
        """Test simulation using num_visits parameter"""
        model = DiseaseProgressionModel()
        df = model.simulate_progression(
            sample_patient_record,
            num_visits=6,
            time_interval_days=30
        )

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 6

    def test_simulate_with_dates(self, sample_patient_record):
        """Test simulation using start_date and end_date"""
        model = DiseaseProgressionModel()
        start = datetime.now().date()
        end = start + timedelta(days=150)

        df = model.simulate_progression(
            sample_patient_record,
            start_date=start,
            end_date=end,
            visit_interval_days=30
        )

        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 5  # ~150 days / 30 days per visit

    def test_output_columns(self, sample_patient_record):
        """Test that output contains expected columns"""
        model = DiseaseProgressionModel()
        df = model.simulate_progression(
            sample_patient_record,
            num_visits=6,
            time_interval_days=30
        )

        assert 'patient_id' in df.columns
        assert 'visit_date' in df.columns
        assert 'visit_number' in df.columns
        assert 'blood_pressure_systolic' in df.columns
        assert 'blood_glucose' in df.columns
        assert 'cholesterol' in df.columns
        assert 'heart_rate' in df.columns

    def test_patient_id_preserved(self, sample_patient_record):
        """Test that patient_id is preserved in output"""
        model = DiseaseProgressionModel()
        df = model.simulate_progression(
            sample_patient_record,
            num_visits=3,
            time_interval_days=30
        )

        assert (df['patient_id'] == sample_patient_record['patient_id']).all()

    def test_visit_numbers_sequential(self, sample_patient_record):
        """Test that visit numbers are sequential"""
        model = DiseaseProgressionModel()
        df = model.simulate_progression(
            sample_patient_record,
            num_visits=6,
            time_interval_days=30
        )

        expected = list(range(1, len(df) + 1))
        assert list(df['visit_number']) == expected

    def test_diabetic_patient_has_a1c(self):
        """Test that diabetic patients get HbA1c measurements"""
        patient = {
            'patient_id': 'PT000001', 'age': 50,
            'diabetes': 1, 'hypertension': 0, 'heart_disease': 0
        }
        model = DiseaseProgressionModel()
        df = model.simulate_progression(patient, num_visits=3, time_interval_days=30)

        assert 'hemoglobin_a1c' in df.columns
        assert (df['hemoglobin_a1c'] > 5.0).all()

    def test_heart_disease_patient_has_ejection_fraction(self):
        """Test that heart disease patients get ejection fraction"""
        patient = {
            'patient_id': 'PT000001', 'age': 60,
            'diabetes': 0, 'hypertension': 0, 'heart_disease': 1
        }
        model = DiseaseProgressionModel()
        df = model.simulate_progression(patient, num_visits=3, time_interval_days=30)

        assert 'ejection_fraction' in df.columns
        assert 'troponin' in df.columns

    def test_hypertensive_patient_higher_bp(self):
        """Test that hypertensive patients start with higher blood pressure"""
        model = DiseaseProgressionModel()

        normal = {
            'patient_id': 'PT000001', 'age': 50,
            'diabetes': 0, 'hypertension': 0, 'heart_disease': 0
        }
        hyper = {
            'patient_id': 'PT000002', 'age': 50,
            'diabetes': 0, 'hypertension': 1, 'heart_disease': 0
        }

        df_normal = model.simulate_progression(normal, num_visits=1, time_interval_days=30)
        df_hyper = model.simulate_progression(hyper, num_visits=1, time_interval_days=30)

        # Hypertensive patient should have higher baseline BP
        assert df_hyper['blood_pressure_systolic'].iloc[0] > df_normal['blood_pressure_systolic'].iloc[0]

    def test_intervention_column(self, sample_patient_record):
        """Test that intervention column is present"""
        model = DiseaseProgressionModel()
        df = model.simulate_progression(
            sample_patient_record,
            num_visits=12,
            time_interval_days=30
        )

        assert 'intervention_occurred' in df.columns
        assert 'intervention_type' in df.columns

        # Allowed intervention types in the simulation
        allowed_types = {'major', 'minor'}

        # Get actual values from the dataframe
        current_types = set(df['intervention_type'].unique())

        # Remove None/NaN from actual values
        current_types_filtered = {x for x in current_types if pd.notna(x)}

        # Verify that all actual types are within the allowed set
        assert current_types_filtered.issubset(allowed_types)

        # Verify intervention_occurred matches intervention_type presence
        for _, row in df.iterrows():
            if pd.notna(row['intervention_type']):
                assert row['intervention_occurred'] is True
            else:
                assert row['intervention_occurred'] is False

    def test_time_interval_days_alias(self, sample_patient_record):
        """Test that time_interval_days works as alias for visit_interval_days"""
        model = DiseaseProgressionModel()
        df = model.simulate_progression(
            sample_patient_record,
            num_visits=3,
            time_interval_days=60
        )

        dates = pd.to_datetime(df['visit_date'])
        if len(dates) > 1:
            diff = (dates.iloc[1] - dates.iloc[0]).days
            assert diff == 60

    def test_simulate_progression_by_visits(self, sample_patient_record):
        """Test the convenience wrapper method"""
        model = DiseaseProgressionModel()
        df = model.simulate_progression_by_visits(
            sample_patient_record,
            num_visits=6,
            time_interval_days=30
        )

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 6
