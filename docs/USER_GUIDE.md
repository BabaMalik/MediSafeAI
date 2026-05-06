# MediSafeAI User Guide

Complete guide for using the MediSafeAI synthetic healthcare data generator.

## Table of Contents

1. [Getting Started](#getting-started)
2. [User Registration](#user-registration)
3. [Data Generation](#data-generation)
4. [Privacy Management](#privacy-management)
5. [API Usage](#api-usage)
6. [CLI Usage](#cli-usage)
7. [Best Practices](#best-practices)
8. [FAQs](#faqs)

## Getting Started

### What is MediSafeAI?

MediSafeAI is a HIPAA-compliant synthetic healthcare data generator that creates realistic but entirely fake patient data. It's designed for:

- **Testing**: Test healthcare applications without real patient data
- **Research**: Conduct medical research with privacy-preserving datasets
- **Training**: Train machine learning models on realistic synthetic data
- **Development**: Develop and demo healthcare software safely

### Key Features

✅ **Synthetic Data**: Generates realistic patient demographics, vitals, and treatment data  
✅ **Differential Privacy**: Mathematical guarantee of privacy protection  
✅ **HIPAA Compliant**: Full audit logging and compliance tracking  
✅ **Reproducible**: Use seeds for consistent data generation  
✅ **Scalable**: Generate from 1 to 100,000+ records  

## User Registration

### Web Interface

1. Navigate to `http://localhost:3000/register`
2. Fill in registration form:
   - **Username**: 3+ characters, letters/numbers/underscores only
   - **Email**: Valid email address
   - **Password**: Min 8 characters, must include:
     - Uppercase letter
     - Lowercase letter
     - Number
   - **Role**: Choose your access level
3. Click "Register"
4. Login with your credentials

### Roles Explained

| Role | Permissions |
|------|------------|
| **Viewer** | View data, read-only access |
| **Researcher** | Generate data, view privacy budget |
| **Data Scientist** | Full data generation and privacy operations |
| **Admin** | All permissions + user management |

## Data Generation

### Web Interface

1. **Login** to the system
2. Navigate to **Generate Data**
3. Configure generation parameters:
   - **Number of Patients**: 1-100,000
   - **Random Seed**: Optional, for reproducibility
   - **Include Vitals**: Blood pressure, heart rate, etc.
   - **Include Treatments**: Medication assignments
   - **Apply Privacy**: Add differential privacy

4. Click **Generate Data**

### Generated Data Structure

**Patients Data** includes:
- Patient ID (e.g., PT000001)
- Demographics (name, gender, DOB, age)
- Location (zip code)
- Socioeconomic (income, insurance)
- Conditions (diabetes, hypertension, heart disease)

**Vitals Data** includes:
- Blood Pressure (systolic/diastolic)
- Heart Rate
- Blood Glucose
- Cholesterol
- Body Temperature
- Respiratory Rate
- Oxygen Saturation
- Weight

**Treatment Data** includes:
- Medications
- Dosage
- Frequency
- Start/End dates

### Using the CLI

Generate data via command line:

```bash
# Generate 1000 patients
python -m src.cli.main generate patients --num-patients 1000 --output data/patients.csv

# Generate with seed (reproducible)
python -m src.cli.main generate patients --num-patients 500 --seed 42

# Generate complete dataset
python -m src.cli.main generate batch --num-patients 1000 --with-vitals --with-treatments

# Apply privacy
python -m src.cli.main privacy apply --input data/patients.csv --epsilon 1.0
```

### Example Output

```csv
patient_id,first_name,last_name,gender,dob,age,zip_code,income,insurance,diabetes,hypertension,heart_disease
PT000001,John,Doe,M,1985-06-15,39,12345,75000,Private,0,0,0
PT000002,Jane,Smith,F,1992-03-22,32,54321,65000,Medicare,1,0,0
...
```

## Privacy Management

### Understanding Differential Privacy

Differential Privacy (DP) adds carefully calibrated noise to data to protect individual privacy while preserving statistical properties.

**Key Parameters:**

- **Epsilon (ε)**: Privacy budget
  - Lower = More private (more noise)
  - Higher = Less private (less noise)
  - Recommended: 0.1-1.0 for high privacy, 1.0-10.0 for moderate

- **Delta (δ)**: Privacy parameter
  - Probability privacy guarantee fails
  - Should be << 1/n (dataset size)
  - Typical value: 1e-5 (0.00001)

### Applying Privacy (Web)

1. Navigate to **Privacy Management**
2. Enter file path or select generated data
3. Set privacy parameters:
   - Epsilon: 1.0 (recommended)
   - Delta: 1e-5
4. Click **Apply Privacy**
5. Download privatized dataset

### Privacy Budget Tracking

The system tracks cumulative privacy budget:

```
Total Operations: 15
Cumulative Epsilon: 12.5
Budget Used: 62.5%
```

**Best Practice**: Monitor your privacy budget and stay under your maximum threshold.

### CLI Privacy Commands

```bash
# Apply differential privacy
python -m src.cli.main privacy apply \
  --input data/patients.csv \
  --output data/private_patients.csv \
  --epsilon 1.0 \
  --delta 1e-5

# Compute private statistics
python -m src.cli.main privacy stats \
  --input data/patients.csv \
  --column age \
  --epsilon 0.5

# Check privacy budget
python -m src.cli.main privacy budget --days 30
```

## API Usage

### Authentication

First, obtain a JWT token:

```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

Response:
```json
{
  "status": "success",
  "data": {
    "user": {...},
    "tokens": {
      "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "token_type": "Bearer",
      "expires_in": 3600
    }
  }
}
```

### Generate Data

```bash
curl -X POST http://localhost:5000/api/v1/generate/patients \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "num_patients": 100,
    "seed": 42
  }'
```

### Apply Privacy

```bash
curl -X POST http://localhost:5000/api/v1/privacy/apply \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input_file": "/path/to/data.csv",
    "privacy_config": {
      "epsilon": 1.0,
      "delta": 0.00001
    },
    "numeric_columns": ["age", "income"]
  }'
```

### Full API Documentation

See [OpenAPI Specification](api/openapi.yaml) for complete API documentation.

## CLI Usage

### Available Commands

```bash
# Help
python -m src.cli.main --help

# Generate data
python -m src.cli.main generate patients --num-patients 1000
python -m src.cli.main generate vitals --input patients.csv
python -m src.cli.main generate batch --num-patients 1000

# Privacy operations
python -m src.cli.main privacy apply --input data.csv --epsilon 1.0
python -m src.cli.main privacy stats --input data.csv --column age
python -m src.cli.main privacy budget

# Database operations
python -m src.cli.main db init
python -m src.cli.main db migrate
python -m src.cli.main db seed

# User management
python -m src.cli.main user create-admin
python -m src.cli.main user list
```

## Best Practices

### Data Generation

1. **Use Seeds**: For reproducible results, always specify a seed
2. **Batch Processing**: Generate large datasets in batches (10K at a time)
3. **Validation**: Always validate generated data before use
4. **Storage**: Store generated data securely with encryption at rest

### Privacy

1. **Budget Management**: Track and limit cumulative epsilon usage
2. **Parameter Selection**: Start with ε=1.0 for balanced privacy-utility
3. **Multiple Releases**: Account for cumulative privacy loss across releases
4. **Documentation**: Document all privacy operations in audit logs

### Security

1. **Access Control**: Use appropriate role-based permissions
2. **Token Management**: Refresh tokens before expiry, never share tokens
3. **Audit**: Regularly review audit logs for suspicious activity
4. **Updates**: Keep MediSafeAI updated with latest security patches

## FAQs

### General

**Q: Is the generated data real?**  
A: No, all data is synthetic and does not represent any real individuals.

**Q: Can I use this for production systems?**  
A: Yes, but always validate data quality and ensure it meets your requirements.

**Q: How realistic is the data?**  
A: Very realistic - it follows real-world statistical distributions and correlations.

### Privacy

**Q: What epsilon value should I use?**  
A: Start with ε=1.0. Lower for more privacy, higher for better utility.

**Q: Can privacy be reversed?**  
A: No, differential privacy provides mathematical guarantees that are non-reversible.

**Q: How is privacy budget tracked?**  
A: Cumulative epsilon is logged in the database for all operations.

### Technical

**Q: What formats are supported?**  
A: CSV, JSON, Parquet, and Excel.

**Q: Can I customize the data schema?**  
A: Yes, via configuration files and API parameters.

**Q: How do I scale to millions of records?**  
A: Use batch generation, database storage, and distributed processing.

## Support

- **Documentation**: https://docs.medisafe.ai
- **GitHub**: https://github.com/medisafe/medisafe-ai
- **Email**: support@medisafe.ai
- **Issues**: https://github.com/medisafe/medisafe-ai/issues

## Examples

### Example 1: Generate Test Data

```bash
# Generate 100 test patients
python -m src.cli.main generate patients --num-patients 100 --seed 42

# Add vitals
python -m src.cli.main generate vitals --input patients.csv

# Apply privacy
python -m src.cli.main privacy apply --input patients.csv --epsilon 1.0
```

### Example 2: Research Dataset

```bash
# Generate large dataset for research
python -m src.cli.main generate batch \
  --num-patients 10000 \
  --with-vitals \
  --with-treatments \
  --with-privacy \
  --epsilon 0.5

# Compute statistics
python -m src.cli.main privacy stats \
  --input research_patients.csv \
  --column age \
  --epsilon 0.1
```

### Example 3: API Integration

```python
import requests

# Login
response = requests.post('http://localhost:5000/api/v1/auth/login', json={
    'username': 'researcher',
    'password': 'SecurePass123'
})
token = response.json()['data']['tokens']['access_token']

# Generate data
headers = {'Authorization': f'Bearer {token}'}
response = requests.post('http://localhost:5000/api/v1/generate/patients',
    headers=headers,
    json={'num_patients': 1000, 'seed': 42}
)

print(f"Generated: {response.json()['data']['records_generated']} patients")
```

---

**Need Help?** Check our [API Documentation](api/openapi.yaml) or contact support@medisafe.ai
