"""
Model layer: loads the trained Random Forest once and turns a health profile
into a risk prediction.

Keeping this separate from the web layer (main.py) means the prediction logic
can be tested on its own and the API file stays about HTTP, not about ML.
"""

import json
import os
import joblib
import pandas as pd

# Locate the saved artifacts relative to the workspace root for unified app
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # /workspace/backend -> /workspace
ARTIFACT_DIR = os.path.join(BASE_DIR, "backend", "models", "diabetes")
MODEL_PATH = os.path.join(ARTIFACT_DIR, "diabetes_rf_model.pkl")
FEATURE_ORDER_PATH = os.path.join(ARTIFACT_DIR, "feature_order.json")
IMPORTANCE_PATH = os.path.join(ARTIFACT_DIR, "feature_importances.json")


class DiabetesModel:
    """Wraps the trained classifier and everything needed to use it."""

    def __init__(self):
        # Load the model saved from the notebook. This is the trained Random
        # Forest; we do NOT retrain here, we just reuse it.
        self.model = joblib.load(MODEL_PATH)

        # The exact column order the model was trained on. Predictions must use
        # the same order, otherwise values line up with the wrong features.
        with open(FEATURE_ORDER_PATH) as f:
            self.feature_order = json.load(f)

        # Feature importances, used to tell the user which of THEIR inputs are
        # the biggest risk drivers.
        with open(IMPORTANCE_PATH) as f:
            self.importances = json.load(f)

    def predict(self, profile_dict: dict) -> dict:
        """Take a validated profile dict and return a prediction dict."""
        # Build a one-row DataFrame with columns in the trained order.
        row = pd.DataFrame([[profile_dict[f] for f in self.feature_order]],
                           columns=self.feature_order)

        # Probability of the 'at risk' class (column 1).
        proba = float(self.model.predict_proba(row)[0][1])
        label = "At risk" if proba >= 0.5 else "Not at risk"

        # Turn the probability into a human-friendly band.
        if proba < 0.33:
            band = "Low"
        elif proba < 0.66:
            band = "Moderate"
        else:
            band = "High"

        # Report the person's own values on the top risk-driving features, so
        # the explanation can be specific rather than generic.
        top_features = list(self.importances.keys())[:5]
        top_factors = [f"{f} = {profile_dict[f]}" for f in top_features]

        return {
            "risk_label": label,
            "risk_probability": round(proba, 3),
            "risk_band": band,
            "top_factors": top_factors,
        }
