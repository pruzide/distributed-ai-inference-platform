import os
from typing import List, Dict, Any

import joblib
import numpy as np


class InferenceEngine:
    """
    InferenceEngine is responsible only for ML prediction.

    It does not know about FastAPI.
    It does not know about Redis.
    It does not know about PostgreSQL.

    Its job:
    1. Load the trained model
    2. Validate input features
    3. Run prediction
    4. Return a clean prediction result
    """

    def __init__(self, model_path: str = "models/credit_risk_model.joblib"):
        self.model_path = model_path
        self.model_package = self._load_model()

        self.model = self.model_package["model"]
        self.feature_count = self.model_package["feature_count"]
        self.model_version = self.model_package["model_version"]
        self.feature_names = self.model_package["feature_names"]

    def _load_model(self) -> Dict[str, Any]:
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Model file not found at {self.model_path}. "
                "Run: python scripts/train_dummy_model.py"
            )

        return joblib.load(self.model_path)

    def predict(self, features: List[float]) -> Dict[str, Any]:
        if len(features) != self.feature_count:
            raise ValueError(
                f"Expected {self.feature_count} features, got {len(features)}"
            )

        input_array = np.array(features).reshape(1, -1)

        prediction = int(self.model.predict(input_array)[0])
        probabilities = self.model.predict_proba(input_array)[0]

        default_probability = float(probabilities[1])

        risk_label = "high_risk" if prediction == 1 else "low_risk"

        return {
            "risk_label": risk_label,
            "prediction": prediction,
            "default_probability": round(default_probability, 4),
            "model_version": self.model_version,
            "features_used": self.feature_names
        }