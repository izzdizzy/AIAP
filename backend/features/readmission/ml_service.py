"""
ML Service for Hospital Readmission Predictor API
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np
import pandas as pd
import xgboost as xgb
import joblib

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    shap = None

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"

DEFAULT_MODEL_PATH = ARTIFACTS_DIR / "readmission_model.joblib"
DEFAULT_FEATURE_COLUMNS_PATH = ARTIFACTS_DIR / "feature_columns.json"
DEFAULT_METADATA_PATH = ARTIFACTS_DIR / "model_metadata.json"
DEFAULT_FEATURE_DEFAULTS_PATH = ARTIFACTS_DIR / "feature_defaults.json"
DEFAULT_THRESHOLD_PATH = ARTIFACTS_DIR / "threshold.json"

FALLBACK_MODEL_PATH = PROJECT_ROOT / "outputs" / "readmission_model.joblib"
FALLBACK_FEATURE_COLUMNS_PATH = PROJECT_ROOT / "outputs" / "feature_columns.json"
FALLBACK_METADATA_PATH = PROJECT_ROOT / "outputs" / "model_metadata.json"
FALLBACK_FEATURE_DEFAULTS_PATH = PROJECT_ROOT / "outputs" / "feature_defaults.json"


class MLService:
    def __init__(self):
        
        self.OPTIONAL_SCORE_FEATURES = {'diabetes_risk_score', 'cad_risk_score'}
        self.model = None
        self.feature_columns = None
        self.feature_defaults = None
        self.shap_explainer = None
        self.optimal_threshold = 0.5
        self.metadata = {}

        self._load_model()
        self._load_feature_columns()
        self._load_feature_defaults()
        self._load_optimal_threshold()
        self._load_metadata()

        if SHAP_AVAILABLE and self.model is not None:
            self._initialize_shap_explainer()

    def _load_model(self) -> None:
        model_path = DEFAULT_MODEL_PATH if DEFAULT_MODEL_PATH.exists() else FALLBACK_MODEL_PATH

        if not model_path.exists():
            raise FileNotFoundError(
                f"Model file not found at {model_path}. "
                "Please ensure the artifacts or outputs folder contains the trained model."
            )

        try:
            self.model = joblib.load(model_path)
            print(f"[MLService] Model loaded successfully from {model_path}")
        except Exception as e:
            raise Exception(f"Failed to load model: {str(e)}")

    def _load_feature_columns(self) -> None:
        feature_path = DEFAULT_FEATURE_COLUMNS_PATH if DEFAULT_FEATURE_COLUMNS_PATH.exists() else FALLBACK_FEATURE_COLUMNS_PATH

        if not feature_path.exists():
            raise FileNotFoundError(
                f"Feature columns file not found at {feature_path}."
            )

        try:
            with open(feature_path, 'r', encoding='utf-8') as f:
                self.feature_columns = json.load(f)
            print(f"[MLService] Feature columns loaded: {len(self.feature_columns)} features")
        except Exception as e:
            raise Exception(f"Failed to load feature columns: {str(e)}")

    def _load_feature_defaults(self) -> None:
        defaults_path = DEFAULT_FEATURE_DEFAULTS_PATH if DEFAULT_FEATURE_DEFAULTS_PATH.exists() else FALLBACK_FEATURE_DEFAULTS_PATH

        if not defaults_path.exists():
            print(f"[MLService] Warning: Feature defaults file not found at {defaults_path}")
            self.feature_defaults = {}
            return

        try:
            with open(defaults_path, 'r', encoding='utf-8') as f:
                self.feature_defaults = json.load(f)
            print(f"[MLService] Feature defaults loaded: {len(self.feature_defaults)} baseline values")
        except Exception as e:
            print(f"[MLService] Warning: Failed to load feature defaults: {str(e)}")
            self.feature_defaults = {}

    def _load_optimal_threshold(self) -> None:
        if DEFAULT_THRESHOLD_PATH.exists():
            try:
                with open(DEFAULT_THRESHOLD_PATH, 'r', encoding='utf-8') as f:
                    threshold_data = json.load(f)

                if 'optimal_threshold_for_80_recall' in threshold_data:
                    self.optimal_threshold = threshold_data['optimal_threshold_for_80_recall']
                    print(f"[MLService] Optimal threshold loaded from threshold.json: {self.optimal_threshold}")
                    return
            except Exception as e:
                print(f"[MLService] Warning: Failed to load threshold from threshold.json: {str(e)}")

        metadata_path = DEFAULT_METADATA_PATH if DEFAULT_METADATA_PATH.exists() else FALLBACK_METADATA_PATH
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                if 'optimal_threshold_for_80_recall' in metadata:
                    self.optimal_threshold = metadata['optimal_threshold_for_80_recall']
                    print(f"[MLService] Optimal threshold loaded from metadata: {self.optimal_threshold}")
                elif 'results' in metadata and 'optimal_threshold_for_85_recall' in metadata['results']:
                    self.optimal_threshold = metadata['results']['optimal_threshold_for_85_recall']
                    print(f"[MLService] Optimal threshold loaded from metadata: {self.optimal_threshold}")
                else:
                    print(f"[MLService] Using default threshold: {self.optimal_threshold}")
            except Exception as e:
                print(f"[MLService] Warning: Failed to load optimal threshold from metadata: {str(e)}")
        else:
            print(f"[MLService] Metadata file not found. Using default threshold: {self.optimal_threshold}")

    def _load_metadata(self) -> None:
        if DEFAULT_METADATA_PATH.exists():
            try:
                with open(DEFAULT_METADATA_PATH, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                print(f"[MLService] Model metadata loaded")
            except Exception as e:
                print(f"[MLService] Warning: Failed to load metadata: {str(e)}")

    def _initialize_shap_explainer(self) -> None:
        try:
            self.shap_explainer = shap.TreeExplainer(self.model)
            print("[MLService] SHAP explainer initialized successfully")
        except Exception as e:
            print(f"[MLService] Warning: Failed to initialize SHAP explainer: {str(e)}")
            self.shap_explainer = None

    def _align_features(self, input_data: pd.DataFrame) -> pd.DataFrame:
        aligned_data = input_data.copy()
        missing_features = set(self.feature_columns) - set(aligned_data.columns)

        for feature in missing_features:
            if feature in self.OPTIONAL_SCORE_FEATURES:
                aligned_data[feature] = np.nan  # Neutral: model ignores missing scores
            elif self.feature_defaults and feature in self.feature_defaults:
                aligned_data[feature] = self.feature_defaults[feature]
            else:
                aligned_data[feature] = 0

        extra_features = set(aligned_data.columns) - set(self.feature_columns)
        for feature in extra_features:
            aligned_data.drop(columns=[feature], inplace=True)

        aligned_data = aligned_data[self.feature_columns]
        return aligned_data
    def _handle_missing_values(self, X: pd.DataFrame) -> pd.DataFrame:
        X_clean = X.copy()
        for col in X_clean.select_dtypes(include=[np.number]).columns:
            if col in self.OPTIONAL_SCORE_FEATURES:
                continue  # XGBoost handles NaN natively for optional scores
            if X_clean[col].isna().any():
                median_val = X_clean[col].median()
                X_clean[col] = X_clean[col].fillna(median_val)

        non_optional = [c for c in X_clean.columns if c not in self.OPTIONAL_SCORE_FEATURES]
        X_clean[non_optional] = X_clean[non_optional].fillna(0)
        return X_clean

    def predict(self, patient_data: Dict[str, Any], return_shap: bool = True) -> Dict[str, Any]:
        from .utils import calculate_clinical_adjustment

        if isinstance(patient_data, dict):
            input_df = pd.DataFrame([patient_data])
        elif isinstance(patient_data, pd.DataFrame):
            input_df = patient_data
        else:
            raise ValueError("Input must be a dictionary or pandas DataFrame")

        aligned_df = self._align_features(input_df)
        clean_df = self._handle_missing_values(aligned_df)

        prediction = self.model.predict(clean_df)[0]
        raw_probability = self.model.predict_proba(clean_df)[0][1]

        base_severity_score = int(raw_probability * 100)
        clinical_adjustment = calculate_clinical_adjustment(clean_df.iloc[0].to_dict())
        clinical_severity_score = min(base_severity_score + clinical_adjustment, 100)

        if clinical_severity_score < 33:
            urgency_level = "Routine Monitoring"
            risk_category = "Low"
        elif clinical_severity_score < 66:
            urgency_level = "Increased Surveillance"
            risk_category = "Moderate"
        else:
            urgency_level = "Immediate Intervention"
            risk_category = "High"

        binary_prediction = 1 if raw_probability >= self.optimal_threshold else 0

        result = {
            'raw_probability': float(raw_probability),
            'clinical_severity_score': clinical_severity_score,
            'urgency_level': urgency_level,
            'risk_category': risk_category,
            'prediction': int(binary_prediction),
            'prediction_label': 'Readmitted' if binary_prediction == 1 else 'Not Readmitted',
            'clinical_adjustment_applied': clinical_adjustment,
            'threshold_used': float(self.optimal_threshold),
        }

        if return_shap and SHAP_AVAILABLE and self.shap_explainer is not None:
            try:
                shap_result = self._compute_shap_values(clean_df)
                result.update(shap_result)
            except Exception as e:
                result['shap_error'] = str(e)

        return result

    def _compute_shap_values(self, X: pd.DataFrame) -> Dict[str, Any]:
        if self.shap_explainer is None:
            return {'shap_values': None, 'top_positive_features': [], 'top_negative_features': []}

        shap_values = self.shap_explainer.shap_values(X)

        if isinstance(shap_values, list):
            shap_values = shap_values[1][:, :] if len(shap_values) > 1 else shap_values[0]

        if len(shap_values.shape) == 2:
            if shap_values.shape[0] == 1:
                mean_abs_shap = np.abs(shap_values[0])
            else:
                mean_abs_shap = np.abs(shap_values).mean(axis=0)
        else:
            mean_abs_shap = np.abs(shap_values).flatten()

        feature_importance = []
        for i, feature in enumerate(self.feature_columns):
            if i < len(mean_abs_shap):
                shap_val = float(shap_values[0][i]) if len(shap_values.shape) == 2 else float(mean_abs_shap[i])
                feature_importance.append({
                    'feature': feature,
                    'importance': float(mean_abs_shap[i]),
                    'shap_value': shap_val
                })

        feature_importance.sort(key=lambda x: x['importance'], reverse=True)

        top_positive_features = [
            {'feature': f['feature'], 'shap_value': f['shap_value']}
            for f in feature_importance if f['shap_value'] > 0
        ][:5]

        top_negative_features = [
            {'feature': f['feature'], 'shap_value': f['shap_value']}
            for f in feature_importance if f['shap_value'] < 0
        ][:5]

        shap_values_list = [
            {'feature': f['feature'], 'importance': f['importance'], 'shap_value': f['shap_value']}
            for f in feature_importance[:10]
        ]

        return {
            'shap_values': shap_values_list,
            'top_positive_features': top_positive_features,
            'top_negative_features': top_negative_features
        }

    def get_model_info(self) -> Dict[str, Any]:
        model_info = {
            'model_type': type(self.model).__name__,
            'feature_count': len(self.feature_columns),
            'shap_available': SHAP_AVAILABLE
        }

        if self.metadata:
            results = self.metadata.get('results', {})
            test_metrics = results.get('test_metrics', {})

            model_info['roc_auc'] = test_metrics.get('roc_auc')
            model_info['recall'] = test_metrics.get('recall')
            model_info['optimal_threshold'] = self.optimal_threshold
            model_info['training_samples'] = self.metadata.get('training_samples')
            model_info['test_samples'] = self.metadata.get('test_samples')

            model_info['theoretical_ceiling'] = {
                'dataset': 'UCI Diabetes Readmission Dataset',
                'baseline_readmission_rate': '~11% (negative class ~89%)',
                'citation': 'Strack B, DeShazo JP, Grinton C, et al. "Diabetes Readmission Prediction using UCI Repository Data." IEEE Journal of Biomedical and Health Informatics, 2014.',
                'note': 'Model optimized for 80%+ recall to minimize false negatives in clinical setting'
            }

        return model_info


_ml_service_instance: Optional[MLService] = None


def get_ml_service() -> MLService:
    global _ml_service_instance
    if _ml_service_instance is None:
        _ml_service_instance = MLService()
    return _ml_service_instance
