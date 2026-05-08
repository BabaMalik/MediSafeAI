"""
Data Generation Pipeline DAG
Automated pipeline for generating synthetic healthcare data
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
import pandas as pd
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, '/opt/airflow/src')

from src.data_generator.patient_generator import PatientGenerator
from src.data_generator.vitals_generator import VitalsGenerator
from src.data_generator.treatment_generator import TreatmentGenerator
from src.data_generator.disease_progression import DiseaseProgressionModel
from src.data_generator.temporal_patterns import TemporalPatternGenerator
from src.privacy.differential_privacy import DifferentialPrivacy
from src.utils.persistence import (
    save_patients_to_db, save_vitals_to_db, save_progression_to_db,
    save_privacy_operation
)


# Default arguments
default_args = {
    'owner': 'medisafe',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email': ['admin@medisafe.ai'],
}

# Create DAG
dag = DAG(
    'data_generation_pipeline',
    default_args=default_args,
    description='Generate synthetic healthcare data with privacy',
    schedule_interval='@weekly',  # Run weekly
    start_date=days_ago(1),
    catchup=False,
    tags=['data-generation', 'synthetic-data', 'privacy'],
)


# =============================================================================
# TASK FUNCTIONS
# =============================================================================

def generate_patients(**context):
    """Generate synthetic patient data"""
    num_patients = context['params'].get('num_patients', 10000)
    output_dir = Path('/opt/airflow/data/raw')
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating {num_patients} patients...")

    generator = PatientGenerator(num_patients=num_patients)
    patients_df = generator.generate_patients()

    # Save to CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'patients_{timestamp}.csv'
    patients_df.to_csv(output_file, index=False)

    print(f"Generated {len(patients_df)} patients -> {output_file}")

    # Push file path to XCom
    context['task_instance'].xcom_push(key='patients_file', value=str(output_file))

    return str(output_file)


def generate_vitals(**context):
    """Generate vital signs for patients"""
    # Get patients file from previous task
    ti = context['task_instance']
    patients_file = ti.xcom_pull(task_ids='generate_patients', key='patients_file')

    print(f"Loading patients from {patients_file}...")
    patients_df = pd.read_csv(patients_file)

    print(f"Generating vitals for {len(patients_df)} patients...")
    generator = VitalsGenerator()
    vitals_df = generator.generate_vitals(patients_df)

    # Save to CSV
    output_dir = Path(patients_file).parent
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'vitals_{timestamp}.csv'
    vitals_df.to_csv(output_file, index=False)

    print(f"Generated vitals for {len(vitals_df)} patients -> {output_file}")

    context['task_instance'].xcom_push(key='vitals_file', value=str(output_file))

    return str(output_file)


def generate_treatments(**context):
    """Generate treatment assignments"""
    ti = context['task_instance']
    patients_file = ti.xcom_pull(task_ids='generate_patients', key='patients_file')

    print(f"Loading patients from {patients_file}...")
    patients_df = pd.read_csv(patients_file)

    print(f"Generating treatments for {len(patients_df)} patients...")
    generator = TreatmentGenerator()
    treatments_df = generator.generate_treatments(patients_df)

    # Save to CSV
    output_dir = Path(patients_file).parent
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'treatments_{timestamp}.csv'
    treatments_df.to_csv(output_file, index=False)

    print(f"Generated treatments for {len(treatments_df)} patients -> {output_file}")

    context['task_instance'].xcom_push(key='treatments_file', value=str(output_file))

    return str(output_file)


def generate_progression(**context):
    """Generate disease progression for patients"""
    ti = context['task_instance']
    patients_file = ti.xcom_pull(task_ids='generate_patients', key='patients_file')
    num_visits = context['params'].get('num_visits', 12)
    interval = context['params'].get('interval', 30)

    print(f"Loading patients from {patients_file}...")
    patients_df = pd.read_csv(patients_file)

    print(f"Generating progression for {len(patients_df)} patients...")
    model = DiseaseProgressionModel()
    all_progression = []

    for _, patient in patients_df.iterrows():
        prog_df = model.simulate_progression(
            patient.to_dict(),
            num_visits=num_visits,
            time_interval_days=interval
        )
        all_progression.append(prog_df)

    progression_df = pd.concat(all_progression, ignore_index=True)

    # Save to CSV
    output_dir = Path(patients_file).parent
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'progression_{timestamp}.csv'
    progression_df.to_csv(output_file, index=False)

    print(f"Generated progression for {len(patients_df)} patients -> {output_file}")

    context['task_instance'].xcom_push(key='progression_file', value=str(output_file))

    return str(output_file)


def apply_temporal_patterns(**context):
    """Apply temporal patterns to vital signs"""
    ti = context['task_instance']
    vitals_file = ti.xcom_pull(task_ids='generate_vitals', key='vitals_file')
    metric = context['params'].get('metric', 'blood_glucose')
    pattern_type = context['params'].get('pattern_type', 'trend')

    print(f"Loading vitals from {vitals_file}...")
    vitals_df = pd.read_csv(vitals_file)

    if 'visit_date' in vitals_df.columns:
        vitals_df['visit_date'] = pd.to_datetime(vitals_df['visit_date'])

    print(f"Applying {pattern_type} pattern to {metric}...")
    generator = TemporalPatternGenerator()

    if pattern_type == 'trend':
        vitals_df = generator.apply_trends(vitals_df, metric=metric)
    elif pattern_type == 'anomaly':
        vitals_df = generator.inject_anomalies(vitals_df, metrics=[metric])
    elif pattern_type == 'seasonal':
        vitals_df = generator.add_cyclic_patterns(vitals_df, metric=metric)

    # Save to CSV
    output_dir = Path(vitals_file).parent
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'vitals_with_patterns_{timestamp}.csv'
    vitals_df.to_csv(output_file, index=False)

    print(f"Applied temporal patterns -> {output_file}")

    context['task_instance'].xcom_push(key='vitals_with_patterns_file', value=str(output_file))

    return str(output_file)


def persist_to_database(**context):
    """Persist generated data to the database"""
    ti = context['task_instance']
    patients_file = ti.xcom_pull(task_ids='generate_patients', key='patients_file')
    vitals_file = ti.xcom_pull(task_ids='generate_vitals', key='vitals_file')
    vitals_patterns_file = ti.xcom_pull(task_ids='apply_patterns', key='vitals_with_patterns_file')
    progression_file = ti.xcom_pull(task_ids='generate_progression', key='progression_file')
    private_file = ti.xcom_pull(task_ids='apply_privacy', key='private_file')

    epsilon = context['params'].get('epsilon', 1.0)
    delta = context['params'].get('delta', 1e-5)

    print("Persisting data to database...")

    # Persist patients
    patients_df = pd.read_csv(patients_file)
    save_patients_to_db(patients_df)

    # Persist vitals (use vitals with patterns if available)
    final_vitals_file = vitals_patterns_file if vitals_patterns_file else vitals_file
    print(f"Persisting vitals from {final_vitals_file}...")
    vitals_df = pd.read_csv(final_vitals_file)
    save_vitals_to_db(vitals_df)

    # Persist progression if it exists
    if progression_file:
        progression_df = pd.read_csv(progression_file)
        save_progression_to_db(progression_df)

    # Log privacy operation
    if private_file:
        save_privacy_operation(
            epsilon=epsilon,
            delta=delta,
            operation_type='privatize_dataframe',
            data_source=patients_file,
            num_records=len(patients_df),
            output_file=private_file
        )

    print("Data persistence complete.")
    return True


def apply_differential_privacy(**context):
    """Apply differential privacy to patient data"""
    ti = context['task_instance']
    patients_file = ti.xcom_pull(task_ids='generate_patients', key='patients_file')

    epsilon = context['params'].get('epsilon', 1.0)
    delta = context['params'].get('delta', 1e-5)

    print(f"Loading patients from {patients_file}...")
    patients_df = pd.read_csv(patients_file)

    print(f"Applying differential privacy (ε={epsilon}, δ={delta})...")
    dp = DifferentialPrivacy(epsilon=epsilon, delta=delta)

    private_df = dp.privatize_dataframe(
        patients_df,
        numeric_columns=['age', 'income'],
        categorical_columns=['insurance']
    )

    # Save to private directory
    output_dir = Path('/opt/airflow/data/private')
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'patients_private_{timestamp}.csv'
    private_df.to_csv(output_file, index=False)

    print(f"Applied privacy to {len(private_df)} records -> {output_file}")

    context['task_instance'].xcom_push(key='private_file', value=str(output_file))

    return str(output_file)


def validate_data(**context):
    """Validate generated data quality"""
    ti = context['task_instance']
    patients_file = ti.xcom_pull(task_ids='generate_patients', key='patients_file')
    vitals_file = ti.xcom_pull(task_ids='generate_vitals', key='vitals_file')

    print("Validating data quality...")

    # Load data
    patients_df = pd.read_csv(patients_file)
    vitals_df = pd.read_csv(vitals_file)

    # Validation checks
    checks_passed = []
    checks_failed = []

    # Check 1: No missing patient IDs
    if not patients_df['patient_id'].isnull().any():
        checks_passed.append("✓ No missing patient IDs")
    else:
        checks_failed.append("✗ Missing patient IDs found")

    # Check 2: Age ranges valid
    if (patients_df['age'] >= 0).all() and (patients_df['age'] <= 120).all():
        checks_passed.append("✓ Age ranges valid")
    else:
        checks_failed.append("✗ Invalid age ranges")

    # Check 3: Vitals match patients
    if len(vitals_df) == len(patients_df):
        checks_passed.append("✓ Vitals count matches patients")
    else:
        checks_failed.append(f"✗ Vitals count mismatch: {len(vitals_df)} vs {len(patients_df)}")

    # Check 4: Blood pressure ranges
    bp_systolic_valid = (vitals_df['blood_pressure_systolic'] >= 60).all() and \
                       (vitals_df['blood_pressure_systolic'] <= 250).all()
    if bp_systolic_valid:
        checks_passed.append("✓ Blood pressure ranges valid")
    else:
        checks_failed.append("✗ Invalid blood pressure ranges")

    # Print results
    print("\n=== Data Validation Results ===")
    for check in checks_passed:
        print(check)
    for check in checks_failed:
        print(check)

    if checks_failed:
        raise ValueError(f"Data validation failed: {len(checks_failed)} checks failed")

    print(f"\n✓ All validation checks passed ({len(checks_passed)} checks)")

    return True


def generate_summary_report(**context):
    """Generate summary report of pipeline execution"""
    ti = context['task_instance']

    patients_file = ti.xcom_pull(task_ids='generate_patients', key='patients_file')
    vitals_file = ti.xcom_pull(task_ids='generate_vitals', key='vitals_file')
    treatments_file = ti.xcom_pull(task_ids='generate_treatments', key='treatments_file')
    private_file = ti.xcom_pull(task_ids='apply_privacy', key='private_file')

    # Load data
    patients_df = pd.read_csv(patients_file)

    # Generate report
    report = f"""
    ========================================
    MediSafeAI Data Generation Summary
    ========================================
    Execution Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

    Files Generated:
    - Patients:   {patients_file} ({len(patients_df)} records)
    - Vitals:     {vitals_file}
    - Treatments: {treatments_file}
    - Private:    {private_file}

    Patient Demographics:
    - Total patients: {len(patients_df)}
    - Male: {len(patients_df[patients_df['gender'] == 'M'])}
    - Female: {len(patients_df[patients_df['gender'] == 'F'])}
    - Average age: {patients_df['age'].mean():.1f} years
    - Diabetes: {patients_df['diabetes'].sum()} ({patients_df['diabetes'].mean()*100:.1f}%)
    - Hypertension: {patients_df['hypertension'].sum()} ({patients_df['hypertension'].mean()*100:.1f}%)
    - Heart disease: {patients_df['heart_disease'].sum()} ({patients_df['heart_disease'].mean()*100:.1f}%)

    Insurance Distribution:
    {patients_df['insurance'].value_counts().to_string()}

    ========================================
    """

    print(report)

    # Save report
    output_dir = Path(patients_file).parent
    report_file = output_dir / f'pipeline_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    report_file.write_text(report)

    print(f"\nReport saved to: {report_file}")

    return str(report_file)


# =============================================================================
# DEFINE TASKS
# =============================================================================

task_generate_patients = PythonOperator(
    task_id='generate_patients',
    python_callable=generate_patients,
    params={'num_patients': 10000},
    dag=dag,
)

task_generate_vitals = PythonOperator(
    task_id='generate_vitals',
    python_callable=generate_vitals,
    dag=dag,
)

task_generate_treatments = PythonOperator(
    task_id='generate_treatments',
    python_callable=generate_treatments,
    dag=dag,
)

task_generate_progression = PythonOperator(
    task_id='generate_progression',
    python_callable=generate_progression,
    params={'num_visits': 12, 'interval': 30},
    dag=dag,
)

task_apply_patterns = PythonOperator(
    task_id='apply_patterns',
    python_callable=apply_temporal_patterns,
    params={'metric': 'blood_glucose', 'pattern_type': 'trend'},
    dag=dag,
)

task_persist_db = PythonOperator(
    task_id='persist_to_db',
    python_callable=persist_to_database,
    params={'epsilon': 1.0, 'delta': 1e-5},
    dag=dag,
)

task_apply_privacy = PythonOperator(
    task_id='apply_privacy',
    python_callable=apply_differential_privacy,
    params={'epsilon': 1.0, 'delta': 1e-5},
    dag=dag,
)

task_validate_data = PythonOperator(
    task_id='validate_data',
    python_callable=validate_data,
    dag=dag,
)

task_generate_report = PythonOperator(
    task_id='generate_report',
    python_callable=generate_summary_report,
    dag=dag,
)

# =============================================================================
# DEFINE TASK DEPENDENCIES
# =============================================================================

# Patients must be generated first
task_generate_patients >> [task_generate_vitals, task_generate_treatments, task_generate_progression, task_apply_privacy]

# Vitals can have temporal patterns applied
task_generate_vitals >> task_apply_patterns

# Validate after vitals are generated
task_generate_vitals >> task_validate_data

# Persist to database after generation and transformation steps
[task_generate_patients, task_generate_vitals, task_apply_patterns, task_generate_progression, task_apply_privacy] >> task_persist_db

# Generate report after all tasks complete
[task_generate_treatments, task_apply_privacy, task_validate_data, task_persist_db] >> task_generate_report
