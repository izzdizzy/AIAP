import json
import os
import joblib
import pandas as pd

# Paths to model artifacts
FEATURE_DIR = os.path.dirname(__file__)
ARTIFACT_DIR = os.path.join(FEATURE_DIR, "model")
LEGACY_MODEL_DIR = os.path.abspath(os.path.join(FEATURE_DIR, "..", "..", "model", "diabetes"))
LEGACY_ARTIFACT_DIR = os.path.abspath(os.path.join(FEATURE_DIR, "..", "..", "..", "AIAP-PR2-main", "AIAP-PR2-main", "backend", "model_artifacts"))


def _resolve_artifact_path(filename: str) -> str:
    candidates = [
        os.path.join(ARTIFACT_DIR, filename),
        os.path.join(LEGACY_MODEL_DIR, filename),
        os.path.join(LEGACY_ARTIFACT_DIR, filename),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return candidates[0]


MODEL_PATH = _resolve_artifact_path("diabetes_rf_model.pkl")
FEATURE_ORDER_PATH = _resolve_artifact_path("feature_order.json")
IMPORTANCE_PATH = _resolve_artifact_path("feature_importances.json")


class DiabetesModel:
    """Wraps the trained classifier and everything needed to use it."""

    def __init__(self):
        self.model = joblib.load(MODEL_PATH)

        with open(FEATURE_ORDER_PATH) as f:
            self.feature_order = json.load(f)

        with open(IMPORTANCE_PATH) as f:
            self.importances = json.load(f)

    def predict(self, profile_dict: dict) -> dict:
        row = pd.DataFrame([[profile_dict[f] for f in self.feature_order]],
                           columns=self.feature_order)

        proba = float(self.model.predict_proba(row)[0][1])
        label = "At risk" if proba >= 0.5 else "Not at risk"

        if proba < 0.33:
            band = "Low"
        elif proba < 0.66:
            band = "Moderate"
        else:
            band = "High"

        top_features = list(self.importances.keys())[:5]
        top_factors = [f"{f} = {profile_dict[f]}" for f in top_features]

        return {
            "risk_label": label,
            "risk_probability": round(proba, 3),
            "risk_band": band,
            "top_factors": top_factors,
        }
