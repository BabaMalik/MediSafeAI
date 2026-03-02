# src/data_generator/patient_generator.py
import numpy as np
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta


class PatientGenerator:
    def __init__(self, num_patients=10000, seed=42):
        self.num_patients = num_patients
        self.faker = Faker()
        self.faker.seed_instance(seed)
        np.random.seed(seed)

    def generate_patients(self, n_patients=None):
        """Generate patient data. Delegates to generate_demographics."""
        return self.generate_demographics(n_patients=n_patients or self.num_patients)

    def generate_demographics(self, n_patients=10000):
        """Generate patient demographic data"""
        patients = []

        for i in range(n_patients):
            patient_id = f"PT{i:06d}"
            gender = np.random.choice(['M', 'F'], p=[0.48, 0.52])

            if gender == 'M':
                first_name = self.faker.first_name_male()
            else:
                first_name = self.faker.first_name_female()

            dob = self.faker.date_of_birth(minimum_age=18, maximum_age=90)
            age = (datetime.now().date() - dob).days // 365

            # Create realistic demographic distributions
            if age < 30:
                diabetes_prob = 0.02
                hypertension_prob = 0.05
                heart_disease_prob = 0.01
            elif age < 50:
                diabetes_prob = 0.08
                hypertension_prob = 0.20
                heart_disease_prob = 0.05
            elif age < 70:
                diabetes_prob = 0.15
                hypertension_prob = 0.40
                heart_disease_prob = 0.15
            else:
                diabetes_prob = 0.25
                hypertension_prob = 0.60
                heart_disease_prob = 0.30

            if gender == 'M':  # Slight adjustments based on gender
                heart_disease_prob *= 1.5

            diabetes = np.random.choice([0, 1], p=[1 - diabetes_prob, diabetes_prob])
            hypertension = np.random.choice([0, 1], p=[1 - hypertension_prob, hypertension_prob])
            heart_disease = np.random.choice([0, 1], p=[1 - heart_disease_prob, heart_disease_prob])

            # Generate income with realistic distribution (log-normal)
            income = np.random.lognormal(mean=10.7, sigma=0.6)

            # Generate patient location
            zip_code = self.faker.zipcode()

            # Patient insurance status
            insurance_status = np.random.choice(['Private', 'Medicare', 'Medicaid', 'Uninsured'],
                                                p=[0.55, 0.20, 0.15, 0.10])

            patients.append({
                'patient_id': patient_id,
                'first_name': first_name,
                'last_name': self.faker.last_name(),
                'gender': gender,
                'dob': dob,
                'age': age,
                'zip_code': zip_code,
                'income': income,
                'insurance': insurance_status,
                'diabetes': diabetes,
                'hypertension': hypertension,
                'heart_disease': heart_disease
            })

        return pd.DataFrame(patients)


if __name__ == "__main__":
    import os
    generator = PatientGenerator(num_patients=10000)
    df = generator.generate_patients()

    output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw')
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, 'patients.csv')
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} patient records and saved to {output_path}")
