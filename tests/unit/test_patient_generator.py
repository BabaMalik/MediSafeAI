"""
Unit tests for PatientGenerator
"""

import pytest
import pandas as pd
from src.data_generator.patient_generator import PatientGenerator


class TestPatientGenerator:
    """Test cases for PatientGenerator class"""

    def test_init(self):
        """Test PatientGenerator initialization"""
        generator = PatientGenerator(num_patients=100, seed=42)
        assert generator.num_patients == 100
        assert generator.seed == 42

    def test_generate_patients_count(self):
        """Test that correct number of patients are generated"""
        num_patients = 50
        generator = PatientGenerator(num_patients=num_patients, seed=42)
        df = generator.generate_patients()

        assert len(df) == num_patients

    def test_generate_patients_columns(self):
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
        """Test patient ID format (PT000000)"""
        generator = PatientGenerator(num_patients=10, seed=42)
        df = generator.generate_patients()

        for patient_id in df['patient_id']:
            assert patient_id.startswith('PT')
            assert len(patient_id) == 8

    def test_gender_values(self):
        """Test that gender only contains M or F"""
        generator = PatientGenerator(num_patients=100, seed=42)
        df = generator.generate_patients()

        assert set(df['gender'].unique()).issubset({'M', 'F'})

    def test_age_ranges(self):
        """Test that ages are within valid ranges"""
        generator = PatientGenerator(num_patients=100, seed=42)
        df = generator.generate_patients()

        assert (df['age'] >= 0).all()
        assert (df['age'] <= 120).all()

    def test_zip_code_format(self):
        """Test ZIP code format (5 digits)"""
        generator = PatientGenerator(num_patients=10, seed=42)
        df = generator.generate_patients()

        for zip_code in df['zip_code']:
            assert len(str(zip_code)) == 5
            assert str(zip_code).isdigit()

    def test_income_positive(self):
        """Test that income values are positive"""
        generator = PatientGenerator(num_patients=100, seed=42)
        df = generator.generate_patients()

        assert (df['income'] > 0).all()

    def test_insurance_types(self):
        """Test that insurance types are valid"""
        generator = PatientGenerator(num_patients=100, seed=42)
        df = generator.generate_patients()

        valid_insurance = {'Private', 'Medicare', 'Medicaid', 'Uninsured'}
        assert set(df['insurance'].unique()).issubset(valid_insurance)

    def test_boolean_conditions(self):
        """Test that conditions are boolean"""
        generator = PatientGenerator(num_patients=100, seed=42)
        df = generator.generate_patients()

        assert df['diabetes'].dtype == bool
        assert df['hypertension'].dtype == bool
        assert df['heart_disease'].dtype == bool

    def test_reproducibility_with_seed(self):
        """Test that same seed produces same results"""
        generator1 = PatientGenerator(num_patients=10, seed=42)
        df1 = generator1.generate_patients()

        generator2 = PatientGenerator(num_patients=10, seed=42)
        df2 = generator2.generate_patients()

        pd.testing.assert_frame_equal(df1, df2)

    def test_different_results_without_seed(self):
        """Test that different generators produce different results"""
        generator1 = PatientGenerator(num_patients=10, seed=None)
        df1 = generator1.generate_patients()

        generator2 = PatientGenerator(num_patients=10, seed=None)
        df2 = generator2.generate_patients()

        # Patient IDs should be different
        assert not df1['patient_id'].equals(df2['patient_id'])

    def test_age_distribution(self):
        """Test that age distribution is reasonable"""
        generator = PatientGenerator(num_patients=1000, seed=42)
        df = generator.generate_patients()

        # Mean age should be in reasonable range (30-60)
        mean_age = df['age'].mean()
        assert 30 <= mean_age <= 60

    def test_no_missing_values(self):
        """Test that there are no missing values"""
        generator = PatientGenerator(num_patients=100, seed=42)
        df = generator.generate_patients()

        assert not df.isnull().any().any()

    @pytest.mark.parametrize("num_patients", [1, 10, 100, 1000])
    def test_various_patient_counts(self, num_patients):
        """Test generation with various patient counts"""
        generator = PatientGenerator(num_patients=num_patients, seed=42)
        df = generator.generate_patients()

        assert len(df) == num_patients
