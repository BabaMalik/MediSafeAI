# MediSafeAI Jupyter Notebooks

This directory contains interactive Jupyter notebooks demonstrating various features and use cases of MediSafeAI.

## Available Notebooks

### 01_getting_started.ipynb
Introduction to MediSafeAI covering:
- Generating synthetic patient data
- Creating vital signs
- Applying differential privacy
- Simulating disease progression
- Generating treatment assignments

## Running the Notebooks

### Local Setup

```bash
# Install Jupyter
pip install jupyter jupyterlab

# Start Jupyter Lab
jupyter lab
```

### Using Docker

```bash
# Start Jupyter service
docker-compose up jupyter

# Access at http://localhost:8888
# Token: medisafe-dev-token (default)
```

## Requirements

All notebooks require the MediSafeAI package to be installed:

```bash
pip install -e .
```

## Additional Libraries

Some notebooks may require additional visualization libraries:

```bash
pip install matplotlib seaborn plotly
```

## Data Privacy Note

All data generated in these notebooks is synthetic and does not represent real patients. The differential privacy examples demonstrate privacy-preserving techniques suitable for research and compliance purposes.
