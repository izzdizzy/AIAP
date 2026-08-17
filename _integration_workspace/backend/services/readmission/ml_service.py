"""
Diabetes ML Service Module
===========================

This module handles ML model inference for the Diabetes Readmission Predictor.
It loads the trained XGBoost model and provides prediction functionality
with clinical severity scoring and SHAP analysis.

This is a modular service isolated from the CAD prediction service.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np
import pandas as pd

# Try to import xgboost, but handle gracefully if not available
try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    xgb = None

# Try to import shap, but handle gracefully if not available
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    shap = None

# Try to import joblib, but handle gracefully if not available
try:
    import joblib
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False
    joblib = None


# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

# Base directory is parent of this file's directory (backend/services/diabetes/ -> backend/ -> workspace/)
BASE_DIR = Path(__file__).parent.parent.parent

# Use artifacts directory for model files (created by training script)
ARTIFACTS_DIR = BASE_DIR / "artifacts" / "diabetes"

# Primary paths - check artifacts/diabetes/ directory first
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
# CLINICAL ADJUSTMENT FUNCTION
# =============================================================================

def calculate_clinical_adjustment(patient_dict: Dict[str, Any]) -> int:
    """
    Calculate clinical adjustment points based on red flags in patient data.
    
    This function adds points to the Clinical Severity Score based on
    high-risk clinical indicators.
    
    Args:
        patient_dict: Dictionary containing patient features
        
    Returns:
        Integer points to add to base severity score (0-20 range)
    """
    adjustment = 0
    
    # High number of prior admissions (3+)
    if patient_dict.get('prior_admissions', 0) >= 3 or patient_dict.get('number_inpatient', 0) >= 3:
        adjustment += 5
    
    # Long hospital stay (7+ days)
    if patient_dict.get('time_in_hospital', 0) >= 7:
        adjustment += 3
    
    # Multiple emergency visits (3+)
    if patient_dict.get('number_emergency', 0) >= 3:
        adjustment += 3
    
    # High comorbidity count (4+)
    if patient_dict.get('comorbidity_count', 0) >= 4:
        adjustment += 4
    
    # On insulin (indicates more severe diabetes)
    if patient_dict.get('on_insulin', 0) == 1 or patient_dict.get('insulin_encoded', 0) == 1:
        adjustment += 2
    
    # Multiple diagnoses (5+)
    if patient_dict.get('number_diagnoses', 0) >= 5:
        adjustment += 3
    
    # Cap adjustment at 20 points
    return min(adjustment, 20)


# =============================================================================
# DIABETES ML SERVICE CLASS
# =============================================================================

class ReadmissionMLService:
    """
    Diabetes Readmission ML Service using trained XGBoost model.
    
    This class handles:
    - Loading the trained model from disk on startup
    - Feature alignment to match training data
    - Generating readmission risk predictions
    - Computing SHAP values for interpretability
    - Calculating Clinical Severity Score (0-100) with adjustments
    """
    
    _instance = None  # Singleton instance
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance is created."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the ML service by loading the model and feature schema."""
        if self._initialized:
            return
            
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
        
        self._initialized = True
    
    def _load_model(self) -> None:
        """Load the trained XGBoost model from disk."""
        if not JOBLIB_AVAILABLE:
            print("[ReadmissionMLService] Warning: joblib not available. Model will not be loaded.")
            return
        
        # Try primary path (artifacts/diabetes/) first, then fallback to outputs/
        model_path = DEFAULT_MODEL_PATH if DEFAULT_MODEL_PATH.exists() else FALLBACK_MODEL_PATH
        
        if not model_path.exists():
            print(f"[ReadmissionMLService] Warning: Model file not found at {model_path}.")
            print("[ReadmissionMLService] Please ensure the artifacts/diabetes/ folder contains the trained model.")
            return
        
        try:
            self.model = joblib.load(model_path)
            print(f"[ReadmissionMLService] Model loaded successfully from {model_path}")
        except Exception as e:
            print(f"[ReadmissionMLService] Error: Failed to load model: {str(e)}")
    
    def _load_feature_columns(self) -> None:
        """Load the expected feature column order from JSON file."""
        # Try primary path (artifacts/diabetes/) first, then fallback to outputs/
        feature_path = DEFAULT_FEATURE_COLUMNS_PATH if DEFAULT_FEATURE_COLUMNS_PATH.exists() else FALLBACK_FEATURE_COLUMNS_PATH
        
        if not feature_path.exists():
            print(f"[ReadmissionMLService] Warning: Feature columns file not found at {feature_path}.")
            return
        
        try:
            with open(feature_path, 'r', encoding='utf-8') as f:
                self.feature_columns = json.load(f)
            print(f"[ReadmissionMLService] Feature columns loaded: {len(self.feature_columns)} features")
        except Exception as e:
            print(f"[ReadmissionMLService] Error: Failed to load feature columns: {str(e)}")
    
    def _load_feature_defaults(self) -> None:
        """Load the baseline default values for all features."""
        # Try primary path (artifacts/diabetes/) first, then fallback to outputs/
        defaults_path = DEFAULT_FEATURE_DEFAULTS_PATH if DEFAULT_FEATURE_DEFAULTS_PATH.exists() else FALLBACK_FEATURE_DEFAULTS_PATH
        
        if not defaults_path.exists():
            print(f"[ReadmissionMLService] Warning: Feature defaults file not found at {defaults_path}")
            self.feature_defaults = {}
            return
        
        try:
            with open(defaults_path, 'r', encoding='utf-8') as f:
                self.feature_defaults = json.load(f)
            print(f"[ReadmissionMLService] Feature defaults loaded: {len(self.feature_defaults)} baseline values")
        except Exception as e:
            print(f"[ReadmissionMLService] Warning: Failed to load feature defaults: {str(e)}")
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
                    print(f"[ReadmissionMLService] Optimal threshold loaded from threshold.json: {self.optimal_threshold}")
                    return
            except Exception as e:
                print(f"[ReadmissionMLService] Warning: Failed to load threshold from threshold.json: {str(e)}")
        
        # Fallback to metadata file
        metadata_path = DEFAULT_METADATA_PATH if DEFAULT_METADATA_PATH.exists() else FALLBACK_METADATA_PATH
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Try to get the optimal threshold from metadata
                if 'optimal_threshold_for_80_recall' in metadata:
                    self.optimal_threshold = metadata['optimal_threshold_for_80_recall']
                    print(f"[ReadmissionMLService] Optimal threshold loaded from metadata: {self.optimal_threshold}")
                elif 'results' in metadata and 'optimal_threshold_for_85_recall' in metadata['results']:
                    self.optimal_threshold = metadata['results']['optimal_threshold_for_85_recall']
                    print(f"[ReadmissionMLService] Optimal threshold loaded from metadata: {self.optimal_threshold}")
                else:
                    print(f"[ReadmissionMLService] Using default threshold: {self.optimal_threshold}")
            except Exception as e:
                print(f"[ReadmissionMLService] Warning: Failed to load optimal threshold from metadata: {str(e)}")
        else:
            print(f"[ReadmissionMLService] Metadata file not found. Using default threshold: {self.optimal_threshold}")
    
    def _load_metadata(self) -> None:
        """Load full model metadata for the info endpoint."""
        if DEFAULT_METADATA_PATH.exists():
            try:
                with open(DEFAULT_METADATA_PATH, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                print(f"[ReadmissionMLService] Model metadata loaded")
            except Exception as e:
                print(f"[ReadmissionMLService] Warning: Failed to load metadata: {str(e)}")
    
    def _initialize_shap_explainer(self) -> None:
        """Initialize SHAP TreeExplainer for the loaded model."""
        try:
            self.shap_explainer = shap.TreeExplainer(self.model)
            print("[ReadmissionMLService] SHAP explainer initialized successfully")
        except Exception as e:
            print(f"[ReadmissionMLService] Warning: Failed to initialize SHAP explainer: {str(e)}")
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
        # Check if model is available
        if self.model is None:
            raise FileNotFoundError(
                "Diabetes ML model not loaded. Please ensure model files exist in artifacts/diabetes/ "
                "or run the training script first."
            )
        
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
        shap_values_list = []
        for fi in feature_importance[:10]:  # Top 10 features
            shap_values_list.append({
                'feature': fi['feature'],
                'importance': fi['importance'],
                'shap_value': fi['shap_value']
            })
        
        # Separate positive and negative contributors
        top_positive = [fi for fi in feature_importance[:5] if fi['shap_value'] > 0]
        top_negative = [fi for fi in feature_importance[:5] if fi['shap_value'] < 0]
        
        return {
            'shap_values': shap_values_list,
            'top_positive_features': top_positive,
            'top_negative_features': top_negative
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model metadata, performance metrics, and theoretical ceiling citations.
        
        Returns:
            Dictionary containing model information
        """
        if not self.metadata:
            return {
                'model_type': 'XGBoost',
                'feature_count': len(self.feature_columns) if self.feature_columns else 0,
                'roc_auc': None,
                'recall': None,
                'optimal_threshold': self.optimal_threshold,
                'theoretical_ceiling': None,
                'training_samples': None,
                'test_samples': None
            }
        
        return {
            'model_type': self.metadata.get('model_type', 'XGBoost'),
            'feature_count': len(self.feature_columns) if self.feature_columns else 0,
            'roc_auc': self.metadata.get('results', {}).get('roc_auc'),
            'recall': self.metadata.get('results', {}).get('recall_at_optimal'),
            'optimal_threshold': self.optimal_threshold,
            'theoretical_ceiling': self.metadata.get('theoretical_ceiling'),
            'training_samples': self.metadata.get('training_samples'),
            'test_samples': self.metadata.get('test_samples')
        }


# =============================================================================
# SERVICE FACTORY FUNCTION
# =============================================================================

_diabetes_ml_service_instance = None

def get_readmission_ml_service() -> ReadmissionMLService:
    """
    Get or create the singleton ReadmissionMLService instance.
    
    Returns:
        ReadmissionMLService instance
    """
    global _diabetes_ml_service_instance
    if _diabetes_ml_service_instance is None:
        _diabetes_ml_service_instance = ReadmissionMLService()
    return _diabetes_ml_service_instance
