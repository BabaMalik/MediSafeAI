"""
Main CLI Entry Point
Provides command-line interface for MediSafeAI operations
"""

import sys
import click
from pathlib import Path
from typing import Optional

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data_generator.patient_generator import PatientGenerator
from src.data_generator.vitals_generator import VitalsGenerator
from src.data_generator.disease_progression import DiseaseProgressionModel
from src.data_generator.treatment_generator import TreatmentGenerator
from src.privacy.differential_privacy import DifferentialPrivacy
from src.config.settings import settings
from src.utils.logger import setup_logging, get_logger
from src.models.base import init_db, reset_db

import pandas as pd

logger = get_logger(__name__)


@click.group()
@click.option('--log-level', default='INFO', help='Logging level')
@click.option('--config-file', default=None, help='Path to config file')
@click.version_option(version=settings.APP_VERSION)
def cli(log_level, config_file):
    """MediSafeAI - Privacy-First Healthcare Analytics CLI"""
    setup_logging(log_level=log_level)
    logger.info(f"MediSafeAI v{settings.APP_VERSION}")


# =============================================================================
# GENERATE COMMANDS
# =============================================================================

@cli.group()
def generate():
    """Generate synthetic healthcare data"""
    pass


@generate.command()
@click.option('--count', '-n', default=1000, help='Number of patients to generate')
@click.option('--output', '-o', default='data/raw/patients.csv', help='Output file path')
@click.option('--seed', default=None, type=int, help='Random seed for reproducibility')
def patients(count, output, seed):
    """Generate synthetic patient data"""
    click.echo(f"Generating {count} patients...")

    try:
        generator = PatientGenerator(num_patients=count, seed=seed)
        df = generator.generate_patients()

        # Ensure output directory exists
        Path(output).parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(output, index=False)
        click.echo(f"✓ Generated {len(df)} patient records")
        click.echo(f"✓ Saved to: {output}")
    except Exception as e:
        logger.error(f"Error generating patients: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@generate.command()
@click.option('--input', '-i', required=True, help='Input patients CSV file')
@click.option('--output', '-o', default='data/raw/vitals.csv', help='Output file path')
def vitals(input, output):
    """Generate vital signs for patients"""
    click.echo(f"Generating vitals from {input}...")

    try:
        patients_df = pd.read_csv(input)
        click.echo(f"Loaded {len(patients_df)} patients")

        generator = VitalsGenerator()
        vitals_df = generator.generate_vitals(patients_df)

        # Ensure output directory exists
        Path(output).parent.mkdir(parents=True, exist_ok=True)

        vitals_df.to_csv(output, index=False)
        click.echo(f"✓ Generated vitals for {len(vitals_df)} patients")
        click.echo(f"✓ Saved to: {output}")
    except Exception as e:
        logger.error(f"Error generating vitals: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@generate.command()
@click.option('--input', '-i', required=True, help='Input patients CSV file')
@click.option('--output', '-o', default='data/raw/treatments.csv', help='Output file path')
def treatments(input, output):
    """Generate treatment assignments for patients"""
    click.echo(f"Generating treatments from {input}...")

    try:
        patients_df = pd.read_csv(input)
        click.echo(f"Loaded {len(patients_df)} patients")

        generator = TreatmentGenerator()
        treatments_df = generator.generate_treatments(patients_df)

        # Ensure output directory exists
        Path(output).parent.mkdir(parents=True, exist_ok=True)

        treatments_df.to_csv(output, index=False)
        click.echo(f"✓ Generated treatments for {len(treatments_df)} patients")
        click.echo(f"✓ Saved to: {output}")
    except Exception as e:
        logger.error(f"Error generating treatments: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


# =============================================================================
# PRIVACY COMMANDS
# =============================================================================

@cli.group()
def privacy():
    """Apply differential privacy to data"""
    pass


@privacy.command()
@click.option('--input', '-i', required=True, help='Input CSV file')
@click.option('--output', '-o', required=True, help='Output CSV file')
@click.option('--epsilon', '-e', default=1.0, help='Privacy budget (epsilon)')
@click.option('--delta', '-d', default=1e-5, help='Privacy parameter (delta)')
@click.option('--columns', '-c', multiple=True, help='Columns to privatize')
def apply(input, output, epsilon, delta, columns):
    """Apply differential privacy to a dataset"""
    click.echo(f"Applying differential privacy (ε={epsilon}, δ={delta})...")

    try:
        df = pd.read_csv(input)
        click.echo(f"Loaded {len(df)} records from {input}")

        dp = DifferentialPrivacy(epsilon=epsilon, delta=delta)

        # Determine columns to privatize
        if not columns:
            # Default: privatize all numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            columns = numeric_cols
        else:
            columns = list(columns)

        click.echo(f"Privatizing columns: {', '.join(columns)}")

        private_df = dp.privatize_dataframe(df, numeric_columns=columns)

        # Ensure output directory exists
        Path(output).parent.mkdir(parents=True, exist_ok=True)

        private_df.to_csv(output, index=False)
        click.echo(f"✓ Applied differential privacy")
        click.echo(f"✓ Saved to: {output}")
    except Exception as e:
        logger.error(f"Error applying privacy: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@privacy.command()
@click.option('--input', '-i', required=True, help='Input CSV file')
@click.option('--column', '-c', required=True, help='Column to analyze')
@click.option('--epsilon', '-e', default=1.0, help='Privacy budget')
@click.option('--delta', '-d', default=1e-5, help='Privacy parameter')
def stats(input, column, epsilon, delta):
    """Compute private statistics for a column"""
    click.echo(f"Computing private statistics for {column}...")

    try:
        df = pd.read_csv(input)
        data = df[column].values

        dp = DifferentialPrivacy(epsilon=epsilon, delta=delta)

        mean_val = dp.private_mean(data)
        var_val = dp.private_variance(data)
        count_val = dp.private_count(data)

        click.echo("\nPrivate Statistics:")
        click.echo(f"  Mean:     {mean_val:.2f}")
        click.echo(f"  Variance: {var_val:.2f}")
        click.echo(f"  Std Dev:  {var_val**0.5:.2f}")
        click.echo(f"  Count:    {count_val:.0f}")
        click.echo(f"\n  Privacy budget: ε={epsilon}, δ={delta}")
    except Exception as e:
        logger.error(f"Error computing statistics: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


# =============================================================================
# SIMULATE COMMANDS
# =============================================================================

@cli.group()
def simulate():
    """Simulate disease progression"""
    pass


@simulate.command()
@click.option('--patient-id', '-p', required=True, help='Patient ID')
@click.option('--input', '-i', required=True, help='Input patients CSV file')
@click.option('--output', '-o', default='data/raw/progression.csv', help='Output file path')
@click.option('--visits', '-v', default=12, help='Number of visits')
@click.option('--interval', default=30, help='Days between visits')
def progression(patient_id, input, output, visits, interval):
    """Simulate disease progression for a patient"""
    click.echo(f"Simulating progression for patient {patient_id}...")

    try:
        patients_df = pd.read_csv(input)
        patient = patients_df[patients_df['patient_id'] == patient_id]

        if patient.empty:
            click.echo(f"✗ Patient {patient_id} not found", err=True)
            sys.exit(1)

        model = DiseaseProgressionModel()
        progression_df = model.simulate_progression(
            patient.iloc[0],
            num_visits=visits,
            time_interval_days=interval
        )

        # Ensure output directory exists
        Path(output).parent.mkdir(parents=True, exist_ok=True)

        progression_df.to_csv(output, index=False)
        click.echo(f"✓ Simulated {len(progression_df)} visits")
        click.echo(f"✓ Saved to: {output}")
    except Exception as e:
        logger.error(f"Error simulating progression: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


# =============================================================================
# DATABASE COMMANDS
# =============================================================================

@cli.group()
def db():
    """Database management commands"""
    pass


@db.command()
def init():
    """Initialize database tables"""
    click.echo("Initializing database...")

    try:
        init_db()
        click.echo("✓ Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@db.command()
@click.confirmation_option(prompt='Are you sure you want to reset the database?')
def reset():
    """Reset database (drop and recreate all tables)"""
    click.echo("Resetting database...")

    try:
        reset_db()
        click.echo("✓ Database reset successfully")
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


# =============================================================================
# SERVER COMMANDS
# =============================================================================

@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=5000, help='Port to bind to')
@click.option('--workers', default=4, help='Number of worker processes')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
def serve(host, port, workers, reload):
    """Start the API server"""
    click.echo(f"Starting MediSafeAI API server on {host}:{port}...")

    try:
        from src.api.app import app

        if reload:
            app.run(host=host, port=port, debug=True)
        else:
            import gunicorn.app.base

            class StandaloneApplication(gunicorn.app.base.BaseApplication):
                def __init__(self, app, options=None):
                    self.options = options or {}
                    self.application = app
                    super().__init__()

                def load_config(self):
                    for key, value in self.options.items():
                        self.cfg.set(key.lower(), value)

                def load(self):
                    return self.application

            options = {
                'bind': f'{host}:{port}',
                'workers': workers,
                'timeout': 300,
            }
            StandaloneApplication(app, options).run()
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


# =============================================================================
# UTILITY COMMANDS
# =============================================================================

@cli.command()
def version():
    """Show version information"""
    click.echo(f"MediSafeAI version {settings.APP_VERSION}")
    click.echo(f"Environment: {settings.APP_ENV}")
    click.echo(f"Python: {sys.version}")


@cli.command()
def config():
    """Show current configuration"""
    click.echo("Current Configuration:")
    click.echo(f"  Environment: {settings.APP_ENV}")
    click.echo(f"  Debug: {settings.DEBUG}")
    click.echo(f"  Log Level: {settings.LOG_LEVEL}")
    click.echo(f"  Database: {settings.DATABASE_URL.split('@')[-1]}")
    click.echo(f"  Default Epsilon: {settings.DEFAULT_EPSILON}")
    click.echo(f"  Default Delta: {settings.DEFAULT_DELTA}")
    click.echo(f"  Data Directory: {settings.DATA_DIR}")


def main():
    """Main entry point"""
    cli()


if __name__ == '__main__':
    main()
