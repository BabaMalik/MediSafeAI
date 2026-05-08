# MediSafeAI

> **Privacy-first synthetic healthcare data generation and predictive analytics platform.**

MediSafeAI is a comprehensive solution designed to bridge the gap between healthcare data privacy and the need for high-quality data in AI/ML research. It enables the generation of mathematically private, demographically realistic, and longitudinally consistent patient data, complete with an integrated pipeline for training and deploying predictive models.

---

## 🎯 Project Goal

The primary goal of MediSafeAI is to provide a **safe, HIPAA-compliant environment** for healthcare researchers and data scientists. By using advanced synthetic data generation techniques and Differential Privacy, it allows organizations to develop and test healthcare applications without ever handling sensitive Real-World Data (RWD).

## 🚀 What to Expect (Expected Outcomes)

When you run MediSafeAI, you can expect:
1.  **Realistic Patient Cohorts**: Thousands of synthetic patients with demographic distributions correlated to health outcomes (age, gender, income, location).
2.  **Longitudinal Health Records**: Multi-visit disease progression simulations modeling vitals (BP, glucose, heart rate) and lab results (HbA1c, Creatinine) over time.
3.  **Provable Privacy**: Datasets protected by Laplace and Gaussian differential privacy mechanisms, ensuring no individual patient can be re-identified.
4.  **Automated ML Pipelines**: Integrated workflows that automatically generate data, persist it to a database, and train predictive models (e.g., disease risk classification).
5.  **Operational Monitoring**: Built-in Prometheus metrics and Grafana dashboards to track API usage and privacy budget consumption.

## 💡 What You Gain

-   **Zero Compliance Risk**: Work with data that is not subject to HIPAA restrictions, eliminating the risk of data breaches.
-   **Accelerated R&D**: Skip the months of legal and administrative overhead required to access real clinical data.
-   **Higher Model Robustness**: Use temporal pattern injection (trends, anomalies, seasonal cycles) to train models that are resilient to real-world data fluctuations.
-   **Privacy Budget Control**: Track exactly how much "privacy" is being used across your organization with centralized audit logging.

## 🏁 The End Result

The end result is a **production-ready analytics ecosystem**. You have a REST API serving both synthetic data and ML predictions, an Airflow-orchestrated data factory constantly refreshing your datasets, and a secure, persistent database containing the history of all operations.

---

## 🛠️ How to Use & Run

### 1. Prerequisites
- Python 3.8+
- Docker & Docker Compose
- PostgreSQL (if running locally without Docker)

### 2. Quick Installation
```bash
git clone https://github.com/BabaMalik/MediSafeAI.git
cd MediSafeAI
python -m venv venv
source venv/bin/activate
pip install -e .
```

### 3. Running with Docker (Recommended)
This starts the full stack: API, PostgreSQL, Redis, Airflow, Prometheus, and Grafana.
```bash
docker-compose up -d
```
- **API**: http://localhost:5000
- **Airflow**: http://localhost:8080 (admin/admin)
- **Grafana**: http://localhost:3000 (admin/admin)

### 4. CLI Usage
Generate data and train models directly from your terminal:

**Generate Patients:**
```bash
medisafe generate patients --count 5000 --output data/raw/patients.csv
```

**Apply Temporal Patterns:**
```bash
medisafe generate temporal --input data/raw/patients.csv --output data/raw/vitals_trend.csv --column blood_glucose --type trend --trend increase
```

**Train Machine Learning Model:**
```bash
medisafe ml train --input data/raw/patients.csv --model-type disease_predictor --target diabetes --features age --features income
```

### 5. API Interaction
**Train a model via API:**
```bash
curl -X POST http://localhost:5000/api/v1/ml/train \
  -H "Content-Type: application/json" \
  -d '{
    "model_type": "disease_predictor",
    "target_column": "diabetes",
    "feature_columns": ["age", "income"]
  }'
```

**Get a Prediction:**
```bash
curl -X POST http://localhost:5000/api/v1/ml/predict \
  -H "Content-Type: application/json" \
  -d '{
    "model_type": "disease_predictor",
    "features": {"age": 65, "income": 85000}
  }'
```

---

## 🏗️ Architecture

-   **`src/data_generator`**: Core synthetic generation engines.
-   **`src/privacy`**: Differential privacy mechanisms.
-   **`src/ml`**: Machine learning predictors and model management.
-   **`src/api`**: Flask REST interface.
-   **`src/airflow`**: Orchestration DAGs for automated pipelines.
-   **`src/models`**: Database schemas (SQLAlchemy).

---

**Disclaimer**: This software generates synthetic data for research and development purposes only. It is not intended for clinical use.
