# MediSafeAI

> **Privacy-First Synthetic Healthcare Data Generation & Predictive Analytics Platform**

MediSafeAI is an end-to-end platform for generating mathematically private, demographically realistic, and longitudinally consistent synthetic patient data. It bridges the gap between healthcare data privacy (HIPAA) and the need for high-quality data in AI/ML research.

---

## 🎯 Project Goal

The primary goal of MediSafeAI is to provide a **safe, HIPAA-compliant environment** for healthcare researchers and data scientists. By using advanced synthetic data generation techniques and **Differential Privacy**, it allows organizations to develop and test healthcare applications and ML models without ever handling sensitive Real-World Data (RWD).

## 🚀 What to Expect (Expected Outcomes)

When you run MediSafeAI, you get a full-stack synthetic data factory:
1.  **Realistic Patient Cohorts**: Generate thousands of patients with realistic age, gender, income, and disease distributions.
2.  **Longitudinal Health Records**: Simulate multi-visit disease progression modeling vitals (BP, glucose, heart rate) and lab results over time.
3.  **Provable Privacy**: Protect datasets using Laplace and Gaussian differential privacy mechanisms, ensuring re-identification is mathematically impossible.
4.  **Integrated ML Module**: Train and evaluate predictive models (e.g., disease risk classification) directly on the generated data.
5.  **Automated Orchestration**: Scheduled Airflow DAGs that handle the entire pipeline from generation to ML model updates.
6.  **Operational Monitoring**: Built-in Prometheus metrics and Grafana dashboards for tracking API performance and privacy budget usage.

## 💡 What You Gain

-   **Zero Compliance Risk**: Work with data that is not subject to HIPAA restrictions, eliminating data breach liabilities.
-   **Accelerated R&D**: Skip the months of legal and administrative overhead required to access real clinical data.
-   **Model Robustness**: Inject trends, anomalies, and seasonal patterns into your data to train more resilient models.
-   **Unified Workflow**: A single platform that handles data generation, privacy protection, persistence, and machine learning.

---

## 🏗️ Architecture

```
MediSafeAI/
├── src/
│   ├── api/             # Flask REST API with JWT Auth & ML endpoints
│   ├── cli/             # Master orchestration CLI
│   ├── data_generator/  # Demographic, Vitals, Progression, and Pattern engines
│   ├── privacy/         # Differential Privacy implementation
│   ├── ml/              # Machine Learning predictors and model management
│   ├── models/          # SQLAlchemy Database models (Patient, User, Audit)
│   ├── airflow/dags/    # Automated data pipelines
│   └── utils/           # Persistence, Logging, and Schemas
├── frontend/            # React-based management dashboard
├── docker/              # Infrastructure config (Prometheus, Grafana, Postgres)
└── tests/               # Unit and Integration test suite
```

---

## 🛠️ How to Use & Run

### 1. Prerequisites
- Python 3.8+
- Docker & Docker Compose
- PostgreSQL (if running locally)

### 2. Installation
```bash
git clone https://github.com/BabaMalik/MediSafeAI.git
cd MediSafeAI
pip install -e .
```

### 3. Running the Full Stack (Recommended)
This starts the API, Frontend, Database, Airflow, and Monitoring tools:
```bash
docker-compose up -d
```
- **API**: http://localhost:5000
- **Frontend**: http://localhost:3000
- **Airflow**: http://localhost:8080 (admin/admin)
- **Grafana**: http://localhost:3000 (admin/admin)

### 4. CLI - Master Orchestration
Generate a complete longitudinal dataset and save to DB/CSV:
```bash
medisafe generate all --count 1000 --visits
```

### 5. Machine Learning Workflow
Train a model on your synthetic data:
```bash
medisafe ml train --input data/raw/patients.csv --model-type disease_predictor --target diabetes --features age --features income
```

### 6. API Interaction (JWT Protected)
1. **Login** to get your token:
   ```bash
   curl -X POST http://localhost:5000/api/v1/auth/login -d '{"email":"admin@medisafe.ai", "password":"password"}'
   ```
2. **Predict** using a trained model:
   ```bash
   curl -X POST http://localhost:5000/api/v1/ml/predict \
     -H "Authorization: Bearer <token>" \
     -d '{"model_type": "disease_predictor", "features": {"age": 65, "income": 85000}}'
   ```

---

**Disclaimer**: This software generates synthetic data for research and development purposes only. It is not intended for clinical use or as a substitute for real patient data in production healthcare systems.
