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
