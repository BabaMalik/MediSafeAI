"""
API Routes
Defines all REST API endpoints for MediSafeAI
"""

from flask import Blueprint, request, jsonify, send_file
from datetime import datetime
from pathlib import Path
import pandas as pd

from src.data_generator.patient_generator import PatientGenerator
from src.data_generator.vitals_generator import VitalsGenerator
from src.data_generator.disease_progression import DiseaseProgressionModel
from src.data_generator.treatment_generator import TreatmentGenerator
from src.privacy.differential_privacy import DifferentialPrivacy
from src.utils.logger import get_logger, get_audit_logger
from src.utils.schemas import (
    PatientCreate, PrivacyRequest, DiseaseProgressionRequest,
    ExportRequest, BatchGenerationRequest
)
from src.config.settings import settings

logger = get_logger(__name__)
audit_logger = get_audit_logger()

# Create blueprint
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')


# =============================================================================
# GENERATION ENDPOINTS
# =============================================================================

@api_v1.route('/generate/patients', methods=['POST'])
def generate_patients():
    """Generate synthetic patient data"""
    try:
        data = request.get_json()
        validated = PatientCreate(**data)

        logger.info(f"Generating {validated.num_patients} patients")

        # Generate patients
        generator = PatientGenerator(
            num_patients=validated.num_patients,
            seed=validated.seed
        )
        patients_df = generator.generate_patients()

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

        return jsonify({
            'status': 'success',
            'message': f'Generated {len(patients_df)} patient records',
            'data': {
                'records_generated': len(patients_df),
                'file_path': str(output_file),
                'columns': list(patients_df.columns)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error generating patients: {e}")
        return jsonify({
            'status': 'error',
            'error_code': 'GENERATION_ERROR',
            'error_message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@api_v1.route('/generate/vitals', methods=['POST'])
def generate_vitals():
    """Generate vital signs for patients"""
    try:
        data = request.get_json()
        input_file = data.get('input_file')

        if not input_file:
            return jsonify({
                'status': 'error',
                'error_message': 'input_file is required'
            }), 400

        # Load patients
        patients_df = pd.read_csv(input_file)
        logger.info(f"Loaded {len(patients_df)} patients from {input_file}")

        # Generate vitals
        generator = VitalsGenerator()
        vitals_df = generator.generate_vitals(patients_df)

        # Save to file
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        output_file = settings.DATA_OUTPUT_DIR / f"vitals_{timestamp}.csv"
        vitals_df.to_csv(output_file, index=False)

        # Audit log
        audit_logger.log_data_generation(
            generator_type='vitals',
            num_records=len(vitals_df),
            output_file=str(output_file)
        )

        return jsonify({
            'status': 'success',
            'message': f'Generated vitals for {len(vitals_df)} patients',
            'data': {
                'records_generated': len(vitals_df),
                'file_path': str(output_file)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error generating vitals: {e}")
        return jsonify({
            'status': 'error',
            'error_message': str(e)
        }), 500


@api_v1.route('/generate/batch', methods=['POST'])
def generate_batch():
    """Generate complete patient dataset with all components"""
    try:
        data = request.get_json()
        validated = BatchGenerationRequest(**data)

        logger.info(f"Starting batch generation for {validated.num_patients} patients")

        # Generate patients
        generator = PatientGenerator(
            num_patients=validated.num_patients,
            seed=validated.seed
        )
        patients_df = generator.generate_patients()

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        output_dir = Path(validated.output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save patients
        patients_file = output_dir / f"patients_{timestamp}.csv"
        patients_df.to_csv(patients_file, index=False)

        files_generated = {'patients': str(patients_file)}

        # Generate vitals if requested
        if validated.include_vitals:
            vitals_gen = VitalsGenerator()
            vitals_df = vitals_gen.generate_vitals(patients_df)
            vitals_file = output_dir / f"vitals_{timestamp}.csv"
            vitals_df.to_csv(vitals_file, index=False)
            files_generated['vitals'] = str(vitals_file)

        # Generate treatments if requested
        if validated.include_treatments:
            treatment_gen = TreatmentGenerator()
            treatments_df = treatment_gen.generate_treatments(patients_df)
            treatments_file = output_dir / f"treatments_{timestamp}.csv"
            treatments_df.to_csv(treatments_file, index=False)
            files_generated['treatments'] = str(treatments_file)

        # Apply privacy if requested
        if validated.apply_privacy:
            dp = DifferentialPrivacy(
                epsilon=validated.privacy_config.epsilon,
                delta=validated.privacy_config.delta
            )
            private_patients_df = dp.privatize_dataframe(
                patients_df,
                numeric_columns=['age', 'income']
            )
            private_file = output_dir / f"patients_private_{timestamp}.csv"
            private_patients_df.to_csv(private_file, index=False)
            files_generated['private_patients'] = str(private_file)

        return jsonify({
            'status': 'success',
            'message': f'Batch generation complete',
            'data': {
                'records_generated': len(patients_df),
                'files': files_generated
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error in batch generation: {e}")
        return jsonify({
            'status': 'error',
            'error_message': str(e)
        }), 500


# =============================================================================
# PRIVACY ENDPOINTS
# =============================================================================

@api_v1.route('/privacy/apply', methods=['POST'])
def apply_privacy():
    """Apply differential privacy to a dataset"""
    try:
        data = request.get_json()
        validated = PrivacyRequest(**data)

        logger.info(f"Applying privacy: ε={validated.privacy_config.epsilon}, δ={validated.privacy_config.delta}")

        # Load data
        df = pd.read_csv(validated.input_file)

        # Apply differential privacy
        dp = DifferentialPrivacy(
            epsilon=validated.privacy_config.epsilon,
            delta=validated.privacy_config.delta
        )

        private_df = dp.privatize_dataframe(
            df,
            numeric_columns=validated.numeric_columns,
            categorical_columns=validated.categorical_columns
        )

        # Save output
        output_file = validated.output_file or str(
            settings.DATA_PRIVATE_DIR / f"private_{Path(validated.input_file).name}"
        )
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        private_df.to_csv(output_file, index=False)

        # Audit log
        audit_logger.log_privacy_operation(
            operation='privatize_dataframe',
            epsilon=validated.privacy_config.epsilon,
            delta=validated.privacy_config.delta,
            input_file=validated.input_file,
            output_file=output_file,
            num_records=len(df)
        )

        return jsonify({
            'status': 'success',
            'message': 'Differential privacy applied successfully',
            'data': {
                'input_file': validated.input_file,
                'output_file': output_file,
                'records_processed': len(df),
                'epsilon': validated.privacy_config.epsilon,
                'delta': validated.privacy_config.delta
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error applying privacy: {e}")
        return jsonify({
            'status': 'error',
            'error_message': str(e)
        }), 500


@api_v1.route('/privacy/statistics', methods=['POST'])
def compute_private_statistics():
    """Compute private statistics for a column"""
    try:
        data = request.get_json()
        input_file = data.get('input_file')
        column = data.get('column')
        epsilon = data.get('epsilon', 1.0)
        delta = data.get('delta', 1e-5)

        # Load data
        df = pd.read_csv(input_file)
        column_data = df[column].values

        # Compute private statistics
        dp = DifferentialPrivacy(epsilon=epsilon, delta=delta)

        stats = {
            'mean': dp.private_mean(column_data),
            'variance': dp.private_variance(column_data),
            'count': dp.private_count(column_data)
        }
        stats['std'] = stats['variance'] ** 0.5

        return jsonify({
            'status': 'success',
            'data': {
                'column': column,
                'statistics': stats,
                'privacy_budget': {
                    'epsilon': epsilon,
                    'delta': delta
                }
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error computing statistics: {e}")
        return jsonify({
            'status': 'error',
            'error_message': str(e)
        }), 500


# =============================================================================
# SIMULATION ENDPOINTS
# =============================================================================

@api_v1.route('/simulate/progression', methods=['POST'])
def simulate_progression():
    """Simulate disease progression for a patient"""
    try:
        data = request.get_json()
        validated = DiseaseProgressionRequest(**data)

        logger.info(f"Simulating progression for patient {validated.patient_id}")

        # Try to load patient from provided data, file, or generate a sample
        patient_data = data.get('patient_data')
        patient = None

        if patient_data:
            # Patient data provided directly in request
            patient = patient_data
        else:
            # Try to load from default patients file
            default_file = settings.DATA_OUTPUT_DIR / 'patients.csv'
            if default_file.exists():
                patients_df = pd.read_csv(default_file)
                matched = patients_df[patients_df['patient_id'] == validated.patient_id]
                if not matched.empty:
                    patient = matched.iloc[0].to_dict()

        if patient is None:
            # Generate a sample patient with the given ID
            generator = PatientGenerator(num_patients=1, seed=hash(validated.patient_id) % 2**31)
            sample_df = generator.generate_patients()
            patient = sample_df.iloc[0].to_dict()
            patient['patient_id'] = validated.patient_id

        model = DiseaseProgressionModel()
        progression_df = model.simulate_progression(
            patient,
            num_visits=validated.num_visits,
            time_interval_days=validated.time_interval_days
        )

        # Convert dates to strings for JSON serialization
        progression_df['visit_date'] = progression_df['visit_date'].astype(str)

        return jsonify({
            'status': 'success',
            'message': f'Simulated {len(progression_df)} visits for patient {validated.patient_id}',
            'data': {
                'patient_id': validated.patient_id,
                'num_visits': len(progression_df),
                'time_interval_days': validated.time_interval_days,
                'progression': progression_df.to_dict(orient='records')
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error simulating progression: {e}")
        return jsonify({
            'status': 'error',
            'error_message': str(e)
        }), 500


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@api_v1.route('/export', methods=['POST'])
def export_data():
    """Export data in different formats"""
    try:
        data = request.get_json()
        validated = ExportRequest(**data)

        # Load data
        df = pd.read_csv(validated.input_file)

        # Select columns if specified
        if validated.columns:
            df = df[validated.columns]

        # Apply privacy if requested
        if validated.apply_privacy:
            dp = DifferentialPrivacy(
                epsilon=validated.privacy_config.epsilon,
                delta=validated.privacy_config.delta
            )
            df = dp.privatize_dataframe(df)

        # Export based on format
        output_file = Path(validated.output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if validated.export_format == 'csv':
            df.to_csv(output_file, index=False)
        elif validated.export_format == 'json':
            df.to_json(output_file, orient='records', indent=2)
        elif validated.export_format == 'parquet':
            df.to_parquet(output_file, index=False)
        elif validated.export_format == 'excel':
            df.to_excel(output_file, index=False)

        return jsonify({
            'status': 'success',
            'message': f'Data exported to {validated.export_format}',
            'data': {
                'output_file': str(output_file),
                'format': validated.export_format,
                'records_exported': len(df)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return jsonify({
            'status': 'error',
            'error_message': str(e)
        }), 500


@api_v1.route('/docs', methods=['GET'])
def api_docs():
    """API documentation"""
    docs = {
        'version': 'v1',
        'endpoints': {
            'generation': {
                'POST /api/v1/generate/patients': 'Generate synthetic patient data',
                'POST /api/v1/generate/vitals': 'Generate vital signs',
                'POST /api/v1/generate/batch': 'Generate complete dataset'
            },
            'privacy': {
                'POST /api/v1/privacy/apply': 'Apply differential privacy',
                'POST /api/v1/privacy/statistics': 'Compute private statistics'
            },
            'simulation': {
                'POST /api/v1/simulate/progression': 'Simulate disease progression'
            },
            'utility': {
                'POST /api/v1/export': 'Export data in various formats',
                'GET /api/v1/docs': 'API documentation'
            }
        }
    }
    return jsonify(docs)


# =============================================================================
# REGISTER ROUTES
# =============================================================================

def register_routes(app):
    """Register all API routes to the Flask app"""
    app.register_blueprint(api_v1)
    logger.info("API routes registered successfully")
