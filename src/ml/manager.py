"""
Model Manager
Handles saving and loading of ML models
"""

import joblib
import os
from pathlib import Path
from typing import Any, Optional
import logging
from src.config.settings import settings

logger = logging.getLogger(__name__)

class ModelManager:
    """Manages ML model artifacts persistence"""

    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = model_dir or (settings.MODEL_DIR / "ml")
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def save_model(self, model: Any, name: str):
        """Save a model to disk"""
        path = self.model_dir / f"{name}.joblib"
        joblib.dump(model, path)
        logger.info(f"Model saved to {path}")

    def load_model(self, name: str) -> Any:
        """Load a model from disk"""
        path = self.model_dir / f"{name}.joblib"
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")

        model = joblib.load(path)
        logger.info(f"Model loaded from {path}")
        return model

    def exists(self, name: str) -> bool:
        """Check if a model exists"""
        return (self.model_dir / f"{name}.joblib").exists()
