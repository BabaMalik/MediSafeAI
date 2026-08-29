# MediSafeAI

> Privacy-first synthetic healthcare data generation platform with differential privacy, disease simulation, and HIPAA-compliant analytics.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## The Problem

Most healthcare data tools start from the premise that *the problem is access* — that if researchers could just get their hands on real patient records, healthcare AI would move forward.

**MediSafeAI starts from a different premise: hand me perfect, unlimited, fully-consented real patient data, and three fundamental problems remain completely unsolved.**

Those three problems are what this project exists to address.

---

### Problem 1 — Real data records one timeline per patient. Never the alternatives.

A patient's chart tells you what happened to them. It cannot tell you what *would* have happened under a different decision. Every record in every EHR in the world is a single observed timeline, and the counterfactual — the road not taken — was never recorded, because it never occurred.

This is not a data volume problem. Ten million patient records still give you exactly one timeline each. You cannot query your way to an answer that was never observed.

### Problem 2 — The cases you most need to learn from are the ones reality gives you least.

Rare adverse drug reactions. Unusual comorbidity combinations. Atypical presentations in under-represented groups. These are precisely the cases where clinical decision support fails and where models need the most training signal — and they are, by definition, scarce.

You cannot order more of them. A hospital with 100,000 patient records and 12 instances of a rare reaction cannot obtain a 13th by collecting harder. Real data delivers the class balance nature produced, not the one your model needs.

### Problem 3 — You cannot validate a model against a population you do not have.

A sepsis model trained on an urban academic hospital gets deployed at a rural clinic with different demographics, different comorbidity patterns, different baseline vitals. Does it still work? Real data cannot answer this before deployment, because the validation population does not exist in your dataset.

The same applies across time: new treatment protocols, shifting population health, seasonal effects. Your dataset is one frozen sample of one population at one moment. Stress-testing against anything else requires data you do not have and cannot collect in advance.

---

### What these three have in common

All three are **unobservability problems, not access problems.** They persist at any data volume, under any consent regime, with any budget. No amount of real data solves them, because the information required was never generated in the first place.

Simulation is the only mechanism that addresses them — because a simulator can be *re-run under different conditions*, which reality cannot.

---

## A Worked Example

**The clinical question:** Margaret is 68, type 2 diabetic, HbA1c 7.2%. Standard practice escalates therapy at the 9-month review. Her physician suspects escalating at month 3 would produce materially better outcomes.

**Why her chart cannot answer this.** Margaret's record shows one year on the standard schedule, ending at HbA1c 8.1%. The month-3 timeline was never observed — she only lived one. To answer from real data you would need a randomised trial: years of enrolment, ethics approval, substantial cost, and a control arm of real patients knowingly assigned to the schedule you suspect is worse.

**What MediSafeAI does instead** — run the same cohort down both timelines:

```python
import numpy as np
from src.data_generator.patient_generator import PatientGenerator
from src.data_generator.disease_progression import DiseaseProgressionModel

# A cohort of patients like Margaret
cohort = PatientGenerator(num_patients=500, seed=42).generate_patients()
diabetics = cohort[cohort['diabetes'] == 1]          # 65 patients

for label, rate in [("standard care", 0.03), ("tight control", 0.015)]:
    np.random.seed(7)
    model = DiseaseProgressionModel(base_deterioration_rate=rate)
    finals = [
        model.simulate_progression(p, num_visits=12, time_interval_days=30)
             ['blood_glucose'].iloc[-1]
        for _, p in diabetics.iterrows()
    ]
    print(f"{label:<15} mean final glucose = {np.mean(finals):.1f} mg/dL")
```

```
standard care   mean final glucose = 185.1 mg/dL
tight control   mean final glucose = 182.5 mg/dL
```

The identical 65 patients — same ages, same baselines, same comorbidities — are run down two timelines that could never both exist in reality. That comparison is the thing real data structurally cannot provide, and it is available here in seconds rather than trial-years.

**What this buys you.** Not a replacement for the trial. A simulated effect is only as trustworthy as the model that produced it, and this one is a hand-specified simulation, not a model fitted to clinical outcomes — so the magnitude above is illustrative of the *method*, not a clinical finding. What it buys you is the ability to ask the question at all, cheaply, and to use the answer to decide which trials are worth the years.

> **Honest limitation, stated plainly.** The contrast above varies baseline deterioration, not treatment timing. Margaret's actual question — *escalate at month 3 or month 9?* — cannot yet be expressed: intervention timing is hardcoded to the calendar in `disease_progression.py`, and the `intervention_effectiveness` constructor argument is currently overridden internally and has no effect. HbA1c is likewise driven only by the internal intervention schedule, so it does not respond to any constructor parameter. Making these levers controllable is the first item on the [Roadmap](#roadmap) — it is what turns a progression simulator into a genuine counterfactual engine.

---

### Where privacy fits

Differential privacy matters here, but it is a **property of the output, not the purpose of the project.** Because the cohorts are simulated rather than drawn from real patients, results are shareable and publishable by default. The privacy engine (Laplace, Gaussian, and randomised-response mechanisms) is what lets you apply the same guarantees when releasing statistics derived from real data alongside the simulated work.

Privacy makes the output safe to share. It is not the reason the project exists.

---

## What MediSafeAI Provides

- **Synthetic patient generation** with demographically realistic distributions (age-correlated disease probabilities, gender-adjusted risk factors, log-normal income distributions)
- **Disease progression simulation** modelling how diabetes, hypertension, and heart disease evolve over time, with configurable deterioration rates and intervention effects — the counterfactual engine
- **Treatment assignment** mapping patient conditions to medication protocols
- **Temporal pattern injection** adding trends, anomalies, and seasonal cycles — the mechanism for constructing distribution-shift test populations
- **Differential privacy** (Laplace and Gaussian mechanisms) with mathematically provable guarantees for safe release

Accessible through a **REST API**, a **CLI**, and **Airflow DAGs** for scheduled pipeline execution, with **audit logging** for compliance tracking.

> **Project status:** the data generation and differential privacy layers described above are implemented and tested. The analytics, machine learning, and interactive interface layers are not yet built — see [Roadmap](#roadmap).

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

## Roadmap

The three problems above define what still needs building. Each layer depends on the one before it.

**Built today — the simulation foundation**

- Patient, vitals, treatment, and temporal pattern generation
- Disease progression simulation with configurable deterioration and intervention effects
- Differential privacy (Laplace, Gaussian, randomised response, private statistics)
- REST API, CLI, Airflow pipelines, JWT authentication

**First — make the counterfactual levers real**

The progression model has the shape of a counterfactual engine but not yet the controls. Three specific gaps: `intervention_effectiveness` is accepted by the constructor and then overridden by an internal random draw; intervention timing is hardcoded to calendar months rather than being a parameter; and HbA1c responds only to the internal schedule, so it is invariant to every constructor argument. Until these are parameters, Problem 1 can only be demonstrated on baseline deterioration rather than on treatment decisions.

**Next — making simulations queryable**

Generated cohorts currently write to CSV and are not persisted to a queryable store, so comparing results across runs is manual. Wiring generation to PostgreSQL is the prerequisite for everything below.

**Then — the counterfactual and analytics layer**

Running paired arms at cohort scale, computing effect sizes with confidence intervals, and exposing aggregate statistics through the API. This is what turns Problem 1 from a single-patient illustration into a usable method.

**Then — machine learning**

Rare-event models trained on deliberately over-sampled synthetic cohorts (Problem 2), and validation harnesses that stress-test models against shifted populations built with the temporal pattern generator (Problem 3). Requires adding scikit-learn, XGBoost, and a deep learning framework — none are currently dependencies.

**Finally — the interactive interface**

A web interface for constructing cohorts, defining counterfactual arms, running comparisons, and inspecting model results. Deliberately last: it needs the layers beneath it to have something to display.

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contact

- **Author**: BabaMalik
- **Email**: babamalik206@gmail.com
- **Issues**: [GitHub Issues](https://github.com/BabaMalik/MediSafeAI/issues)

---

**Disclaimer**: This software generates synthetic data for research and development purposes only. It is not intended for clinical use or as a substitute for real patient data in production healthcare systems.
