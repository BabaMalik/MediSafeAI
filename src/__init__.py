"""
MediSafeAI - HIPAA-Compliant Synthetic Healthcare Data Generator
Provides differential privacy-enhanced synthetic patient data generation
"""

__version__ = "1.0.0"
__author__ = "MediSafeAI Team"

# Make key modules easily importable
from src.data_generator.patient_generator import PatientGenerator
from src.data_generator.vitals_generator import VitalsGenerator
from src.data_generator.treatment_generator import TreatmentGenerator
from src.privacy.differential_privacy import DifferentialPrivacy

__all__ = [
    'PatientGenerator',
    'VitalsGenerator',
    'TreatmentGenerator',
    'DifferentialPrivacy',
]
