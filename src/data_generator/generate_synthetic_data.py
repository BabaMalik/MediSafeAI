import os
import pandas as pd
from datetime import datetime, timedelta

from patient_generator import PatientGenerator
from vitals_generator import VitalsGenerator
from treatment_generator import TreatmentGenerator
from disease_progression import DiseaseProgressionModel
from temporal_patterns import TemporalPatternGenerator

# Create output directory
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Parameters
N_PATIENTS = 1000
START_DATE = datetime(2022, 1, 1)
END_DATE = datetime(2023, 1, 1)
VISIT_INTERVAL_DAYS = 30

# Initialize generators
patient_gen = PatientGenerator()
vitals_gen = VitalsGenerator()
treatment_gen = TreatmentGenerator()
disease_model = DiseaseProgressionModel()
temporal_gen = TemporalPatternGenerator()

# Step 1: Generate Patients
patients_df = patient_gen.generate_demographics(n_patients=N_PATIENTS)
patients_df.to_csv(os.path.join(OUTPUT_DIR, "patients.csv"), index=False)
print(f"✅ Generated {len(patients_df)} patients.")

# Step 2: For each patient, generate visits
all_visits = []
all_vitals = []
all_treatments = []

for _, patient in patients_df.iterrows():
    # Simulate disease progression (visits over time)
    visits_df = disease_model.simulate_progression(
        patient_data=patient,
        start_date=START_DATE,
        end_date=END_DATE,
        visit_interval_days=VISIT_INTERVAL_DAYS
    )

    # Apply temporal trends and anomalies
    visits_df = temporal_gen.inject_anomalies(visits_df, ['blood_glucose', 'cholesterol'])
    visits_df = temporal_gen.add_cyclic_patterns(visits_df, 'heart_rate')

    # Generate vitals per visit
    for i, visit in visits_df.iterrows():
        vitals = vitals_gen.generate_vitals(patient_data=patient)
        vitals['patient_id'] = patient['patient_id']
        vitals['visit_date'] = visit['visit_date']
        all_vitals.append(vitals)

        # Assign treatment per visit
        treatment = treatment_gen.assign_treatments(patient.to_dict(), visit_date=visit['visit_date'])
        treatment['patient_id'] = patient['patient_id']
        all_treatments.append(treatment)

    all_visits.append(visits_df)

# Step 3: Save all data
all_visits_df = pd.concat(all_visits, ignore_index=True)
all_vitals_df = pd.DataFrame(all_vitals)
all_treatments_df = pd.DataFrame(all_treatments)

all_visits_df.to_csv(os.path.join(OUTPUT_DIR, "visits.csv"), index=False)
all_vitals_df.to_csv(os.path.join(OUTPUT_DIR, "vitals.csv"), index=False)
all_treatments_df.to_csv(os.path.join(OUTPUT_DIR, "treatments.csv"), index=False)

print("✅ All synthetic data generated and saved to data/raw/")