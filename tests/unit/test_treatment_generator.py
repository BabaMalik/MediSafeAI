"""
Unit tests for TreatmentGenerator
"""

import pytest
import pandas as pd
from src.data_generator.treatment_generator import TreatmentGenerator
from src.data_generator.patient_generator import PatientGenerator


class TestTreatmentGenerator:
    """Test cases for TreatmentGenerator"""

    def test_init(self):
        """Test TreatmentGenerator initialization"""
        gen = TreatmentGenerator()
        assert 'diabetes' in gen.treatments
        assert 'hypertension' in gen.treatments
        assert 'heart_disease' in gen.treatments

    def test_assign_treatments_diabetic(self):
        """Test treatment assignment for diabetic patient"""
        gen = TreatmentGenerator()
        patient = {'diabetes': 1, 'hypertension': 0, 'heart_disease': 0}
        result = gen.assign_treatments(patient)

        assert 'diabetes_treatment' in result
        assert result['diabetes_treatment'] in gen.treatments['diabetes']

    def test_assign_treatments_hypertensive(self):
        """Test treatment assignment for hypertensive patient"""
        gen = TreatmentGenerator()
        patient = {'diabetes': 0, 'hypertension': 1, 'heart_disease': 0}
        result = gen.assign_treatments(patient)

        assert 'hypertension_treatment' in result
        assert result['hypertension_treatment'] in gen.treatments['hypertension']

    def test_assign_treatments_heart_disease(self):
        """Test treatment assignment for heart disease patient"""
        gen = TreatmentGenerator()
        patient = {'diabetes': 0, 'hypertension': 0, 'heart_disease': 1}
        result = gen.assign_treatments(patient)

        assert 'heart_disease_treatment' in result
        assert result['heart_disease_treatment'] in gen.treatments['heart_disease']

    def test_assign_treatments_healthy(self):
        """Test that healthy patient gets no condition-specific treatments"""
        gen = TreatmentGenerator()
        patient = {'diabetes': 0, 'hypertension': 0, 'heart_disease': 0}
        result = gen.assign_treatments(patient)

        assert 'diabetes_treatment' not in result
        assert 'hypertension_treatment' not in result
        assert 'heart_disease_treatment' not in result

    def test_assign_treatments_multiple_conditions(self):
        """Test treatment assignment for patient with multiple conditions"""
        gen = TreatmentGenerator()
        patient = {'diabetes': 1, 'hypertension': 1, 'heart_disease': 1}
        result = gen.assign_treatments(patient)

        assert 'diabetes_treatment' in result
        assert 'hypertension_treatment' in result
        assert 'heart_disease_treatment' in result

    def test_assign_treatments_with_visit_date(self):
        """Test that visit_date is included when provided"""
        gen = TreatmentGenerator()
        patient = {'diabetes': 1, 'hypertension': 0, 'heart_disease': 0}
        result = gen.assign_treatments(patient, visit_date='2025-01-01')

        assert result['visit_date'] == '2025-01-01'

    def test_generate_treatments_batch(self, small_patients):
        """Test batch treatment generation"""
        gen = TreatmentGenerator()
        treatments_df = gen.generate_treatments(small_patients)

        assert isinstance(treatments_df, pd.DataFrame)
        assert len(treatments_df) == len(small_patients)
        assert 'patient_id' in treatments_df.columns
        assert 'treatments' in treatments_df.columns

    def test_generate_treatments_returns_lists(self, small_patients):
        """Test that treatments column contains lists"""
        gen = TreatmentGenerator()
        treatments_df = gen.generate_treatments(small_patients)

        for treatments in treatments_df['treatments']:
            assert isinstance(treatments, list)
            assert len(treatments) > 0  # At least 'none' for healthy patients

    def test_healthy_patient_gets_none_treatment(self):
        """Test that a patient with no conditions gets ['none']"""
        gen = TreatmentGenerator()
        patients_df = pd.DataFrame([{
            'patient_id': 'PT000001',
            'diabetes': 0,
            'hypertension': 0,
            'heart_disease': 0
        }])
        treatments_df = gen.generate_treatments(patients_df)

        assert treatments_df.iloc[0]['treatments'] == ['none']

    def test_patient_ids_match(self, small_patients):
        """Test that patient IDs in treatments match input"""
        gen = TreatmentGenerator()
        treatments_df = gen.generate_treatments(small_patients)

        assert set(treatments_df['patient_id']) == set(small_patients['patient_id'])
