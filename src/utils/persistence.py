"""
Persistence Utility
Handles saving generated data to the database
"""

import os
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
from src.config.settings import settings
from sqlalchemy.orm import Session
from src.models.base import get_db
from src.models.patient import Patient, PatientVitals, PatientProgression
from src.models.audit import PrivacyOperation
from src.utils.logger import get_logger

logger = get_logger(__name__)

def safe_path(file_path: str, base_dir: Path = settings.DATA_DIR) -> Path:
    """
    Safely resolve a file path within a base directory to prevent path traversal

    Args:
        file_path: The path to resolve
        base_dir: The allowed base directory (defaults to DATA_DIR)

    Returns:
        Resolved Path object

    Raises:
        ValueError: If the path is outside the allowed directory
    """
    requested_path = Path(file_path)
    if not requested_path.is_absolute():
        requested_path = (base_dir / requested_path).resolve()
    else:
        requested_path = requested_path.resolve()

    if not str(requested_path).startswith(str(base_dir.resolve())):
        raise ValueError(f"Path access denied: {file_path} is outside allowed directory")

    return requested_path

def save_patients_to_db(df: pd.DataFrame):
    """Save patients DataFrame to database"""
    with get_db() as session:
        for _, row in df.iterrows():
            patient = Patient(
                patient_id=row['patient_id'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                gender=row['gender'],
                dob=row['dob'],
                age=row['age'],
                zip_code=row['zip_code'],
                income=row['income'],
                insurance=row['insurance'],
                diabetes=bool(row['diabetes']),
                hypertension=bool(row['hypertension']),
                heart_disease=bool(row['heart_disease'])
            )
            session.merge(patient)
        logger.info(f"Saved {len(df)} patients to database")

def save_vitals_to_db(df: pd.DataFrame):
    """Save vitals DataFrame to database"""
    with get_db() as session:
        for _, row in df.iterrows():
            vitals = PatientVitals(
                patient_id=row['patient_id'],
                blood_pressure_systolic=row['blood_pressure_systolic'],
                blood_pressure_diastolic=row['blood_pressure_diastolic'],
                heart_rate=row['heart_rate'],
                blood_glucose=row['blood_glucose'],
                cholesterol=row['cholesterol'],
                body_temperature=row['body_temperature'],
                respiratory_rate=row['respiratory_rate'],
                oxygen_saturation=row['oxygen_saturation'],
                weight=row['weight']
            )
            session.add(vitals)
        logger.info(f"Saved {len(df)} vital records to database")

def save_progression_to_db(df: pd.DataFrame):
    """Save disease progression DataFrame to database"""
    with get_db() as session:
        for _, row in df.iterrows():
            progression = PatientProgression(
                patient_id=row['patient_id'],
                visit_number=row['visit_number'],
                visit_date=row['visit_date'],
                blood_pressure_systolic=row.get('blood_pressure_systolic'),
                blood_pressure_diastolic=row.get('blood_pressure_diastolic'),
                heart_rate=row.get('heart_rate'),
                blood_glucose=row.get('blood_glucose'),
                weight=row.get('weight'),
                hemoglobin_a1c=row.get('hemoglobin_a1c'),
                white_blood_cells=row.get('white_blood_cells'),
                creatinine=row.get('creatinine'),
                insulin_level=row.get('insulin_level'),
                ejection_fraction=row.get('ejection_fraction'),
                troponin=row.get('troponin'),
                intervention_occurred=bool(row.get('intervention_occurred', False)),
                intervention_type=row.get('intervention_type')
            )
            session.add(progression)
        logger.info(f"Saved {len(df)} progression records to database")

def save_privacy_operation(
    epsilon: float,
    delta: float,
    operation_type: str,
    data_source: str,
    mechanism: str = 'auto',
    columns_affected: List[str] = None,
    num_records: int = None,
    output_file: str = None,
    statistics: Dict[str, Any] = None
):
    """Log a privacy operation to the database"""
    with get_db() as session:
        # Calculate cumulative epsilon for the last 30 days (simplified)
        from sqlalchemy import func
        from datetime import datetime, timedelta

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        cumulative = session.query(
            func.sum(PrivacyOperation.epsilon),
            func.sum(PrivacyOperation.delta)
        ).filter(PrivacyOperation.created_at >= thirty_days_ago).first()

        total_epsilon = (cumulative[0] or 0.0) + epsilon
        total_delta = (cumulative[1] or 0.0) + delta

        op = PrivacyOperation(
            epsilon=epsilon,
            delta=delta,
            mechanism=mechanism,
            operation_type=operation_type,
            data_source=data_source,
            columns_affected=columns_affected,
            num_records=num_records,
            cumulative_epsilon=total_epsilon,
            cumulative_delta=total_delta,
            output_file=output_file,
            statistics=statistics
        )
        session.add(op)
        logger.info(f"Logged privacy operation: ε={epsilon} to database")
