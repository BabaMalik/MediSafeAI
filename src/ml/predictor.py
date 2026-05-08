"""
Machine Learning Predictors
Implements models for disease prediction and vitals forecasting
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error
from typing import Dict, Any, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class DiseasePredictor:
    """Predicts presence of diseases based on patient vitals and demographics"""

    def __init__(self, model_params: Optional[Dict[str, Any]] = None):
        self.model = RandomForestClassifier(**(model_params or {'n_estimators': 100, 'random_state': 42}))
        self.features = []
        self.target = ""
        self.is_trained = False

    def train(self, df: pd.DataFrame, target: str, features: List[str]) -> Dict[str, float]:
        """Train the classifier on provided data"""
        self.features = features
        self.target = target

        X = df[features]
        y = df[target]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        logger.info(f"Training DiseasePredictor for {target} with {len(X_train)} samples")
        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        self.is_trained = True
        logger.info(f"Training complete. Accuracy: {accuracy:.4f}")

        return {"accuracy": accuracy, "samples": len(X_train)}

    def predict(self, features_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Predict disease presence for a single set of features"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")

        X = pd.DataFrame([features_dict])[self.features]
        prediction = self.model.predict(X)[0]
        probability = self.model.predict_proba(X)[0][1] if hasattr(self.model, "predict_proba") else None

        return {
            "prediction": int(prediction),
            "probability": float(probability) if probability is not None else None
        }

class VitalsForecaster:
    """Forecasts future vital signs based on historical data"""

    def __init__(self, model_params: Optional[Dict[str, Any]] = None):
        self.model = RandomForestRegressor(**(model_params or {'n_estimators': 100, 'random_state': 42}))
        self.features = []
        self.target = ""
        self.is_trained = False

    def train(self, df: pd.DataFrame, target: str, features: List[str]) -> Dict[str, float]:
        """Train the regressor on provided data"""
        self.features = features
        self.target = target

        X = df[features]
        y = df[target]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        logger.info(f"Training VitalsForecaster for {target} with {len(X_train)} samples")
        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)

        self.is_trained = True
        logger.info(f"Training complete. MSE: {mse:.4f}")

        return {"mse": mse, "rmse": np.sqrt(mse), "samples": len(X_train)}

    def predict(self, features_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Forecast vital sign for a single set of features"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")

        X = pd.DataFrame([features_dict])[self.features]
        prediction = self.model.predict(X)[0]

        return {
            "prediction": float(prediction)
        }
