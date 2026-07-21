"""
Model Inference Module for Hospital Readmission Predictor
==========================================================

This module provides inference logic to load the trained XGBoost model,
align input features, and return readmission risk scores with SHAP values.

Key Features:
- Load saved .joblib model
- Align input features to training schema
- Generate readmission probability score
- Compute SHAP values for feature importance解释

Usage:
    from model import ReadmissionPredictor
    
    predictor = ReadmissionPredictor()
    result = predictor.predict(patient_data)
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

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

DEFAULT_MODEL_PATH = Path("outputs/readmission_model.joblib")
DEFAULT_FEATURE_COLUMNS_PATH = Path("outputs/feature_columns.json")
DEFAULT_METADATA_PATH = Path("outputs/model_metadata.json")


# =============================================================================
# MODEL INFERENCE CLASS
# =============================================================================

class ReadmissionPredictor:
    """
    Hospital Readmission Predictor using trained XGBoost model.
    
    This class handles:
    - Loading the trained model from disk
    - Feature alignment to match training data
    - Generating readmission risk predictions
    - Computing SHAP values for interpretability
    """
    
    def __init__(
        self,
        model_path: Path = DEFAULT_MODEL_PATH,
        feature_columns_path: Path = DEFAULT_FEATURE_COLUMNS_PATH
    ):
        """
        Initialize the predictor by loading the model and feature schema.
        
        Args:
            model_path: Path to the saved .joblib model file
            feature_columns_path: Path to the feature columns JSON file
            
        Raises:
            FileNotFoundError: If model or feature columns file not found
            Exception: If model loading fails
        """
        self.model = None
        self.feature_columns = None
        self.shap_explainer = None
        
        # Load model and feature schema
        self._load_model(model_path)
        self._load_feature_columns(feature_columns_path)
        
        # Initialize SHAP explainer if available
        if SHAP_AVAILABLE and self.model is not None:
            self._initialize_shap_explainer()
    
    def _load_model(self, model_path: Path) -> None:
        """
        Load the trained XGBoost model from disk.
        
        Args:
            model_path: Path to the model file
            
        Raises:
            FileNotFoundError: If model file does not exist
        """
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model file not found at {model_path}. "
                "Please run train_model.py first to train and save the model."
            )
        
        try:
            self.model = joblib.load(model_path)
            print(f"Model loaded successfully from {model_path}")
        except Exception as e:
            raise Exception(f"Failed to load model: {str(e)}")
    
    def _load_feature_columns(self, feature_columns_path: Path) -> None:
        """
        Load the expected feature column order from JSON file.
        
        Args:
            feature_columns_path: Path to the feature columns JSON file
            
        Raises:
            FileNotFoundError: If feature columns file does not exist
        """
        if not feature_columns_path.exists():
            raise FileNotFoundError(
                f"Feature columns file not found at {feature_columns_path}. "
                "Please run train_model.py first."
            )
        
        try:
            with open(feature_columns_path, 'r') as f:
                self.feature_columns = json.load(f)
            print(f"Feature columns loaded: {len(self.feature_columns)} features")
        except Exception as e:
            raise Exception(f"Failed to load feature columns: {str(e)}")
    
    def _initialize_shap_explainer(self) -> None:
        """
        Initialize SHAP TreeExplainer for the loaded model.
        """
        try:
            self.shap_explainer = shap.TreeExplainer(self.model)
            print("SHAP explainer initialized successfully")
        except Exception as e:
            print(f"Warning: Failed to initialize SHAP explainer: {str(e)}")
            self.shap_explainer = None
    
    def _align_features(self, input_data: pd.DataFrame) -> pd.DataFrame:
        """
        Align input features to match the training data schema.
        
        This ensures that:
        - All expected features are present
        - Features are in the correct order
        - Missing features are filled with zeros
        - Extra features are removed
        
        Args:
            input_data: DataFrame with patient features
            
        Returns:
            pd.DataFrame: Aligned DataFrame with correct feature order
        """
        # Create a copy to avoid modifying original data
        aligned_data = input_data.copy()
        
        # Check which expected features are missing
        missing_features = set(self.feature_columns) - set(aligned_data.columns)
        
        # Add missing features with zero values
        for feature in missing_features:
            aligned_data[feature] = 0
        
        # Remove extra features not in training data
        extra_features = set(aligned_data.columns) - set(self.feature_columns)
        for feature in extra_features:
            aligned_data.drop(columns=[feature], inplace=True)
        
        # Reorder columns to match training data
        aligned_data = aligned_data[self.feature_columns]
        
        return aligned_data
    
    def _handle_missing_values(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values in input data using median imputation.
        
        Args:
            X: Input DataFrame
            
        Returns:
            pd.DataFrame: DataFrame with missing values filled
        """
        X_clean = X.copy()
        
        # Fill numeric missing values with column median
        for col in X_clean.select_dtypes(include=[np.number]).columns:
            if X_clean[col].isna().any():
                median_val = X_clean[col].median()
                X_clean[col] = X_clean[col].fillna(median_val)
        
        # Fill any remaining NaN with 0
        X_clean = X_clean.fillna(0)
        
        return X_clean
    
    def predict(
        self,
        patient_data: Dict[str, Any],
        return_shap: bool = True
    ) -> Dict[str, Any]:
        """
        Generate readmission risk prediction for a single patient.
        
        Args:
            patient_data: Dictionary containing patient features
            return_shap: Whether to compute SHAP values (default: True)
            
        Returns:
            Dictionary containing:
            - risk_score: Probability of readmission (0-1)
            - risk_percentage: Probability as percentage (0-100)
            - prediction: Binary prediction (0 or 1)
            - shap_values: SHAP values for each feature (if available)
            - feature_importance: Top contributing features
        """
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
        risk_score = self.model.predict_proba(clean_df)[0][1]
        
        # Return raw probability (0.0 to 1.0) - UI will handle absolute thresholds (0-30, 31-60, 61-100)
        
        # Compile result
        result = {
            'risk_score': float(risk_score),
            'risk_percentage': float(risk_score * 100),
            'prediction': int(prediction),
            'prediction_label': 'Readmitted' if prediction == 1 else 'Not Readmitted',
        }
        
        # Compute SHAP values if requested and available
        if return_shap and SHAP_AVAILABLE and self.shap_explainer is not None:
            try:
                shap_result = self._compute_shap_values(clean_df)
                result.update(shap_result)
            except Exception as e:
                result['shap_error'] = str(e)
        
        return result
    
    def predict_batch(
        self,
        patient_data_list: List[Dict[str, Any]],
        return_shap: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Generate predictions for multiple patients.
        
        Args:
            patient_data_list: List of dictionaries containing patient features
            return_shap: Whether to compute SHAP values (default: False for batch)
            
        Returns:
            List of prediction result dictionaries
        """
        results = []
        for patient_data in patient_data_list:
            result = self.predict(patient_data, return_shap=return_shap)
            results.append(result)
        return results
    
    def _compute_shap_values(
        self,
        X: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Compute SHAP values for feature importance explanation.
        
        Args:
            X: Input DataFrame with aligned features
            
        Returns:
            Dictionary containing SHAP values and feature importance ranking
        """
        if self.shap_explainer is None:
            return {'shap_values': None, 'feature_importance': []}
        
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
                feature_importance.append({
                    'feature': feature,
                    'importance': float(mean_abs_shap[i]),
                    'shap_value': float(shap_values[0][i]) if len(shap_values.shape) == 2 else float(mean_abs_shap[i])
                })
        
        # Sort by importance
        feature_importance.sort(key=lambda x: x['importance'], reverse=True)
        
        return {
            'shap_values': shap_values.tolist() if hasattr(shap_values, 'tolist') else shap_values,
            'feature_importance': feature_importance[:10],  # Top 10 features
            'top_positive_features': [f for f in feature_importance if f['shap_value'] > 0][:5],
            'top_negative_features': [f for f in feature_importance if f['shap_value'] < 0][:5]
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary containing model metadata
        """
        model_info = {
            'model_type': type(self.model).__name__,
            'feature_count': len(self.feature_columns),
            'features': self.feature_columns,
            'shap_available': SHAP_AVAILABLE
        }
        
        # Try to load additional metadata if available
        if DEFAULT_METADATA_PATH.exists():
            try:
                with open(DEFAULT_METADATA_PATH, 'r') as f:
                    metadata = json.load(f)
                    model_info['metadata'] = metadata
            except Exception:
                pass
        
        return model_info


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def load_predictor(
    model_path: Path = DEFAULT_MODEL_PATH,
    feature_columns_path: Path = DEFAULT_FEATURE_COLUMNS_PATH
) -> ReadmissionPredictor:
    """
    Convenience function to create a ReadmissionPredictor instance.
    
    Args:
        model_path: Path to the model file
        feature_columns_path: Path to feature columns file
        
    Returns:
        ReadmissionPredictor instance
    """
    return ReadmissionPredictor(model_path, feature_columns_path)


def predict_readmission_risk(
    patient_data: Dict[str, Any],
    model_path: Path = DEFAULT_MODEL_PATH,
    feature_columns_path: Path = DEFAULT_FEATURE_COLUMNS_PATH,
    return_shap: bool = True
) -> Dict[str, Any]:
    """
    Convenience function for one-off predictions.
    
    Args:
        patient_data: Dictionary containing patient features
        model_path: Path to the model file
        feature_columns_path: Path to feature columns file
        return_shap: Whether to include SHAP values
        
    Returns:
        Dictionary containing prediction results
    """
    predictor = load_predictor(model_path, feature_columns_path)
    return predictor.predict(patient_data, return_shap=return_shap)


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Example usage demonstrating the inference workflow
    
    # Sample patient data (matching the feature schema from final_dataset.csv)
    sample_patient = {
        'prior_admissions': 2,
        'comorbidity_count': 5,
        'age': 65,
        'medication_count': 10,
        'discharge_diagnosis': 250.01,
        'age_comorbidity_interaction': 325,
        'medication_comorbidity_interaction': 50,
        'admissions_comorbidity_interaction': 10,
        'age_medication_interaction': 650,
        'high_risk_flag': 0
    }
    
    print("=" * 60)
    print("HOSPITAL READMISSION PREDICTOR - INFERENCE DEMO")
    print("=" * 60)
    
    try:
        # Create predictor
        predictor = ReadmissionPredictor()
        
        # Get model info
        print("\nModel Information:")
        model_info = predictor.get_model_info()
        print(f"  Model Type: {model_info['model_type']}")
        print(f"  Feature Count: {model_info['feature_count']}")
        
        # Make prediction
        print("\n" + "-" * 40)
        print("Making Prediction...")
        print("-" * 40)
        
        result = predictor.predict(sample_patient, return_shap=True)
        
        print(f"\nRisk Score: {result['risk_score']:.4f} ({result['risk_percentage']:.2f}%)")
        print(f"Prediction: {result['prediction_label']}")
        
        # Display SHAP-based feature importance
        if 'feature_importance' in result and result['feature_importance']:
            print("\nTop Contributing Features:")
            for i, feat in enumerate(result['feature_importance'][:5], 1):
                print(f"  {i}. {feat['feature']}: {feat['importance']:.4f}")
        
        print("\n" + "=" * 60)
        print("INFERENCE COMPLETE")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("Please ensure the model has been trained by running train_model.py")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
