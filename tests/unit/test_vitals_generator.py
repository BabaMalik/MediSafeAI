"""
Unit tests for VitalsGenerator
"""

import pytest
import pandas as pd
from src.data_generator.vitals_generator import VitalsGenerator
from src.data_generator.patient_generator import PatientGenerator


class TestVitalsGenerator:
    """Test cases for VitalsGenerator"""

    def test_init(self):
        """Test VitalsGenerator initialization"""
        gen = VitalsGenerator(seed=42)
        assert gen is not None

    def test_single_patient_vitals(self, sample_patient_record):
        """Test generating vitals for a single patient dict"""
        gen = VitalsGenerator(seed=42)
        vitals = gen.generate_vitals(sample_patient_record)
        assert isinstance(vitals, dict)
        assert 'blood_pressure_systolic' in vitals
        assert 'heart_rate' in vitals
        assert 'blood_glucose' in vitals

    def test_batch_vitals(self, small_patients):
        """Test generating vitals for a DataFrame of patients"""
        gen = VitalsGenerator(seed=42)
        vitals_df = gen.generate_vitals(small_patients)

        assert isinstance(vitals_df, pd.DataFrame)
        assert len(vitals_df) == len(small_patients)
        assert 'patient_id' in vitals_df.columns

    def test_vitals_columns(self, small_patients):
        """Test that all expected vital sign columns are present"""
        gen = VitalsGenerator(seed=42)
        vitals_df = gen.generate_vitals(small_patients)

        expected = [
            'patient_id', 'blood_pressure_systolic', 'blood_pressure_diastolic',
            'heart_rate', 'blood_glucose', 'cholesterol', 'body_temperature',
            'respiratory_rate', 'oxygen_saturation', 'weight'
        ]
        for col in expected:
            assert col in vitals_df.columns, f"Missing column: {col}"

    def test_blood_pressure_ranges(self, small_patients):
        """Test that blood pressure values are physiologically reasonable"""
        gen = VitalsGenerator(seed=42)
        vitals_df = gen.generate_vitals(small_patients)

        assert (vitals_df['blood_pressure_systolic'] > 50).all()
        assert (vitals_df['blood_pressure_systolic'] < 250).all()
        assert (vitals_df['blood_pressure_diastolic'] > 30).all()
        assert (vitals_df['blood_pressure_diastolic'] < 150).all()

    def test_heart_rate_ranges(self, small_patients):
        """Test that heart rate values are reasonable"""
        gen = VitalsGenerator(seed=42)
        vitals_df = gen.generate_vitals(small_patients)

        assert (vitals_df['heart_rate'] > 30).all()
        assert (vitals_df['heart_rate'] < 150).all()

    def test_hypertensive_patients_higher_bp(self):
        """Test that hypertensive patients have higher blood pressure on average"""
        gen = VitalsGenerator(seed=42)

        normal = {'age': 40, 'hypertension': 0, 'heart_disease': 0, 'diabetes': 0}
        hyper = {'age': 40, 'hypertension': 1, 'heart_disease': 0, 'diabetes': 0}

        # Generate many samples to test statistical difference
        normal_bps = [gen._generate_single_vitals(normal)['blood_pressure_systolic'] for _ in range(100)]
        hyper_bps = [gen._generate_single_vitals(hyper)['blood_pressure_systolic'] for _ in range(100)]

        assert sum(hyper_bps) / len(hyper_bps) > sum(normal_bps) / len(normal_bps)

    def test_diabetic_patients_higher_glucose(self):
        """Test that diabetic patients have higher blood glucose on average"""
        gen = VitalsGenerator(seed=42)

        normal = {'age': 40, 'hypertension': 0, 'heart_disease': 0, 'diabetes': 0}
        diabetic = {'age': 40, 'hypertension': 0, 'heart_disease': 0, 'diabetes': 1}

        normal_glucose = [gen._generate_single_vitals(normal)['blood_glucose'] for _ in range(100)]
        diabetic_glucose = [gen._generate_single_vitals(diabetic)['blood_glucose'] for _ in range(100)]

        assert sum(diabetic_glucose) / len(diabetic_glucose) > sum(normal_glucose) / len(normal_glucose)

    def test_generate_vitals_df(self):
        """Test generating multiple vitals records for one patient"""
        gen = VitalsGenerator(seed=42)
        patient = {'age': 40, 'hypertension': 0, 'heart_disease': 0, 'diabetes': 0}
        df = gen.generate_vitals_df(patient, n_records=10)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10

    def test_patient_ids_match(self, small_patients):
        """Test that patient IDs in vitals match input patients"""
        gen = VitalsGenerator(seed=42)
        vitals_df = gen.generate_vitals(small_patients)

        assert set(vitals_df['patient_id']) == set(small_patients['patient_id'])
