"""
Celery Tasks for Asynchronous Processing
Handles background jobs for data generation, privacy operations, and monitoring
"""

from celery import Task
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path

from src.api.celery_app import celery_app
from src.data_generator.patient_generator import PatientGenerator
from src.data_generator.vitals_generator import VitalsGenerator
from src.data_generator.treatment_generator import TreatmentGenerator
from src.privacy.differential_privacy import DifferentialPrivacy
from src.config.settings import settings
from src.utils.logger import get_logger, get_audit_logger

logger = get_logger(__name__)
audit_logger = get_audit_logger()


class DatabaseTask(Task):
    """Base task with database session management"""
    _db = None

    @property
    def db(self):
        if self._db is None:
            from src.models.base import get_db_session
            self._db = get_db_session()
        return self._db


# =============================================================================
# DATA GENERATION TASKS
# =============================================================================

@celery_app.task(bind=True, base=DatabaseTask, name='src.api.tasks.generate_patients_async')
def generate_patients_async(self, num_patients=1000, seed=None):
    """
    Asynchronously generate patient data

    Args:
        num_patients: Number of patients to generate
        seed: Random seed for reproducibility

    Returns:
        dict with file_path and num_records
    """
    try:
        logger.info(f"Starting async patient generation: {num_patients} patients")

        # Generate patients
        generator = PatientGenerator(seed=seed)
        patients_df = generator.generate_demographics(n_patients=num_patients)

        # Save to file
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        output_file = settings.DATA_OUTPUT_DIR / f"patients_{timestamp}.csv"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        patients_df.to_csv(output_file, index=False)

        # Audit log
        audit_logger.log_data_generation(
            generator_type='patients',
            num_records=len(patients_df),
            output_file=str(output_file)
        )

        result = {
            'file_path': str(output_file),
            'num_records': len(patients_df),
            'timestamp': timestamp
        }

        logger.info(f"Completed patient generation: {result}")
        return result

    except Exception as e:
        logger.error(f"Error in async patient generation: {e}", exc_info=True)
        raise


@celery_app.task(bind=True, base=DatabaseTask, name='src.api.tasks.generate_complete_dataset')
def generate_complete_dataset(self, num_patients=1000, seed=None, apply_privacy=False, epsilon=1.0):
    """
    Generate complete dataset with patients, vitals, and treatments

    Args:
        num_patients: Number of patients
        seed: Random seed
        apply_privacy: Whether to apply differential privacy
        epsilon: Privacy budget

    Returns:
        dict with file paths
    """
    try:
        logger.info(f"Starting complete dataset generation: {num_patients} patients")

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        output_dir = settings.DATA_OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate patients
        gen = PatientGenerator(seed=seed)
        patients_df = gen.generate_demographics(n_patients=num_patients)
        patients_file = output_dir / f"patients_{timestamp}.csv"
        patients_df.to_csv(patients_file, index=False)

        result = {'patients_file': str(patients_file)}

        # Generate vitals
        vitals_gen = VitalsGenerator()
        vitals_df = vitals_gen.generate_vitals(patients_df)
        vitals_file = output_dir / f"vitals_{timestamp}.csv"
        vitals_df.to_csv(vitals_file, index=False)
        result['vitals_file'] = str(vitals_file)

        # Generate treatments
        treatment_gen = TreatmentGenerator()
        treatments_df = treatment_gen.generate_treatments(patients_df)
        treatments_file = output_dir / f"treatments_{timestamp}.csv"
        treatments_df.to_csv(treatments_file, index=False)
        result['treatments_file'] = str(treatments_file)

        # Apply privacy if requested
        if apply_privacy:
            dp = DifferentialPrivacy(epsilon=epsilon, delta=1e-5)
            private_df = dp.privatize_dataframe(
                patients_df,
                numeric_columns=['age', 'income']
            )
            private_file = settings.DATA_PRIVATE_DIR / f"patients_private_{timestamp}.csv"
            private_file.parent.mkdir(parents=True, exist_ok=True)
            private_df.to_csv(private_file, index=False)
            result['private_file'] = str(private_file)

            # Audit privacy operation
            audit_logger.log_privacy_operation(
                operation='batch_privatization',
                epsilon=epsilon,
                delta=1e-5,
                num_records=len(patients_df)
            )

        logger.info(f"Completed dataset generation: {num_patients} records")
        return result

    except Exception as e:
        logger.error(f"Error in complete dataset generation: {e}", exc_info=True)
        raise


# =============================================================================
# PRIVACY TASKS
# =============================================================================

@celery_app.task(bind=True, base=DatabaseTask, name='src.api.tasks.privacy_apply_async')
def privacy_apply_async(self, input_file, output_file=None, epsilon=1.0, delta=1e-5, columns=None):
    """
    Asynchronously apply differential privacy to a dataset

    Args:
        input_file: Path to input CSV
        output_file: Path to output CSV
        epsilon: Privacy budget
        delta: Privacy parameter
        columns: Columns to privatize

    Returns:
        dict with file_path and stats
    """
    try:
        logger.info(f"Starting async privacy application: {input_file}")

        # Load data
        df = pd.read_csv(input_file)

        # Apply privacy
        dp = DifferentialPrivacy(epsilon=epsilon, delta=delta)
        private_df = dp.privatize_dataframe(
            df,
            numeric_columns=columns or ['age', 'income']
        )

        # Save
        if output_file is None:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            output_file = settings.DATA_PRIVATE_DIR / f"private_{timestamp}.csv"
            output_file.parent.mkdir(parents=True, exist_ok=True)

        private_df.to_csv(output_file, index=False)

        # Audit
        audit_logger.log_privacy_operation(
            operation='privatize_async',
            epsilon=epsilon,
            delta=delta,
            num_records=len(df)
        )

        result = {
            'input_file': input_file,
            'output_file': str(output_file),
            'num_records': len(df),
            'epsilon': epsilon,
            'delta': delta
        }

        logger.info(f"Completed privacy application: {result}")
        return result

    except Exception as e:
        logger.error(f"Error in async privacy application: {e}", exc_info=True)
        raise


# =============================================================================
# MONITORING TASKS
# =============================================================================

@celery_app.task(bind=True, base=DatabaseTask, name='src.api.tasks.monitor_privacy_budget')
def monitor_privacy_budget(self):
    """
    Monitor cumulative privacy budget usage
    Runs daily to check if budget thresholds are exceeded
    """
    try:
        logger.info("Monitoring privacy budget usage...")

        from src.models.audit import PrivacyOperation
        from sqlalchemy import func

        # Query last 30 days of privacy operations
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        total_ops = self.db.query(func.count(PrivacyOperation.id))\
            .filter(PrivacyOperation.created_at >= thirty_days_ago)\
            .scalar() or 0

        total_epsilon = self.db.query(func.sum(PrivacyOperation.epsilon))\
            .filter(PrivacyOperation.created_at >= thirty_days_ago)\
            .scalar() or 0.0

        max_budget = settings.MAX_EPSILON

        report = {
            'date': datetime.utcnow().isoformat(),
            'total_operations_30d': total_ops,
            'cumulative_epsilon_30d': float(total_epsilon),
            'max_epsilon': max_budget,
            'budget_remaining': max_budget - float(total_epsilon),
            'usage_percentage': (float(total_epsilon) / max_budget * 100) if max_budget > 0 else 0
        }

        # Alert if over threshold
        if report['usage_percentage'] > 80:
            logger.warning(f"Privacy budget usage high: {report['usage_percentage']:.1f}%")

        logger.info(f"Privacy budget report: {report}")
        return report

    except Exception as e:
        logger.error(f"Error monitoring privacy budget: {e}", exc_info=True)
        return {'error': str(e)}


@celery_app.task(bind=True, base=DatabaseTask, name='src.api.tasks.cleanup_old_data')
def cleanup_old_data(self, days=90):
    """
    Clean up old temporary data files
    Runs weekly to remove files older than specified days
    """
    try:
        logger.info(f"Cleaning up data older than {days} days...")

        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0

        # Clean up old CSV files in data directories
        for data_dir in [settings.DATA_OUTPUT_DIR, settings.DATA_PRIVATE_DIR]:
            if data_dir.exists():
                for file_path in data_dir.glob('*.csv'):
                    if datetime.fromtimestamp(file_path.stat().st_mtime) < cutoff_date:
                        file_path.unlink()
                        deleted_count += 1
                        logger.debug(f"Deleted old file: {file_path}")

        logger.info(f"Cleanup complete: {deleted_count} files deleted")
        return {'deleted_count': deleted_count}

    except Exception as e:
        logger.error(f"Error during cleanup: {e}", exc_info=True)
        return {'error': str(e)}
