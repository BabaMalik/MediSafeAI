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
from src.data_generator.temporal_patterns import TemporalPatternGenerator
from src.privacy.differential_privacy import DifferentialPrivacy
from src.utils.logger import get_logger, get_audit_logger
from src.utils.schemas import (
    PatientCreate, PrivacyRequest, DiseaseProgressionRequest,
    ExportRequest, BatchGenerationRequest, TemporalPatternRequest,
    MLTrainRequest, MLPredictRequest, MLPredictionResponse
)
from src.utils.persistence import (
    save_patients_to_db, save_vitals_to_db, save_progression_to_db,
    save_privacy_operation, safe_path
)
from src.ml.predictor import DiseasePredictor, VitalsForecaster
from src.ml.manager import ModelManager
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

        # Save to database
        try:
            save_patients_to_db(patients_df)
        except Exception as e:
            logger.error(f"Failed to save patients to database: {e}")

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


@api_v1.route('/generate/temporal', methods=['POST'])
def generate_temporal():
    """Apply temporal patterns to a dataset"""
    try:
        data = request.get_json()
        validated = TemporalPatternRequest(**data)

        logger.info(f"Applying {validated.pattern_type} pattern to {validated.column}")

        # Load data safely
        df = pd.read_csv(safe_path(validated.input_file))

        # Ensure date columns are datetime objects if they exist
        if 'visit_date' in df.columns:
            df['visit_date'] = pd.to_datetime(df['visit_date'])

        generator = TemporalPatternGenerator()

        if validated.pattern_type == 'trend':
            df = generator.apply_trends(
                df,
                metric=validated.column,
                trend=validated.parameters.get('trend', 'increase')
            )
        elif validated.pattern_type == 'anomaly':
            generator.anomaly_rate = validated.parameters.get('anomaly_rate', 0.1)
            df = generator.inject_anomalies(df, metrics=[validated.column])
        elif validated.pattern_type == 'seasonal':
            df = generator.add_cyclic_patterns(
                df,
                metric=validated.column,
                amplitude=validated.parameters.get('amplitude', 5),
                period_days=validated.parameters.get('period_days', 90)
            )

        # Save to file
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        output_file = settings.DATA_OUTPUT_DIR / f"temporal_{timestamp}.csv"
        df.to_csv(output_file, index=False)

        return jsonify({
            'status': 'success',
            'message': f'Applied {validated.pattern_type} pattern to {validated.column}',
            'data': {
                'file_path': str(output_file),
                'pattern_type': validated.pattern_type,
                'column': validated.column
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error applying temporal patterns: {e}")
        return jsonify({
            'status': 'error',
            'error_message': str(e)
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

        # Load patients safely
        patients_df = pd.read_csv(safe_path(input_file))
        logger.info(f"Loaded {len(patients_df)} patients from {input_file}")

        # Generate vitals
        generator = VitalsGenerator()
        vitals_df = generator.generate_vitals(patients_df)

        # Save to file
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        output_file = settings.DATA_OUTPUT_DIR / f"vitals_{timestamp}.csv"
        vitals_df.to_csv(output_file, index=False)

        # Save to database
        try:
            save_vitals_to_db(vitals_df)
        except Exception as e:
            logger.error(f"Failed to save vitals to database: {e}")

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

        try:
            save_patients_to_db(patients_df)
        except Exception as e:
            logger.error(f"Failed to save patients to database: {e}")

        files_generated = {'patients': str(patients_file)}

        # Generate vitals if requested
        if validated.include_vitals:
            vitals_gen = VitalsGenerator()
            vitals_df = vitals_gen.generate_vitals(patients_df)
            vitals_file = output_dir / f"vitals_{timestamp}.csv"
            vitals_df.to_csv(vitals_file, index=False)

            try:
                save_vitals_to_db(vitals_df)
            except Exception as e:
                logger.error(f"Failed to save vitals to database: {e}")

            files_generated['vitals'] = str(vitals_file)

        # Generate progression if requested
        if validated.include_progression:
            progression_model = DiseaseProgressionModel()
            all_progression = []
            for _, patient in patients_df.iterrows():
                prog_df = progression_model.simulate_progression(
                    patient.to_dict(),
                    num_visits=settings.DEFAULT_NUM_VISITS,
                    time_interval_days=settings.DEFAULT_TIME_INTERVAL_DAYS
                )
                all_progression.append(prog_df)

            if all_progression:
                progression_df = pd.concat(all_progression, ignore_index=True)
                progression_file = output_dir / f"progression_{timestamp}.csv"
                progression_df.to_csv(progression_file, index=False)

                try:
                    save_progression_to_db(progression_df)
                except Exception as e:
                    logger.error(f"Failed to save progression to database: {e}")

                files_generated['progression'] = str(progression_file)

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

        # Load data safely
        df = pd.read_csv(safe_path(validated.input_file))

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

        # Save output safely
        if validated.output_file:
            output_file = str(safe_path(validated.output_file))
        else:
            output_file = str(settings.DATA_PRIVATE_DIR / f"private_{Path(validated.input_file).name}")

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

        # Save to database
        try:
            save_privacy_operation(
                epsilon=validated.privacy_config.epsilon,
                delta=validated.privacy_config.delta,
                operation_type='privatize_dataframe',
                data_source=validated.input_file,
                mechanism=validated.privacy_config.mechanism.value,
                columns_affected=validated.numeric_columns + (validated.categorical_columns or []),
                num_records=len(df),
                output_file=output_file
            )
        except Exception as e:
            logger.error(f"Failed to save privacy operation to database: {e}")

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

        # Load data safely
        df = pd.read_csv(safe_path(input_file))
        column_data = df[column].values

        # Compute private statistics
        dp = DifferentialPrivacy(epsilon=epsilon, delta=delta)

        stats = {
            'mean': dp.private_mean(column_data),
            'variance': dp.private_variance(column_data),
            'count': dp.private_count(column_data)
        }
        stats['std'] = stats['variance'] ** 0.5

        # Save to database
        try:
            save_privacy_operation(
                epsilon=epsilon,
                delta=delta,
                operation_type='compute_statistics',
                data_source=input_file,
                columns_affected=[column],
                num_records=len(df),
                statistics=stats
            )
        except Exception as e:
            logger.error(f"Failed to save privacy statistics to database: {e}")

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
# MACHINE LEARNING ENDPOINTS
# =============================================================================

@api_v1.route('/ml/train', methods=['POST'])
def train_model():
    """Train an ML model on generated data"""
    try:
        data = request.get_json()
        validated = MLTrainRequest(**data)

        logger.info(f"Training {validated.model_type} for target {validated.target_column}")

        # In a real scenario, we would load from DB.
        # Here we'll try to find a relevant CSV file in raw data dir as a fallback.
        data_file = settings.DATA_OUTPUT_DIR / "patients.csv"
        if not data_file.exists():
             # Find any patient file
             files = list(settings.DATA_OUTPUT_DIR.glob("patients_*.csv"))
             if files:
                 data_file = files[0]
             else:
                 return jsonify({
                     'status': 'error',
                     'error_message': 'No training data found. Please generate patients first.'
                 }), 400

        df = pd.read_csv(data_file)

        if validated.model_type == 'disease_predictor':
            model = DiseasePredictor()
        else:
            model = VitalsForecaster()

        results = model.train(df, validated.target_column, validated.feature_columns)

        # Save model
        manager = ModelManager()
        manager.save_model(model, validated.model_type.value)

        return jsonify({
            'status': 'success',
            'message': f'Model {validated.model_type} trained successfully',
            'data': {
                'training_results': results,
                'model_name': validated.model_type.value
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error training model: {e}")
        return jsonify({
            'status': 'error',
            'error_message': str(e)
        }), 500


@api_v1.route('/ml/predict', methods=['POST'])
def predict():
    """Get prediction from a trained model"""
    try:
        data = request.get_json()
        validated = MLPredictRequest(**data)

        manager = ModelManager()
        if not manager.exists(validated.model_type.value):
            return jsonify({
                'status': 'error',
                'error_message': f'Model {validated.model_type} not found. Please train it first.'
            }), 404

        model = manager.load_model(validated.model_type.value)
        prediction_results = model.predict(validated.features)

        response = MLPredictionResponse(
            model_type=validated.model_type.value,
            prediction=prediction_results['prediction'],
            probability=prediction_results.get('probability')
        )

        return jsonify({
            'status': 'success',
            'data': response.dict(),
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error in prediction: {e}")
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

        # Save to database
        try:
            save_progression_to_db(progression_df)
        except Exception as e:
            logger.error(f"Failed to save progression to database: {e}")

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

        # Load data safely
        df = pd.read_csv(safe_path(validated.input_file))

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

        # Export based on format safely
        output_file = safe_path(validated.output_file)
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
                'POST /api/v1/generate/temporal': 'Apply temporal patterns to data',
                'POST /api/v1/generate/batch': 'Generate complete dataset'
            },
            'privacy': {
                'POST /api/v1/privacy/apply': 'Apply differential privacy',
                'POST /api/v1/privacy/statistics': 'Compute private statistics'
            },
            'simulation': {
                'POST /api/v1/simulate/progression': 'Simulate disease progression'
            },
            'ml': {
                'POST /api/v1/ml/train': 'Train an ML model',
                'POST /api/v1/ml/predict': 'Get model predictions'
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
