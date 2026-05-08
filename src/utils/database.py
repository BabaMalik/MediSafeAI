"""
Database Utilities
Helper functions for database operations, migrations, and data loading
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime

from src.models.base import get_db_session, init_db
from src.models.patient import Patient, PatientVitals, PatientProgression
from src.models.audit import AuditLog, PrivacyOperation
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_patients_to_db(df: pd.DataFrame, batch_size: int = 1000) -> int:
    """
    Load patient data from DataFrame to database

    Args:
        df: DataFrame with patient data
        batch_size: Number of records to insert per batch

    Returns:
        Number of records inserted
    """
    session = get_db_session()
    inserted_count = 0

    try:
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i + batch_size]

            for _, row in batch.iterrows():
                patient = Patient(
                    patient_id=row['patient_id'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    gender=row['gender'],
                    dob=pd.to_datetime(row['dob']).date(),
                    age=int(row['age']),
                    zip_code=row['zip_code'],
                    income=float(row['income']),
                    insurance=row['insurance'],
                    diabetes=bool(row['diabetes']),
                    hypertension=bool(row['hypertension']),
                    heart_disease=bool(row['heart_disease'])
                )
                session.add(patient)
                inserted_count += 1

            session.commit()
            logger.info(f"Loaded {inserted_count}/{len(df)} patients to database")

        return inserted_count

    except Exception as e:
        session.rollback()
        logger.error(f"Error loading patients to database: {e}")
        raise
    finally:
        session.close()


def load_vitals_to_db(df: pd.DataFrame, batch_size: int = 1000) -> int:
    """
    Load vitals data from DataFrame to database

    Args:
        df: DataFrame with vitals data
        batch_size: Number of records per batch

    Returns:
        Number of records inserted
    """
    session = get_db_session()
    inserted_count = 0

    try:
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i + batch_size]

            for _, row in batch.iterrows():
                vitals = PatientVitals(
                    patient_id=row['patient_id'],
                    blood_pressure_systolic=float(row['blood_pressure_systolic']),
                    blood_pressure_diastolic=float(row['blood_pressure_diastolic']),
                    heart_rate=float(row['heart_rate']),
                    blood_glucose=float(row['blood_glucose']),
                    cholesterol=float(row['cholesterol']),
                    body_temperature=float(row['body_temperature']),
                    respiratory_rate=float(row['respiratory_rate']),
                    oxygen_saturation=float(row['oxygen_saturation']),
                    weight=float(row['weight'])
                )
                session.add(vitals)
                inserted_count += 1

            session.commit()
            logger.info(f"Loaded {inserted_count}/{len(df)} vitals to database")

        return inserted_count

    except Exception as e:
        session.rollback()
        logger.error(f"Error loading vitals to database: {e}")
        raise
    finally:
        session.close()


def log_privacy_operation_to_db(
    epsilon: float,
    delta: float,
    mechanism: str,
    operation_type: str,
    data_source: str,
    num_records: int,
    columns_affected: List[str] = None,
    output_file: str = None,
    user_id: str = None
) -> PrivacyOperation:
    """
    Log a differential privacy operation to database

    Args:
        epsilon: Privacy budget used
        delta: Privacy parameter
        mechanism: Privacy mechanism (laplace, gaussian, etc.)
        operation_type: Type of operation
        data_source: Source data identifier
        num_records: Number of records affected
        columns_affected: List of columns privatized
        output_file: Output file path
        user_id: User who performed operation

    Returns:
        Created PrivacyOperation record
    """
    session = get_db_session()

    try:
        # Calculate cumulative privacy budget
        from sqlalchemy import func
        cumulative_epsilon = session.query(func.sum(PrivacyOperation.epsilon)).scalar() or 0.0
        cumulative_delta = session.query(func.sum(PrivacyOperation.delta)).scalar() or 0.0

        privacy_op = PrivacyOperation(
            epsilon=epsilon,
            delta=delta,
            mechanism=mechanism,
            operation_type=operation_type,
            data_source=data_source,
            columns_affected=columns_affected,
            num_records=num_records,
            cumulative_epsilon=cumulative_epsilon + epsilon,
            cumulative_delta=cumulative_delta + delta,
            output_file=output_file,
            user_id=user_id
        )

        session.add(privacy_op)
        session.commit()
        session.refresh(privacy_op)

        logger.info(f"Logged privacy operation: ε={epsilon}, cumulative ε={privacy_op.cumulative_epsilon}")

        return privacy_op

    except Exception as e:
        session.rollback()
        logger.error(f"Error logging privacy operation: {e}")
        raise
    finally:
        session.close()


def log_audit_event(
    event_type: str,
    event_action: str,
    event_description: str = None,
    user_id: str = None,
    resource_type: str = None,
    resource_id: str = None,
    metadata: Dict[str, Any] = None,
    status: str = 'success'
) -> AuditLog:
    """
    Log an audit event to database

    Args:
        event_type: Type of event (data_access, data_generation, etc.)
        event_action: Specific action taken
        event_description: Human-readable description
        user_id: User who performed action
        resource_type: Type of resource affected
        resource_id: ID of resource
        metadata: Additional context
        status: Status of event

    Returns:
        Created AuditLog record
    """
    session = get_db_session()

    try:
        audit = AuditLog(
            event_type=event_type,
            event_action=event_action,
            event_description=event_description,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata,
            status=status
        )

        session.add(audit)
        session.commit()
        session.refresh(audit)

        return audit

    except Exception as e:
        session.rollback()
        logger.error(f"Error logging audit event: {e}")
        raise
    finally:
        session.close()


def get_privacy_budget_summary(days: int = 30) -> Dict[str, Any]:
    """
    Get summary of privacy budget usage

    Args:
        days: Number of days to look back

    Returns:
        Dictionary with budget summary
    """
    session = get_db_session()

    try:
        from sqlalchemy import func
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        total_ops = session.query(func.count(PrivacyOperation.id))\
            .filter(PrivacyOperation.created_at >= cutoff_date)\
            .scalar() or 0

        total_epsilon = session.query(func.sum(PrivacyOperation.epsilon))\
            .filter(PrivacyOperation.created_at >= cutoff_date)\
            .scalar() or 0.0

        summary = {
            'days': days,
            'total_operations': total_ops,
            'total_epsilon': float(total_epsilon),
            'operations': []
        }

        # Get recent operations
        recent_ops = session.query(PrivacyOperation)\
            .filter(PrivacyOperation.created_at >= cutoff_date)\
            .order_by(PrivacyOperation.created_at.desc())\
            .limit(10)\
            .all()

        summary['operations'] = [op.to_dict() for op in recent_ops]

        return summary

    except Exception as e:
        logger.error(f"Error getting privacy budget summary: {e}")
        return {'error': str(e)}
    finally:
        session.close()


def check_database_connection() -> bool:
    """
    Check if database is accessible

    Returns:
        True if database is accessible, False otherwise
    """
    try:
        session = get_db_session()
        session.execute('SELECT 1')
        session.close()
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
