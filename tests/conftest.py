"""
Pytest configuration and fixtures
"""

import pytest
import pandas as pd
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.data_generator.patient_generator import PatientGenerator
from src.config.settings import settings


@pytest.fixture
def sample_patients():
    """Generate sample patient data for testing"""
    generator = PatientGenerator(num_patients=100, seed=42)
    return generator.generate_patients()


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directory"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "raw").mkdir()
    (data_dir / "processed").mkdir()
    (data_dir / "private").mkdir()
    return data_dir


@pytest.fixture
def sample_patient_record():
    """Single patient record for testing"""
    return {
        'patient_id': 'PT000001',
        'first_name': 'John',
        'last_name': 'Doe',
        'gender': 'M',
        'dob': pd.Timestamp('1985-06-15'),
        'age': 39,
        'zip_code': '12345',
        'income': 75000.0,
        'insurance': 'Private',
        'diabetes': False,
        'hypertension': True,
        'heart_disease': False
    }


@pytest.fixture
def privacy_epsilon():
    """Default epsilon for privacy tests"""
    return 1.0


@pytest.fixture
def privacy_delta():
    """Default delta for privacy tests"""
    return 1e-5
