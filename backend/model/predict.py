from pathlib import Path

import numpy as np
import shap
import xgboost as xgb

from .preprocess import preprocess

# 1.0 Set probability callibration
predicted = [0.0724278733303601, 0.14618450097548655, 0.2532640571923966, 0.33953218907117844, 0.4496487511528863, 0.5490519532135555, 0.6495058690679485, 0.7526845932006836, 0.8585651904344559, 0.9325561032885998]
actual    = [0.022727272727272728, 0.14102564102564102, 0.23404255319148937, 0.3269230769230769, 0.3111111111111111, 0.5476190476190477, 0.7413793103448276, 0.7640449438202247, 0.9333333333333333, 0.9203539823008849]


# Resolve project root relative to this file's location
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODELS_DIR / "exported_model2.ubj"


def load_model() -> xgb.XGBClassifier:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found at target location: {MODEL_PATH}")

    model = xgb.XGBClassifier()
    model.load_model(MODEL_PATH)
    return model

# 1.1 Load model
model = load_model()

# 1.2 SHAP explainer
explainer = shap.TreeExplainer(model)

def predict_from_preprocessed(X):
    prediction = int(model.predict(X)[0])
    raw_probability = float(model.predict_proba(X)[0][1])
    probability = float(np.interp(raw_probability, predicted, actual))

    shap_values = explainer.shap_values(X)[0]
    raw_shap = dict(zip(X.columns, shap_values))

    return {
        'prediction': prediction,
        'raw_probability': raw_probability,
        'risk_probability': probability,
        'risk_percent': round(probability * 100, 1),
        'shap_values': raw_shap
    }


# 2. Predict
def predict(patient):
    X = preprocess(patient)
    return predict_from_preprocessed(X)