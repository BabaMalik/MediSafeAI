# MediSafeAI

> Privacy-first synthetic healthcare data generation platform with differential privacy, disease simulation, and HIPAA-compliant analytics.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What is MediSafeAI?

MediSafeAI generates **realistic synthetic patient data** that looks and behaves like real healthcare data — without exposing any real patient information. It solves a core problem in healthcare AI: you need data to build models, but real patient data is heavily regulated under HIPAA.

The platform provides:

- **Synthetic patient generation** with demographically realistic distributions (age-correlated disease probabilities, gender-adjusted risk factors, log-normal income distributions)
- **Differential privacy** (Laplace and Gaussian mechanisms) so that even synthetic data can be shared safely with mathematically provable privacy guarantees
- **Disease progression simulation** that models how conditions like diabetes, hypertension, and heart disease evolve over time with realistic vital sign trajectories and intervention effects
- **Treatment assignment** that maps patient conditions to appropriate medication protocols
- **Temporal pattern injection** to add trends, anomalies, and seasonal cycles to time-series health data

All of this is accessible through a **REST API**, a **CLI**, and **Airflow DAGs** for scheduled pipeline execution, with full **audit logging** for HIPAA compliance tracking.

## Architecture

```
MediSafeAI/
├── src/
│   ├── data_generator/          # Synthetic data generation
│   │   ├── patient_generator.py    # Patient demographics
│   │   ├── vitals_generator.py     # Vital signs (BP, heart rate, glucose, etc.)
│   │   ├── disease_progression.py  # Longitudinal disease simulation
│   │   ├── treatment_generator.py  # Medication assignment
│   │   └── temporal_patterns.py    # Trends, anomalies, seasonal cycles
│   ├── privacy/                 # Differential privacy engine
│   │   └── differential_privacy.py # Laplace/Gaussian noise, randomized response
│   ├── api/                     # Flask REST API
│   ├── cli/                     # Click-based CLI
│   ├── airflow/dags/            # Scheduled data pipelines
│   ├── models/                  # SQLAlchemy models (Patient, Vitals, Audit)
│   ├── config/                  # Environment-based configuration
│   └── utils/                   # Logging, Pydantic schemas
├── tests/                       # Test suite
├── data/                        # Generated data output
├── notebooks/                   # Jupyter notebooks
├── docker/                      # Dockerfiles
├── docker-compose.yml           # Full stack: PostgreSQL, Redis, Airflow, API
└── .github/workflows/           # CI/CD pipelines
```

## Quick Start

### Installation

```bash
git clone https://github.com/BabaMalik/MediSafeAI.git
cd MediSafeAI
python -m venv venv
source venv/bin/activate
pip install -e .
```

### Generate Patients

```python
from src.data_generator.patient_generator import PatientGenerator

generator = PatientGenerator(seed=42)
patients_df = generator.generate_patients(n_patients=1000)
patients_df.to_csv('data/raw/patients.csv', index=False)
```

### Generate Vitals

```python
from src.data_generator.vitals_generator import VitalsGenerator

vitals_gen = VitalsGenerator()
vitals_df = vitals_gen.generate_vitals(patients_df)
```

### Apply Differential Privacy

```python
from src.privacy.differential_privacy import DifferentialPrivacy

dp = DifferentialPrivacy(epsilon=1.0, delta=1e-5)
private_df = dp.privatize_dataframe(
    patients_df,
    numeric_columns=['age', 'income'],
    categorical_columns=['insurance']
)

# Compute private statistics
stats = dp.compute_private_statistics(patients_df['age'], stats=['mean', 'variance', 'count'])
```

### Simulate Disease Progression

```python
from src.data_generator.disease_progression import DiseaseProgressionModel

model = DiseaseProgressionModel()
progression_df = model.simulate_progression(
    patients_df.iloc[0],
    num_visits=12,
    time_interval_days=30
)
```

## CLI Usage

```bash
# Generate patient data
medisafe generate patients --count 10000 --output data/raw/patients.csv

# Generate vitals
medisafe generate vitals --input data/raw/patients.csv --output data/raw/vitals.csv

# Apply differential privacy
medisafe privacy apply --input data/raw/patients.csv --epsilon 1.0 --output data/private/patients.csv

# Compute private statistics
medisafe privacy stats --input data/raw/patients.csv --column age --epsilon 1.0

# Simulate disease progression
medisafe simulate progression --patient-id PT000001 --input data/raw/patients.csv --visits 12

# Start API server
medisafe serve --host 0.0.0.0 --port 5000
```

## REST API

```bash
# Generate patients
curl -X POST http://localhost:5000/api/v1/generate/patients \
  -H "Content-Type: application/json" \
  -d '{"num_patients": 100}'

# Apply differential privacy
curl -X POST http://localhost:5000/api/v1/privacy/apply \
  -H "Content-Type: application/json" \
  -d '{"input_file": "data/raw/patients.csv", "numeric_columns": ["age", "income"], "privacy_config": {"epsilon": 1.0}}'

# Compute private statistics
curl -X POST http://localhost:5000/api/v1/privacy/statistics \
  -H "Content-Type: application/json" \
  -d '{"input_file": "data/raw/patients.csv", "column": "age"}'

# Simulate disease progression
curl -X POST http://localhost:5000/api/v1/simulate/progression \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "PT000001", "num_visits": 12, "time_interval_days": 30}'

# Health check
curl http://localhost:5000/health

# API docs
curl http://localhost:5000/api/v1/docs
```

## Docker Deployment

```bash
# Start full stack (PostgreSQL, Redis, Airflow, API, Jupyter)
docker-compose up -d

# Services:
#   API:      http://localhost:5000
#   Airflow:  http://localhost:8080
#   Jupyter:  http://localhost:8888
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Privacy settings
DEFAULT_EPSILON=1.0        # Privacy budget (lower = more private)
DEFAULT_DELTA=1e-5         # Privacy violation probability

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/medisafe_db

# API
API_HOST=0.0.0.0
API_PORT=5000
```

### Privacy Budget Guidelines

| Use Case | Epsilon | Privacy Level |
|----------|---------|---------------|
| External data sharing | < 1.0 | Strong |
| Internal analytics | 1.0 - 5.0 | Moderate |
| Low-sensitivity reports | > 5.0 | Weak |

## Development

```bash
# Run tests
pytest --cov=src --cov-report=html

# Code formatting
black src/ tests/

# Linting
flake8 src/ tests/
```

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contact

- **Author**: BabaMalik
- **Email**: babamalik206@gmail.com
- **Issues**: [GitHub Issues](https://github.com/BabaMalik/MediSafeAI/issues)

---

**Disclaimer**: This software generates synthetic data for research and development purposes only. It is not intended for clinical use or as a substitute for real patient data in production healthcare systems.
