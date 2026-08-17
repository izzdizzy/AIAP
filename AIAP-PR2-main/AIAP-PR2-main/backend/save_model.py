"""
Train the diabetes Random Forest and save it for the backend.

This is the bridge between the notebook and the API: the notebook explores and
tunes the model; this script trains the final chosen model and writes it to disk
as a .pkl file that the FastAPI backend loads. Run it once (or whenever the model
changes):

    python save_model.py

It writes three files into model_artifacts/:
  - diabetes_rf_model.pkl   the trained model
  - feature_order.json      the column order the model expects
  - feature_importances.json which features matter most (used by the explainer)
"""

import json
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

# Point this at your dataset.
DATA_PATH = "diabetes_012_health_indicators_BRFSS2015.csv"
OUT_DIR = os.path.join(os.path.dirname(__file__), "model_artifacts")
os.makedirs(OUT_DIR, exist_ok=True)

# --- Load and build the binary target (same as the notebook) ---
df = pd.read_csv(DATA_PATH)
df["target"] = (df["Diabetes_012"] > 0).astype(int)
df = df.drop(columns=["Diabetes_012"])

FEATURES = [c for c in df.columns if c != "target"]
X, y = df[FEATURES], df["target"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=RANDOM_STATE, stratify=y)

# --- Train the final model (capped depth: better recall AND much smaller file) ---
model = RandomForestClassifier(
    n_estimators=200, max_depth=10, min_samples_leaf=5,
    class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1)
model.fit(X_train, y_train)

# --- Quick check ---
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]
print(classification_report(y_test, y_pred, target_names=["Not at risk", "At risk"]))
print("ROC-AUC:", round(roc_auc_score(y_test, y_proba), 3))

# --- Save model + metadata ---
joblib.dump(model, os.path.join(OUT_DIR, "diabetes_rf_model.pkl"))
json.dump(FEATURES, open(os.path.join(OUT_DIR, "feature_order.json"), "w"), indent=2)
importances = dict(sorted(
    zip(FEATURES, model.feature_importances_.round(4).tolist()),
    key=lambda kv: kv[1], reverse=True))
json.dump(importances, open(os.path.join(OUT_DIR, "feature_importances.json"), "w"), indent=2)

print("Saved model and metadata to", OUT_DIR)
