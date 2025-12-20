# MediSafeAI

> A privacy-first predictive healthcare analytics system with Airflow orchestration, Spark processing, and ML-driven insights.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

MediSafeAI is a comprehensive healthcare analytics platform designed to generate synthetic patient data while ensuring HIPAA compliance through differential privacy techniques. The system simulates realistic healthcare scenarios including patient demographics, vital signs, disease progression, and treatment protocols.

### Key Features

- **Synthetic Data Generation**: Create realistic healthcare datasets without exposing real patient information
- **Differential Privacy**: Implement ε-differential privacy with configurable privacy budgets
- **Disease Simulation**: Model disease progression over time with intervention effects
- **Temporal Patterns**: Add trends, anomalies, and seasonal variations to data
- **Airflow Orchestration**: Automate data pipelines and ML workflows
- **REST API**: Programmatic access to data generation and privacy operations
- **Docker Support**: Containerized deployment for reproducibility

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose (optional, for containerized deployment)
- PostgreSQL (optional, for Airflow metadata)

### Local Installation

```bash
# Clone the repository
git clone https://github.com/BabaMalik/MediSafeAI.git
cd MediSafeAI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt
```

### Docker Installation

```bash
# Build and start all services
docker-compose up -d

# Access Airflow UI at http://localhost:8080
# Access API at http://localhost:5000
```

## Quick Start

### Generate Synthetic Patient Data

```python
from src.data_generator.patient_generator import PatientGenerator

# Generate 1000 synthetic patients
generator = PatientGenerator(num_patients=1000)
patients_df = generator.generate_patients()

# Save to CSV
patients_df.to_csv('data/raw/patients.csv', index=False)
print(f"Generated {len(patients_df)} patient records")
```

### Add Vital Signs

```python
from src.data_generator.vitals_generator import VitalsGenerator

vitals_gen = VitalsGenerator()
vitals_df = vitals_gen.generate_vitals(patients_df)

print(vitals_df.head())
```

### Apply Differential Privacy

```python
from src.privacy.differential_privacy import DifferentialPrivacy

# Initialize with privacy budget
dp = DifferentialPrivacy(epsilon=1.0, delta=1e-5)

# Privatize numeric columns
private_df = dp.privatize_dataframe(
    patients_df,
    numeric_columns=['age', 'income'],
    categorical_columns=['insurance']
)

# Compute private statistics
private_mean_age = dp.private_mean(patients_df['age'].values)
print(f"Private mean age: {private_mean_age:.2f}")
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

print(progression_df[['visit_date', 'blood_pressure_systolic', 'blood_glucose']])
```

## Usage

### Command Line Interface

```bash
# Generate patient data
medisafe generate patients --count 10000 --output data/raw/patients.csv

# Generate vitals data
medisafe generate vitals --input data/raw/patients.csv --output data/raw/vitals.csv

# Apply differential privacy
medisafe privacy apply --input data/raw/patients.csv --epsilon 1.0 --output data/private/patients.csv

# Simulate disease progression
medisafe simulate progression --patient-id PT000001 --visits 12 --output data/progression.csv

# Start API server
medisafe serve --host 0.0.0.0 --port 5000
```

### REST API Examples

```bash
# Generate patients via API
curl -X POST http://localhost:5000/api/v1/generate/patients \
  -H "Content-Type: application/json" \
  -d '{"num_patients": 100}'

# Apply differential privacy
curl -X POST http://localhost:5000/api/v1/privacy/apply \
  -H "Content-Type: application/json" \
  -d '{
    "data": [...],
    "epsilon": 1.0,
    "columns": ["age", "income"]
  }'

# Get health status
curl http://localhost:5000/health
```

### Python API

```python
from medisafe import MediSafeAI

# Initialize the system
app = MediSafeAI()

# Generate complete patient dataset
dataset = app.generate_complete_dataset(
    num_patients=5000,
    include_vitals=True,
    include_progression=True,
    include_treatments=True,
    privacy_epsilon=1.0
)

# Export to various formats
dataset.to_csv('data/complete_dataset.csv')
dataset.to_parquet('data/complete_dataset.parquet')
dataset.to_json('data/complete_dataset.json')
```

## Architecture

### Project Structure

```
MediSafeAI/
├── src/
│   ├── data_generator/          # Synthetic data generation modules
│   │   ├── patient_generator.py     # Patient demographics
│   │   ├── vitals_generator.py      # Vital signs
│   │   ├── disease_progression.py   # Disease simulation
│   │   ├── treatment_generator.py   # Treatment assignment
│   │   └── temporal_patterns.py     # Temporal pattern injection
│   ├── privacy/                 # Privacy protection
│   │   └── differential_privacy.py
│   ├── api/                     # REST API endpoints
│   │   ├── routes.py
│   │   └── schemas.py
│   ├── airflow/                 # Airflow DAGs
│   │   └── dags/
│   ├── models/                  # Database models
│   ├── config/                  # Configuration management
│   └── utils/                   # Utilities and helpers
├── tests/                       # Test suite
│   ├── unit/
│   ├── integration/
│   └── test_data/
├── data/                        # Data storage
│   ├── raw/
│   ├── processed/
│   └── private/
├── notebooks/                   # Jupyter notebooks
├── docker/                      # Docker configurations
├── docs/                        # Documentation
├── requirements.txt
├── setup.py
├── docker-compose.yml
└── README.md
```

### Component Overview

#### Data Generation Pipeline

1. **Patient Generator**: Creates demographic data with realistic distributions
2. **Vitals Generator**: Produces condition-aware vital signs
3. **Disease Progression**: Simulates longitudinal health metrics
4. **Treatment Generator**: Assigns appropriate medications
5. **Temporal Patterns**: Adds realistic time-based variations

#### Privacy Layer

- **Laplace Mechanism**: Adds Laplace noise for pure ε-DP
- **Gaussian Mechanism**: Implements (ε,δ)-DP with Gaussian noise
- **Randomized Response**: Protects categorical data
- **Private Aggregates**: Computes statistics with privacy guarantees

#### Orchestration

- **Airflow DAGs**: Scheduled data generation and processing workflows
- **Task Dependencies**: Manage complex pipeline dependencies
- **Monitoring**: Track pipeline health and data quality

## API Reference

### Generate Patients

```
POST /api/v1/generate/patients
```

**Request Body:**
```json
{
  "num_patients": 1000,
  "seed": 42
}
```

**Response:**
```json
{
  "status": "success",
  "records_generated": 1000,
  "file_path": "data/raw/patients_20250101_120000.csv"
}
```

### Apply Differential Privacy

```
POST /api/v1/privacy/apply
```

**Request Body:**
```json
{
  "input_file": "data/raw/patients.csv",
  "epsilon": 1.0,
  "delta": 1e-5,
  "columns": ["age", "income"]
}
```

### Health Check

```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600
}
```

For complete API documentation, visit `/api/docs` when running the server.

## Configuration

### Environment Variables

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Key configuration options:

```bash
# Application
APP_ENV=development
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/medisafe
AIRFLOW_DATABASE_URL=postgresql://user:password@localhost:5432/airflow

# Privacy Settings
DEFAULT_EPSILON=1.0
DEFAULT_DELTA=1e-5

# API
API_HOST=0.0.0.0
API_PORT=5000
API_WORKERS=4

# Airflow
AIRFLOW_HOME=/opt/airflow
AIRFLOW_WEBSERVER_PORT=8080
```

### Differential Privacy Guidelines

| Use Case | Recommended ε | Privacy Level |
|----------|---------------|---------------|
| High Privacy | ε < 1.0 | Strong privacy, more noise |
| Balanced | ε = 1.0 - 5.0 | Moderate privacy-utility tradeoff |
| Low Privacy | ε > 5.0 | Weaker privacy, better utility |

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_patient_generator.py

# Run integration tests
pytest tests/integration/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/
pylint src/

# Type checking
mypy src/
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Use Cases

### 1. ML Model Training

Generate privacy-preserving training data for healthcare ML models:

```python
# Generate large training dataset
train_data = app.generate_complete_dataset(num_patients=50000)

# Apply privacy before sharing
private_train_data = dp.privatize_dataframe(train_data, epsilon=1.0)

# Train model
model.fit(private_train_data)
```

### 2. Healthcare Analytics Research

Simulate disease progression studies:

```python
# Study diabetes progression over 5 years
diabetic_patients = patients_df[patients_df['diabetes'] == 1]
progression_data = model.simulate_progression(
    diabetic_patients,
    num_visits=60,
    time_interval_days=30
)

# Analyze trends
analyze_hba1c_trends(progression_data)
```

### 3. HIPAA-Compliant Data Sharing

Share data with external partners while maintaining privacy:

```python
# Prepare data for external sharing
external_data = dp.privatize_dataframe(
    patients_df,
    epsilon=0.5,  # Stronger privacy
    delta=1e-6
)

# Verify privacy guarantees
privacy_loss = dp.compute_privacy_loss(original_data, external_data)
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/MediSafeAI.git

# Create a feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git commit -m "Add your feature"

# Push and create pull request
git push origin feature/your-feature-name
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use MediSafeAI in your research, please cite:

```bibtex
@software{medisafeai2025,
  author = {BabaMalik},
  title = {MediSafeAI: Privacy-First Healthcare Analytics},
  year = {2025},
  url = {https://github.com/BabaMalik/MediSafeAI}
}
```

## Acknowledgments

- Differential Privacy implementation based on [Google's DP library](https://github.com/google/differential-privacy)
- Synthetic data generation inspired by [Synthea](https://github.com/synthetichealth/synthea)

## Contact

- **Author**: BabaMalik
- **Email**: babamalik206@gmail.com
- **Issues**: [GitHub Issues](https://github.com/BabaMalik/MediSafeAI/issues)

---

**Disclaimer**: This software generates synthetic data for research and development purposes only. It is not intended for clinical use or to replace real patient data in production healthcare systems.
