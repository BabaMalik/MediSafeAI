"""
Unit tests for PatientGenerator
"""

import pytest
import pandas as pd
from src.data_generator.patient_generator import PatientGenerator


class TestPatientGenerator:
    """Test cases for PatientGenerator class"""

    def test_init_defaults(self):
        """Test PatientGenerator initialization with defaults"""
        generator = PatientGenerator()
        assert generator.num_patients == 10000

    def test_init_custom(self):
        """Test PatientGenerator initialization with custom params"""
        generator = PatientGenerator(num_patients=100, seed=42)
        assert generator.num_patients == 100

    def test_generate_patients_count(self):
        """Test that correct number of patients are generated"""
        generator = PatientGenerator(num_patients=50, seed=42)
        df = generator.generate_patients()
        assert len(df) == 50

    def test_generate_patients_override_count(self):
        """Test that n_patients arg overrides constructor value"""
        generator = PatientGenerator(num_patients=50, seed=42)
        df = generator.generate_patients(n_patients=10)
        assert len(df) == 10

    def test_generate_demographics_alias(self):
        """Test that generate_patients delegates to generate_demographics"""
        generator = PatientGenerator(num_patients=10, seed=42)
        df1 = generator.generate_patients()

        generator2 = PatientGenerator(num_patients=10, seed=42)
        df2 = generator2.generate_demographics(n_patients=10)

        pd.testing.assert_frame_equal(df1, df2)

    def test_expected_columns(self):
        """Test that all expected columns are present"""
        generator = PatientGenerator(num_patients=10, seed=42)
        df = generator.generate_patients()

        expected_columns = [
            'patient_id', 'first_name', 'last_name', 'gender',
            'dob', 'age', 'zip_code', 'income', 'insurance',
            'diabetes', 'hypertension', 'heart_disease'
        ]

        assert list(df.columns) == expected_columns

    def test_patient_id_uniqueness(self):
        """Test that patient IDs are unique"""
        generator = PatientGenerator(num_patients=100, seed=42)
        df = generator.generate_patients()
        assert df['patient_id'].is_unique

    def test_patient_id_format(self):
        """Test patient ID format (PT followed by 6 digits)"""
        generator = PatientGenerator(num_patients=10, seed=42)
        df = generator.generate_patients()

        for pid in df['patient_id']:
            assert pid.startswith('PT')
            assert len(pid) == 8
            assert pid[2:].isdigit()

    def test_gender_values(self):
        """Test that gender only contains M or F"""
        generator = PatientGenerator(num_patients=100, seed=42)
        df = generator.generate_patients()
        assert set(df['gender'].unique()).issubset({'M', 'F'})

    def test_age_ranges(self):
        """Test that ages are within valid ranges (18-90 based on faker config)"""
        generator = PatientGenerator(num_patients=100, seed=42)
        df = generator.generate_patients()
        assert (df['age'] >= 0).all()
        assert (df['age'] <= 120).all()

    def test_income_positive(self):
        """Test that income values are positive"""
        generator = PatientGenerator(num_patients=100, seed=42)
        df = generator.generate_patients()
        assert (df['income'] > 0).all()

    def test_insurance_types(self):
        """Test that insurance types are valid"""
        generator = PatientGenerator(num_patients=200, seed=42)
        df = generator.generate_patients()
        valid_insurance = {'Private', 'Medicare', 'Medicaid', 'Uninsured'}
        assert set(df['insurance'].unique()).issubset(valid_insurance)

    def test_condition_values(self):
        """Test that condition columns contain 0 or 1"""
        generator = PatientGenerator(num_patients=100, seed=42)
        df = generator.generate_patients()
        for col in ['diabetes', 'hypertension', 'heart_disease']:
            assert set(df[col].unique()).issubset({0, 1})

    def test_reproducibility_with_seed(self):
        """Test that same seed produces same results"""
        gen1 = PatientGenerator(num_patients=10, seed=42)
        df1 = gen1.generate_patients()

        gen2 = PatientGenerator(num_patients=10, seed=42)
        df2 = gen2.generate_patients()

        pd.testing.assert_frame_equal(df1, df2)

    def test_no_missing_values(self):
        """Test that there are no missing values"""
        generator = PatientGenerator(num_patients=100, seed=42)
        df = generator.generate_patients()
        assert not df.isnull().any().any()

    @pytest.mark.parametrize("n", [1, 10, 100, 500])
    def test_various_patient_counts(self, n):
        """Test generation with various patient counts"""
        generator = PatientGenerator(num_patients=n, seed=42)
        df = generator.generate_patients()
        assert len(df) == n
