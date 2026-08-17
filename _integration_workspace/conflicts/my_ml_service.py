"""
ML Service for Hospital Readmission Predictor API
==================================================

This module handles ML model inference, migrated from model.py.
It loads the trained XGBoost model and provides prediction functionality
with clinical severity scoring and SHAP analysis.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np
import pandas as pd
import xgboost as xgb
import joblib

# Try to import shap, but handle gracefully if not available
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    shap = None


# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

# Base directory is parent of this file's directory (backend/ -> workspace/)
BASE_DIR = Path(__file__).parent.parent

# Use artifacts directory for model files (created by training script)
ARTIFACTS_DIR = Path(__file__).parent / "artifacts"

# Primary paths - check artifacts/ directory first
DEFAULT_MODEL_PATH = ARTIFACTS_DIR / "model.joblib"
DEFAULT_FEATURE_COLUMNS_PATH = ARTIFACTS_DIR / "feature_columns.json"
DEFAULT_METADATA_PATH = ARTIFACTS_DIR / "model_metadata.json"
DEFAULT_FEATURE_DEFAULTS_PATH = ARTIFACTS_DIR / "feature_defaults.json"
DEFAULT_THRESHOLD_PATH = ARTIFACTS_DIR / "threshold.json"

# Fallback paths - legacy outputs/ directory
FALLBACK_MODEL_PATH = BASE_DIR / "outputs" / "readmission_model.joblib"
FALLBACK_FEATURE_COLUMNS_PATH = BASE_DIR / "outputs" / "feature_columns.json"
FALLBACK_METADATA_PATH = BASE_DIR / "outputs" / "model_metadata.json"
FALLBACK_FEATURE_DEFAULTS_PATH = BASE_DIR / "outputs" / "feature_defaults.json"


# =============================================================================
# ML SERVICE CLASS
# =============================================================================

class MLService:
    """
    Hospital Readmission ML Service using trained XGBoost model.
    
    This class handles:
    - Loading the trained model from disk on startup
    - Feature alignment to match training data
    - Generating readmission risk predictions
    - Computing SHAP values for interpretability
    - Calculating Clinical Severity Score (0-100) with adjustments
    """
    
    def __init__(self):
        """Initialize the ML service by loading the model and feature schema."""
        self.model = None
        self.feature_columns = None
        self.feature_defaults = None
        self.shap_explainer = None
        self.optimal_threshold = 0.5  # Default threshold
        self.metadata = {}
        
        # Load model and feature schema
        self._load_model()
        self._load_feature_columns()
        self._load_feature_defaults()
        self._load_optimal_threshold()
        self._load_metadata()
        
        # Initialize SHAP explainer if available
        if SHAP_AVAILABLE and self.model is not None:
            self._initialize_shap_explainer()
    
    def _load_model(self) -> None:
        """Load the trained XGBoost model from disk."""
        # Try primary path (artifacts/) first, then fallback to outputs/
        model_path = DEFAULT_MODEL_PATH if DEFAULT_MODEL_PATH.exists() else FALLBACK_MODEL_PATH
        
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model file not found at {model_path}. "
                "Please ensure the artifacts/ folder contains the trained model, "
                "or run: python backend/scripts/train.py"
            )
        
        try:
            self.model = joblib.load(model_path)
            print(f"[MLService] Model loaded successfully from {model_path}")
        except Exception as e:
            raise Exception(f"Failed to load model: {str(e)}")
    
    def _load_feature_columns(self) -> None:
        """Load the expected feature column order from JSON file."""
        # Try primary path (artifacts/) first, then fallback to outputs/
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
        """Load the baseline default values for all features."""
        # Try primary path (artifacts/) first, then fallback to outputs/
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
        """Load the optimal threshold from the threshold.json or model metadata file."""
        # Try primary threshold path first
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
        
        # Fallback to metadata file
        metadata_path = DEFAULT_METADATA_PATH if DEFAULT_METADATA_PATH.exists() else FALLBACK_METADATA_PATH
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Try to get the optimal threshold from metadata
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
        """Load full model metadata for the info endpoint."""
        if DEFAULT_METADATA_PATH.exists():
            try:
                with open(DEFAULT_METADATA_PATH, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                print(f"[MLService] Model metadata loaded")
            except Exception as e:
                print(f"[MLService] Warning: Failed to load metadata: {str(e)}")
    
    def _initialize_shap_explainer(self) -> None:
        """Initialize SHAP TreeExplainer for the loaded model."""
        try:
            self.shap_explainer = shap.TreeExplainer(self.model)
            print("[MLService] SHAP explainer initialized successfully")
        except Exception as e:
            print(f"[MLService] Warning: Failed to initialize SHAP explainer: {str(e)}")
            self.shap_explainer = None
    
    def _align_features(self, input_data: pd.DataFrame) -> pd.DataFrame:
        """
        Align input features to match the training data schema.
        
        Using dataset baselines instead of zeros prevents distribution shifts
        that cause false high-risk predictions for partial inputs.
        """
        # Create a copy to avoid modifying original data
        aligned_data = input_data.copy()
        
        # Check which expected features are missing
        missing_features = set(self.feature_columns) - set(aligned_data.columns)
        
        # Add missing features with baseline default values (median/mode) instead of zeros
        for feature in missing_features:
            if self.feature_defaults and feature in self.feature_defaults:
                aligned_data[feature] = self.feature_defaults[feature]
            else:
                # Fallback to 0 if no default available
                aligned_data[feature] = 0
        
        # Remove extra features not in training data
        extra_features = set(aligned_data.columns) - set(self.feature_columns)
        for feature in extra_features:
            aligned_data.drop(columns=[feature], inplace=True)
        
        # Reorder columns to match training data
        aligned_data = aligned_data[self.feature_columns]
        
        return aligned_data
    
    def _handle_missing_values(self, X: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in input data using median imputation."""
        X_clean = X.copy()
        
        # Fill numeric missing values with column median
        for col in X_clean.select_dtypes(include=[np.number]).columns:
            if X_clean[col].isna().any():
                median_val = X_clean[col].median()
                X_clean[col] = X_clean[col].fillna(median_val)
        
        # Fill any remaining NaN with 0
        X_clean = X_clean.fillna(0)
        
        return X_clean
    
    def predict(self, patient_data: Dict[str, Any], return_shap: bool = True) -> Dict[str, Any]:
        """
        Generate readmission risk prediction for a single patient.
        
        Args:
            patient_data: Dictionary containing patient features
            return_shap: Whether to compute SHAP values (default: True)
            
        Returns:
            Dictionary containing:
            - raw_probability: Probability of readmission (0.0-1.0)
            - clinical_severity_score: 0-100 score with clinical adjustments
            - urgency_level: Routine Monitoring, Increased Surveillance, or Immediate Intervention
            - risk_category: Low, Moderate, or High
            - prediction: Binary prediction (0 or 1)
            - prediction_label: Human-readable prediction
            - clinical_adjustment_applied: Points added due to clinical rules
            - shap_values: SHAP analysis (if requested)
        """
        # Import clinical adjustment function
        from utils import calculate_clinical_adjustment
        
        # Convert dict to DataFrame
        if isinstance(patient_data, dict):
            input_df = pd.DataFrame([patient_data])
        elif isinstance(patient_data, pd.DataFrame):
            input_df = patient_data
        else:
            raise ValueError("Input must be a dictionary or pandas DataFrame")
        
        # Align features
        aligned_df = self._align_features(input_df)
        
        # Handle missing values
        clean_df = self._handle_missing_values(aligned_df)
        
        # Generate prediction
        prediction = self.model.predict(clean_df)[0]
        raw_probability = self.model.predict_proba(clean_df)[0][1]
        
        # Calculate Clinical Severity Score (0-100)
        # Start with raw probability scaled to 0-100
        base_severity_score = int(raw_probability * 100)
        
        # Apply clinical adjustment based on red flags
        clinical_adjustment = calculate_clinical_adjustment(clean_df.iloc[0].to_dict())
        
        # Cap the final score at 100
        clinical_severity_score = min(base_severity_score + clinical_adjustment, 100)
        
        # Determine urgency level and risk category based on severity score
        if clinical_severity_score < 33:
            urgency_level = "Routine Monitoring"
            risk_category = "Low"
        elif clinical_severity_score < 66:
            urgency_level = "Increased Surveillance"
            risk_category = "Moderate"
        else:
            urgency_level = "Immediate Intervention"
            risk_category = "High"
        
        # Binary prediction using optimal threshold
        binary_prediction = 1 if raw_probability >= self.optimal_threshold else 0
        
        # Compile result
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
        
        # Compute SHAP values if requested and available
        if return_shap and SHAP_AVAILABLE and self.shap_explainer is not None:
            try:
                shap_result = self._compute_shap_values(clean_df)
                result.update(shap_result)
            except Exception as e:
                result['shap_error'] = str(e)
        
        return result
    
    def _compute_shap_values(self, X: pd.DataFrame) -> Dict[str, Any]:
        """Compute SHAP values for feature importance explanation."""
        if self.shap_explainer is None:
            return {'shap_values': None, 'top_positive_features': [], 'top_negative_features': []}
        
        # Compute SHAP values
        shap_values = self.shap_explainer.shap_values(X)
        
        # Handle different SHAP output formats
        if isinstance(shap_values, list):
            # For multi-output models
            shap_values = shap_values[1][:, :] if len(shap_values) > 1 else shap_values[0]
        
        # Get absolute SHAP values for importance ranking
        if len(shap_values.shape) == 2:
            # Single sample or already aggregated
            if shap_values.shape[0] == 1:
                mean_abs_shap = np.abs(shap_values[0])
            else:
                mean_abs_shap = np.abs(shap_values).mean(axis=0)
        else:
            mean_abs_shap = np.abs(shap_values).flatten()
        
        # Create feature importance ranking
        feature_importance = []
        for i, feature in enumerate(self.feature_columns):
            if i < len(mean_abs_shap):
                shap_val = float(shap_values[0][i]) if len(shap_values.shape) == 2 else float(mean_abs_shap[i])
                feature_importance.append({
                    'feature': feature,
                    'importance': float(mean_abs_shap[i]),
                    'shap_value': shap_val
                })
        
        # Sort by importance
        feature_importance.sort(key=lambda x: x['importance'], reverse=True)
        
        # Format top features for response
        top_positive_features = [
            {'feature': f['feature'], 'shap_value': f['shap_value']}
            for f in feature_importance if f['shap_value'] > 0
        ][:5]
        
        top_negative_features = [
            {'feature': f['feature'], 'shap_value': f['shap_value']}
            for f in feature_importance if f['shap_value'] < 0
        ][:5]
        
        # Format shap_values as list of objects for frontend
        shap_values_list = [
            {'feature': f['feature'], 'importance': f['importance'], 'shap_value': f['shap_value']}
            for f in feature_importance[:10]  # Top 10 only
        ]
        
        return {
            'shap_values': shap_values_list,
            'top_positive_features': top_positive_features,
            'top_negative_features': top_negative_features
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model for the info endpoint."""
        model_info = {
            'model_type': type(self.model).__name__,
            'feature_count': len(self.feature_columns),
            'shap_available': SHAP_AVAILABLE
        }
        
        # Add performance metrics from metadata
        if self.metadata:
            results = self.metadata.get('results', {})
            test_metrics = results.get('test_metrics', {})
            
            model_info['roc_auc'] = test_metrics.get('roc_auc')
            model_info['recall'] = test_metrics.get('recall')
            model_info['optimal_threshold'] = self.optimal_threshold
            model_info['training_samples'] = self.metadata.get('training_samples')
            model_info['test_samples'] = self.metadata.get('test_samples')
            
            # Add theoretical ceiling citations
            model_info['theoretical_ceiling'] = {
                'dataset': 'UCI Diabetes Readmission Dataset',
                'baseline_readmission_rate': '~11% (negative class ~89%)',
                'citation': 'Strack B, DeShazo JP, Grinton C, et al. "Diabetes Readmission Prediction using UCI Repository Data." IEEE Journal of Biomedical and Health Informatics, 2014.',
                'note': 'Model optimized for 80%+ recall to minimize false negatives in clinical setting'
            }
        
        return model_info


# Singleton instance for the FastAPI app
_ml_service_instance: Optional[MLService] = None


def get_ml_service() -> MLService:
    """Get or create the ML service singleton instance."""
    global _ml_service_instance
    if _ml_service_instance is None:
        _ml_service_instance = MLService()
    return _ml_service_instance
