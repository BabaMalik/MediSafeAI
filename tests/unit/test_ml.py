"""
Unit tests for ML module
"""

import pytest
import pandas as pd
import numpy as np
from src.ml.predictor import DiseasePredictor, VitalsForecaster
from src.ml.manager import ModelManager
from pathlib import Path

@pytest.fixture
def sample_ml_data():
    """Create sample data for training"""
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        'age': np.random.randint(18, 90, n),
        'income': np.random.lognormal(10, 1, n),
        'blood_pressure_systolic': np.random.normal(120, 15, n),
        'blood_glucose': np.random.normal(100, 20, n),
        'diabetes': np.random.randint(0, 2, n),
        'weight': np.random.normal(180, 30, n)
    })
    return df

class TestMLModule:
    """Test cases for Machine Learning module"""

    def test_disease_predictor_train_predict(self, sample_ml_data):
        """Test training and prediction for DiseasePredictor"""
        predictor = DiseasePredictor()
        features = ['age', 'blood_pressure_systolic', 'blood_glucose']
        target = 'diabetes'

        results = predictor.train(sample_ml_data, target, features)
        assert 'accuracy' in results
        assert results['samples'] > 0
        assert predictor.is_trained is True

        # Test prediction
        sample_features = {
            'age': 50,
            'blood_pressure_systolic': 140,
            'blood_glucose': 150
        }
        prediction = predictor.predict(sample_features)
        assert 'prediction' in prediction
        assert prediction['prediction'] in [0, 1]
        assert 'probability' in prediction

    def test_vitals_forecaster_train_predict(self, sample_ml_data):
        """Test training and prediction for VitalsForecaster"""
        forecaster = VitalsForecaster()
        features = ['age', 'weight']
        target = 'blood_pressure_systolic'

        results = forecaster.train(sample_ml_data, target, features)
        assert 'mse' in results
        assert 'rmse' in results
        assert forecaster.is_trained is True

        # Test prediction
        sample_features = {
            'age': 40,
            'weight': 170
        }
        prediction = forecaster.predict(sample_features)
        assert 'prediction' in prediction
        assert isinstance(prediction['prediction'], float)

    def test_model_manager(self):
        """Test ModelManager saving and loading"""
        import os
        from src.ml.predictor import DiseasePredictor

        # Use a temporary directory
        tmp_dir = Path("tests/tmp_models")
        manager = ModelManager(model_dir=tmp_dir)

        model = DiseasePredictor()
        # Mock training status
        model.is_trained = True
        model.features = ['f1']

        manager.save_model(model, "test_model")
        assert (tmp_dir / "test_model.joblib").exists()

        loaded_model = manager.load_model("test_model")
        assert isinstance(loaded_model, DiseasePredictor)
        assert loaded_model.features == ['f1']

        # Cleanup
        os.remove(tmp_dir / "test_model.joblib")
        tmp_dir.rmdir()
