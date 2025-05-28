# src/data_generator/vitals_generator.py

import numpy as np
import pandas as pd


class VitalsGenerator:
    """Generates synthetic vital signs for a given patient"""

    def __init__(self, seed=None):
        if seed is not None:
            np.random.seed(seed)

    def generate_vitals(self, patient_data: dict) -> dict:
        age = patient_data.get('age', 40)
        has_hypertension = patient_data.get('hypertension', 0)
        has_heart_disease = patient_data.get('heart_disease', 0)
        has_diabetes = patient_data.get('diabetes', 0)

        return {
            'systolic_bp': np.random.normal(130 if has_hypertension else 120, 10),
            'diastolic_bp': np.random.normal(85 if has_hypertension else 75, 7),
            'heart_rate': np.random.normal(80 if has_heart_disease else 70, 5),
            'blood_glucose': np.random.normal(180 if has_diabetes else 100, 20),
            'cholesterol': np.random.normal(220 if has_heart_disease else 180, 15),
            'body_temp': np.random.normal(98.6, 0.7),
            'respiratory_rate': np.random.normal(18, 2),
            'oxygen_saturation': np.random.normal(96, 2),
            'weight': np.random.normal(70, 15) - (age * 0.1)
        }

    def generate_vitals_df(self, patient_data: dict, n_records=10) -> pd.DataFrame:
        return pd.DataFrame([self.generate_vitals(patient_data) for _ in range(n_records)])
