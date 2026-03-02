# src/data_generator/vitals_generator.py

import numpy as np
import pandas as pd


class VitalsGenerator:
    """Generates synthetic vital signs for a given patient"""

    def __init__(self, seed=None):
        if seed is not None:
            np.random.seed(seed)

    def generate_vitals(self, patient_data) -> pd.DataFrame:
        """Generate vitals - handles both dict and DataFrame input"""
        # If it's a DataFrame, use the batch method
        if isinstance(patient_data, pd.DataFrame):
            return self.generate_vitals_for_patients(patient_data)

        # Otherwise treat as single patient dict
        return self._generate_single_vitals(patient_data)

    def _generate_single_vitals(self, patient_data: dict) -> dict:
        age = patient_data.get('age', 40)
        has_hypertension = patient_data.get('hypertension', 0)
        has_heart_disease = patient_data.get('heart_disease', 0)
        has_diabetes = patient_data.get('diabetes', 0)

        return {
            'blood_pressure_systolic': np.random.normal(130 if has_hypertension else 120, 10),
            'blood_pressure_diastolic': np.random.normal(85 if has_hypertension else 75, 7),
            'heart_rate': np.random.normal(80 if has_heart_disease else 70, 5),
            'blood_glucose': np.random.normal(180 if has_diabetes else 100, 20),
            'cholesterol': np.random.normal(220 if has_heart_disease else 180, 15),
            'body_temperature': np.random.normal(98.6, 0.7),
            'respiratory_rate': np.random.normal(18, 2),
            'oxygen_saturation': np.random.normal(96, 2),
            'weight': np.random.normal(70, 15) - (age * 0.1)
        }

    def generate_vitals_df(self, patient_data: dict, n_records=10) -> pd.DataFrame:
        return pd.DataFrame([self._generate_single_vitals(patient_data) for _ in range(n_records)])

    def generate_vitals_for_patients(self, patients_df: pd.DataFrame) -> pd.DataFrame:
        """Generate vitals for a DataFrame of patients"""
        vitals_list = []

        for idx, patient in patients_df.iterrows():
            patient_dict = patient.to_dict()
            vitals = self._generate_single_vitals(patient_dict)
            vitals['patient_id'] = patient_dict.get('patient_id', f'PT{idx:06d}')
            vitals_list.append(vitals)

        vitals_df = pd.DataFrame(vitals_list)

        # Reorder columns to have patient_id first
        cols = ['patient_id'] + [col for col in vitals_df.columns if col != 'patient_id']
        return vitals_df[cols]
