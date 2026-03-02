# src/data_generator/treatment_generator.py

import random


class TreatmentGenerator:
    """Simulates treatment assignments for synthetic patients"""

    def __init__(self):
        self.treatments = {
            'diabetes': ['metformin', 'insulin', 'glipizide'],
            'hypertension': ['amlodipine', 'lisinopril', 'hydrochlorothiazide'],
            'heart_disease': ['aspirin', 'statins', 'beta_blockers']
        }

    def assign_treatments(self, patient_data: dict, visit_date=None) -> dict:
        assigned = {'visit_date': visit_date} if visit_date else {}

        if patient_data.get('diabetes', 0):
            assigned['diabetes_treatment'] = random.choice(self.treatments['diabetes'])

        if patient_data.get('hypertension', 0):
            assigned['hypertension_treatment'] = random.choice(self.treatments['hypertension'])

        if patient_data.get('heart_disease', 0):
            assigned['heart_disease_treatment'] = random.choice(self.treatments['heart_disease'])

        return assigned

    def generate_treatments(self, patients_df):
        """
        Generate treatments for a DataFrame of patients

        Args:
            patients_df: DataFrame containing patient data

        Returns:
            DataFrame with patient_id and assigned treatments
        """
        import pandas as pd

        treatments_list = []

        for idx, patient in patients_df.iterrows():
            patient_dict = patient.to_dict()
            patient_id = patient_dict.get('patient_id', f'PT{idx:06d}')

            # Get all treatments for this patient
            treatment_names = []

            if patient_dict.get('diabetes', 0) == 1:
                treatment_names.extend(self.treatments['diabetes'][:2])  # Give 2 diabetes meds

            if patient_dict.get('hypertension', 0) == 1:
                treatment_names.append(random.choice(self.treatments['hypertension']))

            if patient_dict.get('heart_disease', 0) == 1:
                treatment_names.append(random.choice(self.treatments['heart_disease']))

            treatments_list.append({
                'patient_id': patient_id,
                'treatments': treatment_names if treatment_names else ['none']
            })

        return pd.DataFrame(treatments_list)
