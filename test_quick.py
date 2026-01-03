#!/usr/bin/env python
"""
Quick Test Script for MediSafeAI
Tests core functionality without external dependencies
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

        gen = PatientGenerator(num_patients=10, seed=42)
        df = gen.generate_patients()

        print(f"✓ Generated {len(df)} patients")
        print(f"✓ Columns: {', '.join(df.columns)}")
        print(f"\nSample data:")
        print(df.head(3))
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
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
        gen = PatientGenerator(num_patients=5, seed=42)
        patients_df = gen.generate_patients()

        # Generate vitals
        vitals_gen = VitalsGenerator()
        vitals_df = vitals_gen.generate_vitals(patients_df)

        print(f"✓ Generated vitals for {len(vitals_df)} patients")
        print(f"✓ Columns: {', '.join(vitals_df.columns)}")
        print(f"\nSample vitals:")
        print(vitals_df[['patient_id', 'blood_pressure_systolic', 'blood_pressure_diastolic', 'heart_rate']].head(3))
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_differential_privacy():
    """Test differential privacy"""
    print("\n" + "=" * 60)
    print("TEST 3: Differential Privacy")
    print("=" * 60)
    try:
        import numpy as np
        from src.privacy.differential_privacy import DifferentialPrivacy

        # Create test data
        data = np.array([10, 20, 30, 40, 50])

        # Apply privacy
        dp = DifferentialPrivacy(epsilon=1.0, delta=1e-5)

        true_mean = data.mean()
        private_mean = dp.private_mean(data)

        print(f"✓ Original mean: {true_mean:.2f}")
        print(f"✓ Private mean: {private_mean:.2f}")
        print(f"✓ Difference: {abs(true_mean - private_mean):.2f}")
        print(f"✓ Privacy parameters: ε={dp.epsilon}, δ={dp.delta}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
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
        gen = PatientGenerator(num_patients=1, seed=42)
        patient = gen.generate_patients().iloc[0]

        # Simulate progression
        model = DiseaseProgressionModel()
        progression_df = model.simulate_progression(
            patient,
            num_visits=6,
            time_interval_days=30
        )

        print(f"✓ Simulated {len(progression_df)} visits")
        print(f"\nProgression data:")
        print(progression_df[['visit_number', 'visit_date', 'blood_glucose', 'hemoglobin_a1c']].head())
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_configuration():
    """Test configuration module"""
    print("\n" + "=" * 60)
    print("TEST 5: Configuration")
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
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("MediSafeAI - Quick Test Suite")
    print("=" * 60)

    results = []

    results.append(("Patient Generator", test_patient_generator()))
    results.append(("Vitals Generator", test_vitals_generator()))
    results.append(("Differential Privacy", test_differential_privacy()))
    results.append(("Disease Progression", test_disease_progression()))
    results.append(("Configuration", test_configuration()))

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
        print("\n🎉 All tests passed! MediSafeAI is working correctly!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the errors above.")


if __name__ == '__main__':
    main()
