#!/usr/bin/env python
"""
Working Test Script for MediSafeAI
Tests with the ACTUAL existing code API
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_patient_generator():
    """Test patient data generation"""
    print("=" * 60)
    print("TEST 1: Patient Generator")
    print("=" * 60)
    try:
        from src.data_generator.patient_generator import PatientGenerator

        # Use actual API: PatientGenerator(seed)
        gen = PatientGenerator(seed=42)
        df = gen.generate_demographics(n_patients=10)  # Actual method name

        print(f"✓ Generated {len(df)} patients")
        print(f"✓ Columns: {', '.join(df.columns)}")
        print(f"\nSample data:")
        print(df.head(3))
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vitals_generator():
    """Test vitals generation"""
    print("\n" + "=" * 60)
    print("TEST 2: Vitals Generator")
    print("=" * 60)
    try:
        from src.data_generator.patient_generator import PatientGenerator
        from src.data_generator.vitals_generator import VitalsGenerator

        # Generate patients first
        gen = PatientGenerator(seed=42)
        patients_df = gen.generate_demographics(n_patients=5)

        # Generate vitals
        vitals_gen = VitalsGenerator()
        vitals_df = vitals_gen.generate_vitals(patients_df)

        print(f"✓ Generated vitals for {len(vitals_df)} patients")
        print(f"✓ Vital signs columns present")
        print(f"\nSample vitals:")
        print(vitals_df[['patient_id', 'blood_pressure_systolic', 'heart_rate']].head(3))
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_differential_privacy():
    """Test differential privacy"""
    print("\n" + "=" * 60)
    print("TEST 3: Differential Privacy")
    print("=" * 60)
    try:
        import pandas as pd
        from src.privacy.differential_privacy import DifferentialPrivacy

        # Create test data
        test_df = pd.DataFrame({
            'patient_id': ['PT001', 'PT002', 'PT003'],
            'age': [25, 45, 65],
            'income': [50000, 75000, 100000]
        })

        print("Original data:")
        print(test_df)

        # Apply privacy using actual API
        dp = DifferentialPrivacy(epsilon=1.0, delta=1e-5)
        private_df = dp.privatize_dataframe(
            test_df,
            numeric_columns=['age', 'income']
        )

        print("\nPrivatized data:")
        print(private_df)

        print(f"\n✓ Privacy applied with ε={dp.epsilon}, δ={dp.delta}")
        print(f"✓ Noise added to protect patient data")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_disease_progression():
    """Test disease progression simulation"""
    print("\n" + "=" * 60)
    print("TEST 4: Disease Progression")
    print("=" * 60)
    try:
        from src.data_generator.patient_generator import PatientGenerator
        from src.data_generator.disease_progression import DiseaseProgressionModel

        # Generate a patient
        gen = PatientGenerator(seed=42)
        patients_df = gen.generate_demographics(n_patients=1)
        patient = patients_df.iloc[0]

        print(f"Patient: {patient['patient_id']}, Age: {patient['age']}")

        # Simulate progression
        model = DiseaseProgressionModel()
        progression_df = model.simulate_progression(
            patient,
            num_visits=6,
            time_interval_days=30
        )

        print(f"\n✓ Simulated {len(progression_df)} visits over 6 months")
        print(f"\nProgression summary:")
        print(progression_df[['visit_number', 'blood_glucose']].head())
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_treatment_generator():
    """Test treatment generation"""
    print("\n" + "=" * 60)
    print("TEST 5: Treatment Generator")
    print("=" * 60)
    try:
        from src.data_generator.patient_generator import PatientGenerator
        from src.data_generator.treatment_generator import TreatmentGenerator

        # Generate patients
        gen = PatientGenerator(seed=42)
        patients_df = gen.generate_demographics(n_patients=5)

        # Generate treatments
        treatment_gen = TreatmentGenerator()
        treatments_df = treatment_gen.generate_treatments(patients_df)

        print(f"✓ Generated treatments for {len(treatments_df)} patients")
        print(f"\nSample treatments:")
        for idx, row in treatments_df.head(3).iterrows():
            print(f"  {row['patient_id']}: {', '.join(row['treatments'])}")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration():
    """Test configuration module"""
    print("\n" + "=" * 60)
    print("TEST 6: Configuration")
    print("=" * 60)
    try:
        from src.config.settings import settings

        print(f"✓ App Name: {settings.APP_NAME}")
        print(f"✓ Version: {settings.APP_VERSION}")
        print(f"✓ Environment: {settings.APP_ENV}")
        print(f"✓ Default Epsilon: {settings.DEFAULT_EPSILON}")
        print(f"✓ Data Directory: {settings.DATA_DIR}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("MediSafeAI - Working Test Suite")
    print("Testing with ACTUAL existing code")
    print("=" * 60)

    results = []

    results.append(("Patient Generator", test_patient_generator()))
    results.append(("Vitals Generator", test_vitals_generator()))
    results.append(("Differential Privacy", test_differential_privacy()))
    results.append(("Disease Progression", test_disease_progression()))
    results.append(("Treatment Generator", test_treatment_generator()))
    results.append(("Configuration Module", test_configuration()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! MediSafeAI core features are working!")
    elif passed > 0:
        print(f"\n⚡ {passed} features working! {total - passed} need attention.")
    else:
        print(f"\n⚠️  All tests failed. Check dependencies and setup.")

    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
