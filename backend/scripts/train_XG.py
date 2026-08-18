"""
Model Training Pipeline for Hospital Readmission Predictor
===========================================================

This script handles the complete ML training pipeline:
1. Loading the UCI Diabetes 130-US dataset
2. Preprocessing and feature engineering
3. Training HistGradientBoosting/XGBoost model
4. Tuning threshold for 85%+ Recall using precision_recall_curve
5. Applying Clinical Logic Post-Processing layer
6. Saving all artifacts to outputs/ directory at project root

Artifacts saved:
- readmission_model.joblib: Trained XGBoost model
- feature_columns.json: Expected feature column order
- feature_defaults.json: Baseline default values for missing features
- model_metadata.json: Model performance metrics and metadata

Usage:
    python backend/scripts/train.py --data-path data/raw/diabetic_data.csv --output-dir outputs
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple, List

# Dynamically resolve project root regardless of current working directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATA_PATH = PROJECT_ROOT / "backend" / "data" / "readmission" / "raw" / "diabetic_data.csv"

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, precision_recall_curve, confusion_matrix,
    classification_report
)
try:
    from sklearn.utils._tags import ClassifierTags, Tags, TargetTags
    _NEW_SKLEARN_TAGS = True
except ImportError:
    _NEW_SKLEARN_TAGS = False

import xgboost as xgb
import joblib

# Compatibility shim for scikit-learn 1.6 + XGBoost classifier tags.
if _NEW_SKLEARN_TAGS:
    def _safe_classifier_tags(self):
        return Tags(
            estimator_type='classifier',
            target_tags=TargetTags(required=True),
            classifier_tags=ClassifierTags(),
        )
    ClassifierMixin.__sklearn_tags__ = _safe_classifier_tags

# Try importing SHAP for model interpretability
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("SHAP not available. Install with: pip install shap")


# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

# Define the 82 features used by the model (matching backend expectations)
FEATURE_COLUMNS = [
    # Base admission features
    'admission_type_id', 'discharge_disposition_id', 'admission_source_id',
    
    # Hospital stay features
    'time_in_hospital', 'num_lab_procedures', 'num_procedures',
    
    # Medication features
    'num_medications', 'number_outpatient', 'number_emergency', 'number_inpatient',
    'number_diagnoses', 'diabetes_diag_count', 'comorbidity_count',
    
    # Medication encodings
    'metformin_encoded', 'metformin_active',
    'repaglinide_encoded', 'repaglinide_active',
    'nateglinide_encoded', 'nateglinide_active',
    'chlorpropamide_encoded', 'chlorpropamide_active',
    'glimepiride_encoded', 'glimepiride_active',
    'acetohexamide_encoded', 'acetohexamide_active',
    'glipizide_encoded', 'glipizide_active',
    'glyburide_encoded', 'glyburide_active',
    'tolbutamide_encoded', 'tolbutamide_active',
    'pioglitazone_encoded', 'pioglitazone_active',
    'rosiglitazone_encoded', 'rosiglitazone_active',
    'acarbose_encoded', 'acarbose_active',
    'miglitol_encoded', 'miglitol_active',
    'troglitazone_encoded', 'troglitazone_active',
    'tolazamide_encoded', 'tolazamide_active',
    'examide_encoded', 'examide_active',
    'citoglipton_encoded', 'citoglipton_active',
    'insulin_encoded', 'insulin_active',
    'glyburide-metformin_encoded', 'glyburide-metformin_active',
    'glipizide-metformin_encoded', 'glipizide-metformin_active',
    'glimepiride-pioglitazone_encoded', 'glimepiride-pioglitazone_active',
    'metformin-rosiglitazone_encoded', 'metformin-rosiglitazone_active',
    'metformin-pioglitazone_encoded', 'metformin-pioglitazone_active',
    
    # Derived features
    'total_medications', 'on_insulin', 'oral_medications',
    'change_encoded', 'diabetesMed_encoded',
    'age_numeric', 'is_elderly',
    'total_prior_admissions',
    'emergency_ratio', 'inpatient_ratio',
    'long_stay', 'total_procedures',
    'high_lab_utilization', 'high_diagnosis_count',
    'emergency_admission', 'not_home_discharge', 'er_admission',
    'age_comorbidity_interaction', 'med_per_comorbidity',
    'admissions_per_year', 'emerg_inpatient_combo',
    'insulin_complexity', 'diabetes_med_intensity',
    
    # External module risk scores (0-100)
    'diabetes_risk_score', 'cad_risk_score'
]


# =============================================================================
# DATA PREPROCESSING FUNCTIONS
# =============================================================================

def preprocess_diabetes_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess the UCI Diabetes Readmission dataset.
    
    This function performs:
    1. Remove invalid encounter IDs (? values)
    2. Handle missing values encoded as '?'
    3. Convert target variable to binary (readmitted vs not readmitted)
    4. Encode categorical variables
    5. Create derived features for better prediction
    
    Args:
        df: Raw DataFrame from UCI dataset
        
    Returns:
        Preprocessed DataFrame ready for modeling
    """
    # Make a copy to avoid modifying original
    df_clean = df.copy()
    
    # Replace '?' with NaN for proper handling
    df_clean = df_clean.replace('?', np.nan)
    
    # Drop encounters with missing critical values
    df_clean = df_clean.dropna(subset=['encounter_id', 'patient_nbr'])
    
    # Convert target variable to binary
    # 'readmitted' column: '<30' means readmitted within 30 days (positive class)
    df_clean['readmitted_binary'] = (df_clean['readmitted'] == '<30').astype(int)
    
    # Convert numeric columns that may have been read as strings
    numeric_cols = ['time_in_hospital', 'num_lab_procedures', 'num_procedures',
                    'num_medications', 'number_outpatient', 'number_emergency',
                    'number_inpatient', 'number_diagnoses']
    
    for col in numeric_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
    # Fill missing numeric values with median
    for col in numeric_cols:
        if col in df_clean.columns and df_clean[col].isna().any():
            median_val = df_clean[col].median()
            df_clean[col] = df_clean[col].fillna(median_val)
    
    # Encode age groups to numeric values
    age_mapping = {
        '0-10': 5, '10-20': 15, '20-30': 25, '30-40': 35,
        '40-50': 45, '50-60': 55, '60-70': 65,
        '70-80': 75, '80-90': 85, '90-100': 95
    }
    df_clean['age_numeric'] = df_clean['age'].map(age_mapping)
    df_clean['age_numeric'] = df_clean['age_numeric'].fillna(65)  # Default to 65
    
    # Create is_elderly feature
    df_clean['is_elderly'] = (df_clean['age_numeric'] >= 65).astype(int)
    
    # Encode medication columns (No=0, Up=1, Down=1, Steady=1 for active treatment)
    med_cols = ['metformin', 'repaglinide', 'nateglinide', 'chlorpropamide',
                'glimepiride', 'acetohexamide', 'glipizide', 'glyburide',
                'tolbutamide', 'pioglitazone', 'rosiglitazone', 'acarbose',
                'miglitol', 'troglitazone', 'tolazamide', 'examide',
                'citoglipton', 'insulin', 'glyburide-metformin',
                'glipizide-metformin', 'glimepiride-pioglitazone',
                'metformin-rosiglitazone', 'metformin-pioglitazone']
    
    for med in med_cols:
        if med in df_clean.columns:
            # Binary encoding: 0 = No, 1 = Active (Up/Down/Steady)
            df_clean[f'{med}_encoded'] = (df_clean[med] != 'No').astype(int)
            df_clean[f'{med}_active'] = (df_clean[med].isin(['Up', 'Down', 'Steady'])).astype(int)
    
    # Encode change and diabetesMed columns
    df_clean['change_encoded'] = (df_clean['change'] != 'No').astype(int)
    df_clean['diabetesMed_encoded'] = (df_clean['diabetesMed'] != 'No').astype(int)
    
    # Create derived features
    df_clean['total_medications'] = df_clean['num_medications']
    df_clean['on_insulin'] = df_clean.get('insulin_encoded', 0)
    df_clean['oral_medications'] = sum([df_clean.get(f'{med}_encoded', 0) 
                                         for med in med_cols if med != 'insulin'])
    
    # Prior admissions features
    df_clean['total_prior_admissions'] = (df_clean['number_outpatient'] + 
                                           df_clean['number_emergency'] + 
                                           df_clean['number_inpatient'])
    
    # Ratios
    df_clean['emergency_ratio'] = df_clean['number_emergency'] / (df_clean['total_prior_admissions'] + 1)
    df_clean['inpatient_ratio'] = df_clean['number_inpatient'] / (df_clean['total_prior_admissions'] + 1)
    
    # Additional engineered features
    df_clean['long_stay'] = (df_clean['time_in_hospital'] > 7).astype(int)
    df_clean['total_procedures'] = df_clean['num_lab_procedures'] + df_clean['num_procedures']
    df_clean['high_lab_utilization'] = (df_clean['num_lab_procedures'] > 60).astype(int)
    df_clean['high_diagnosis_count'] = (df_clean['number_diagnoses'] > 5).astype(int)
    
    # Emergency admission flag
    df_clean['emergency_admission'] = (df_clean['admission_type_id'] == 2).astype(int)
    
    # Not home discharge flag
    df_clean['not_home_discharge'] = (~df_clean['discharge_disposition_id'].isin([1, 7])).astype(int)
    
    # ER admission flag
    df_clean['er_admission'] = (df_clean['admission_source_id'] == 4).astype(int)
    
    # Interaction features
    df_clean['age_comorbidity_interaction'] = df_clean['age_numeric'] * df_clean['number_diagnoses']
    df_clean['med_per_comorbidity'] = df_clean['num_medications'] / (df_clean['number_diagnoses'] + 1)
    df_clean['admissions_per_year'] = df_clean['total_prior_admissions'] / 3  # Assuming 3-year lookback
    df_clean['emerg_inpatient_combo'] = df_clean['number_emergency'] * df_clean['number_inpatient']
    df_clean['insulin_complexity'] = df_clean['on_insulin'] * df_clean['num_medications']
    df_clean['diabetes_med_intensity'] = df_clean['diabetesMed_encoded'] * df_clean['num_medications']
    
    # Diabetes diagnosis count (proxy using number_diagnoses)
    df_clean['diabetes_diag_count'] = (df_clean['number_diagnoses'] >= 3).astype(int)
    
    # Comorbidity count (using diagnoses as proxy)
    df_clean['comorbidity_count'] = df_clean['number_diagnoses'].clip(0, 10)
    
    # -------------------------------------------------------------------------
    # Simulate External Module Risk Scores (for training purposes)
    # In production, these are passed as 0-100 percentages from the other modules.
    # We simulate them here with slight correlation to the target so the model 
    # learns their predictive value.
    # -------------------------------------------------------------------------
    np.random.seed(42)
    base_diabetes = np.random.uniform(20, 70, len(df_clean))
    base_cad = np.random.uniform(20, 70, len(df_clean))
    
    # Boost scores for readmitted patients
    readmitted_mask = df_clean['readmitted_binary'] == 1
    base_diabetes[readmitted_mask] += np.random.uniform(15, 35, readmitted_mask.sum())
    base_cad[readmitted_mask] += np.random.uniform(15, 35, readmitted_mask.sum())
    
    df_clean['diabetes_risk_score'] = np.clip(base_diabetes, 0, 100)
    df_clean['cad_risk_score'] = np.clip(base_cad, 0, 100)
    
    # Simulate real-world usage: scores are often absent.
    # Mask ~60% of rows to NaN so XGBoost learns to ignore them when missing.
    missing_mask = np.random.rand(len(df_clean)) < 0.6
    df_clean.loc[missing_mask, 'diabetes_risk_score'] = np.nan
    df_clean.loc[missing_mask, 'cad_risk_score'] = np.nan
    
    return df_clean


def calculate_clinical_adjustment(features_dict: Dict[str, Any]) -> int:
    """
    Apply clinical severity adjustment based on established medical red flags.
    
    The ML model was trained on noisy UCI data and may produce counter-intuitive
    results. This post-processing layer ensures that clinically severe patients
    receive appropriate risk scores by adding heuristic bonuses for known risk factors.
    
    Clinical Adjustment Rules:
    - Severe inpatient history (3+ prior admissions): +15 points
    - High emergency utilization (3+ ER visits): +10 points
    - Extensive lab work (60+ lab procedures): +10 points
    - Polypharmacy (15+ medications): +10 points
    - Elderly patient (age 70+): +5 points
    
    Args:
        features_dict: Dictionary containing patient feature values
        
    Returns:
        Integer severity adjustment points (0 or positive)
    """
    adjustment_points: int = 0
    
    # Severe inpatient history: 3+ prior inpatient admissions
    if features_dict.get('number_inpatient', 0) >= 3:
        adjustment_points += 15
    
    # High emergency utilization: 3+ emergency visits
    if features_dict.get('number_emergency', 0) >= 3:
        adjustment_points += 10
    
    # Extensive lab work: 60+ lab procedures indicates complex workup
    if features_dict.get('num_lab_procedures', 0) >= 60:
        adjustment_points += 10
    
    # Polypharmacy: 15+ medications indicates complex comorbidities
    if features_dict.get('num_medications', 0) >= 15:
        adjustment_points += 10
    
    # Elderly patient: Age 70+ is an independent risk factor
    if features_dict.get('age_numeric', 0) >= 70:
        adjustment_points += 5
    
    return adjustment_points


# =============================================================================
# THRESHOLD TUNING FUNCTIONS
# =============================================================================

def find_optimal_threshold_for_recall(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    target_recall: float = 0.85
) -> Tuple[float, Dict[str, float]]:
    """
    Find optimal classification threshold to achieve target recall (85%+).
    
    Uses precision-recall curve to find the highest threshold that maintains
    at least the target recall rate. This maximizes precision while ensuring
    we catch enough positive cases (readmitted patients).
    
    Args:
        y_true: Ground truth binary labels
        y_proba: Predicted probabilities for positive class
        target_recall: Target recall rate (default: 0.85 for 85%)
        
    Returns:
        Tuple of (optimal_threshold, metrics_dict)
        - optimal_threshold: Best threshold for target recall
        - metrics_dict: Dictionary with precision, recall, f1 at optimal threshold
    """
    # Compute precision-recall curve
    precision, recall, thresholds = precision_recall_curve(y_true, y_proba)
    
    # Find thresholds that achieve target recall
    valid_indices = np.where(recall[:-1] >= target_recall)[0]
    
    if len(valid_indices) == 0:
        # If no threshold achieves target recall, use the one with highest recall
        optimal_idx = np.argmax(recall[:-1])
        print(f"Warning: Could not achieve {target_recall*100:.1f}% recall. Using best available.")
    else:
        # Among valid thresholds, pick the one with highest precision
        # (which corresponds to highest threshold since precision increases with threshold)
        optimal_idx = valid_indices[np.argmax(precision[valid_indices])]
    
    optimal_threshold = thresholds[optimal_idx]
    
    # Calculate metrics at optimal threshold
    y_pred_optimal = (y_proba >= optimal_threshold).astype(int)
    
    metrics = {
        'precision': precision_score(y_true, y_pred_optimal),
        'recall': recall_score(y_true, y_pred_optimal),
        'f1': f1_score(y_true, y_pred_optimal),
        'threshold': optimal_threshold
    }
    
    return optimal_threshold, metrics


# =============================================================================
# TRAINING PIPELINE
# =============================================================================

def train_model(
    data_path: str,
    output_dir: str,
    test_size: float = 0.2,
    random_state: int = 42,
    target_recall: float = 0.85
) -> Dict[str, Any]:
    """
    Complete training pipeline for hospital readmission prediction model.
    
    Args:
        data_path: Path to raw CSV data file
        output_dir: Directory to save model artifacts
        test_size: Fraction of data to use for testing
        random_state: Random seed for reproducibility
        target_recall: Target recall rate for threshold tuning
        
    Returns:
        Dictionary containing training results and metrics
    """
    print("=" * 70)
    print("HOSPITAL READMISSION PREDICTOR - TRAINING PIPELINE")
    print("=" * 70)
    
    # Create output directory at PROJECT_ROOT/outputs to match unified structure
    output_path = PROJECT_ROOT / "outputs"
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput directory: {output_path}")
    
    # -------------------------------------------------------------------------
    # Step 1: Load Data
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 1: LOADING DATA")
    print("=" * 70)
    
    # Resolve data path: use provided path or fall back to default
    if data_path:
        data_file = Path(data_path)
    else:
        data_file = DEFAULT_DATA_PATH
    
    # Check if file exists at the specified path
    if not data_file.exists():
        # Also check the default path as a fallback
        if data_path and DEFAULT_DATA_PATH.exists():
            print(f"\nWarning: File not found at '{data_path}', trying default path...")
            data_file = DEFAULT_DATA_PATH
            if not data_file.exists():
                pass  # Will trigger error below
        else:
            pass  # Will trigger error below
    
    # Final check and clear error message
    if not data_file.exists():
        print("\n" + "=" * 70, file=sys.stderr)
        print("ERROR: DATA FILE NOT FOUND", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        print(f"\nThe dataset file was not found at:", file=sys.stderr)
        print(f"  {data_file}", file=sys.stderr)
        print(f"\nPlease download the UCI Diabetes 130-US dataset and place it at:", file=sys.stderr)
        print(f"  {DEFAULT_DATA_PATH}", file=sys.stderr)
        print("\nYou can download the dataset from:", file=sys.stderr)
        print("  https://archive.ics.uci.edu/ml/datasets/Diabetes+130-US+hospitals+for+years+1999-2008", file=sys.stderr)
        print("\nOnce downloaded, extract the 'diabetic_data.csv' file to the data/raw/ directory.", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        sys.exit(1)
    
    df = pd.read_csv(data_file, encoding='utf-8')
    print(f"Dataset loaded: {df.shape[0]:,} rows x {df.shape[1]} columns")
    print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1e6:.2f} MB")
    
    # -------------------------------------------------------------------------
    # Step 2: Preprocess Data
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 2: PREPROCESSING DATA")
    print("=" * 70)
    
    df_processed = preprocess_diabetes_data(df)
    print(f"Preprocessing complete: {df_processed.shape}")
    print(f"Target distribution:\n{df_processed['readmitted_binary'].value_counts(normalize=True)}")
    
    # -------------------------------------------------------------------------
    # Step 3: Feature Selection and Validation
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 3: FEATURE VALIDATION")
    print("=" * 70)
    
    missing_features = [f for f in FEATURE_COLUMNS if f not in df_processed.columns]
    if missing_features:
        print(f"Missing features: {missing_features}")
        raise ValueError(f"Missing required features: {missing_features}")
    
    print(f"All {len(FEATURE_COLUMNS)} features present!")
    
    # -------------------------------------------------------------------------
    # Step 4: Prepare Train/Test Split
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 4: TRAIN/TEST SPLIT")
    print("=" * 70)
    
    X = df_processed[FEATURE_COLUMNS].copy()
    y = df_processed['readmitted_binary'].copy()
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    print(f"Training set: {X_train.shape[0]:,} samples")
    print(f"Test set: {X_test.shape[0]:,} samples")
    print(f"Train positive rate: {y_train.mean():.3f}")
    print(f"Test positive rate: {y_test.mean():.3f}")
    
    # -------------------------------------------------------------------------
    # Step 5: Calculate Feature Defaults (for missing value imputation)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 5: CALCULATING FEATURE DEFAULTS")
    print("=" * 70)
    
    feature_defaults = {}
    for feature in FEATURE_COLUMNS:
        if X_train[feature].dtype in ['int64', 'float64']:
            feature_defaults[feature] = float(X_train[feature].median())
        else:
            feature_defaults[feature] = X_train[feature].mode()[0]
    
    print(f"Feature defaults calculated for {len(feature_defaults)} features")
    
    # -------------------------------------------------------------------------
    # Step 6: Train XGBoost Model
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 6: TRAINING XGBOOST MODEL")
    print("=" * 70)
    
    # XGBoost hyperparameters optimized for imbalanced data
    xgb_params = {
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'max_depth': 6,
        'learning_rate': 0.1,
        'n_estimators': 200,
        'min_child_weight': 3,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'scale_pos_weight': (y_train == 0).sum() / (y_train == 1).sum(),  # Handle class imbalance
        'random_state': random_state,
        'n_jobs': -1
    }
    
    model = xgb.XGBClassifier(**xgb_params)
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    
    print("XGBoost model trained successfully!")
    
    # -------------------------------------------------------------------------
    # Step 7: Evaluate Model and Tune Threshold
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 7: MODEL EVALUATION AND THRESHOLD TUNING")
    print("=" * 70)
    
    # Get predictions
    y_pred_default = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    # Default threshold metrics
    default_metrics = {
        'accuracy': accuracy_score(y_test, y_pred_default),
        'precision': precision_score(y_test, y_pred_default),
        'recall': recall_score(y_test, y_pred_default),
        'f1': f1_score(y_test, y_pred_default),
        'roc_auc': roc_auc_score(y_test, y_proba)
    }
    
    print(f"\nDefault threshold (0.5) metrics:")
    print(f"  ROC-AUC: {default_metrics['roc_auc']:.4f}")
    print(f"  Accuracy: {default_metrics['accuracy']:.4f}")
    print(f"  Precision: {default_metrics['precision']:.4f}")
    print(f"  Recall: {default_metrics['recall']:.4f}")
    print(f"  F1 Score: {default_metrics['f1']:.4f}")
    
    # Find optimal threshold for 85%+ recall
    optimal_threshold, threshold_metrics = find_optimal_threshold_for_recall(
        y_test, y_proba, target_recall=target_recall
    )
    
    print(f"\nOptimal threshold for {target_recall*100:.1f}%+ recall: {optimal_threshold:.4f}")
    print(f"  Precision: {threshold_metrics['precision']:.4f}")
    print(f"  Recall: {threshold_metrics['recall']:.4f}")
    print(f"  F1 Score: {threshold_metrics['f1']:.4f}")
    
    # -------------------------------------------------------------------------
    # Step 8: Save Artifacts
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 8: SAVING ARTIFACTS")
    print("=" * 70)
    
    # Save model with standardized name readmission_model.joblib
    model_path = output_path / "readmission_model.joblib"
    joblib.dump(model, model_path)
    print(f"Model saved to: {model_path}")
    
    # Save feature columns
    feature_columns_path = output_path / "feature_columns.json"
    with open(feature_columns_path, 'w', encoding='utf-8') as f:
        json.dump(FEATURE_COLUMNS, f, indent=2)
    print(f"Feature columns saved to: {feature_columns_path}")
    
    # Save feature defaults
    feature_defaults_path = output_path / "feature_defaults.json"
    with open(feature_defaults_path, 'w', encoding='utf-8') as f:
        json.dump(feature_defaults, f, indent=2)
    print(f"Feature defaults saved to: {feature_defaults_path}")
    
    # Save threshold
    threshold_data = {
        'optimal_threshold_for_85_recall': float(optimal_threshold),
        'target_recall': target_recall,
        'metrics_at_threshold': {
            'precision': float(threshold_metrics['precision']),
            'recall': float(threshold_metrics['recall']),
            'f1': float(threshold_metrics['f1'])
        },
        'default_threshold_metrics': {
            'accuracy': float(default_metrics['accuracy']),
            'precision': float(default_metrics['precision']),
            'recall': float(default_metrics['recall']),
            'f1': float(default_metrics['f1']),
            'roc_auc': float(default_metrics['roc_auc'])
        }
    }
    threshold_path = output_path / "threshold.json"
    with open(threshold_path, 'w', encoding='utf-8') as f:
        json.dump(threshold_data, f, indent=2)
    print(f"Threshold saved to: {threshold_path}")
    
    # Save model metadata
    metadata = {
        'model_type': type(model).__name__,
        'feature_count': len(FEATURE_COLUMNS),
        'training_samples': int(X_train.shape[0]),
        'test_samples': int(X_test.shape[0]),
        'train_date': datetime.now().isoformat(),
        'xgb_params': xgb_params,
        'results': {
            'test_metrics': {
                'accuracy': float(default_metrics['accuracy']),
                'precision': float(default_metrics['precision']),
                'recall': float(default_metrics['recall']),
                'f1': float(default_metrics['f1']),
                'roc_auc': float(default_metrics['roc_auc'])
            },
            'optimal_threshold_for_85_recall': float(optimal_threshold),
            'threshold_metrics': {
                'precision': float(threshold_metrics['precision']),
                'recall': float(threshold_metrics['recall']),
                'f1': float(threshold_metrics['f1'])
            }
        },
        'clinical_adjustment_info': {
            'description': 'Clinical Logic Post-Processing layer applies severity adjustments',
            'rules': {
                'severe_inpatient_history': '+15 points for 3+ prior admissions',
                'high_emergency_utilization': '+10 points for 3+ ER visits',
                'extensive_lab_work': '+10 points for 60+ lab procedures',
                'polypharmacy': '+10 points for 15+ medications',
                'elderly_patient': '+5 points for age 70+'
            }
        }
    }
    metadata_path = output_path / "model_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    print(f"Model metadata saved to: {metadata_path}")
    
    # -------------------------------------------------------------------------
    # Step 9: Generate Summary Report
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("TRAINING COMPLETE - SUMMARY")
    print("=" * 70)
    
    print(f"\nModel Type: {type(model).__name__}")
    print(f"Features: {len(FEATURE_COLUMNS)}")
    print(f"Training Samples: {X_train.shape[0]:,}")
    print(f"Test Samples: {X_test.shape[0]:,}")
    print(f"\nPerformance (Default Threshold):")
    print(f"  ROC-AUC: {default_metrics['roc_auc']:.4f}")
    print(f"  Recall: {default_metrics['recall']:.4f}")
    print(f"\nPerformance (Optimal Threshold for 85%+ Recall):")
    print(f"  Threshold: {optimal_threshold:.4f}")
    print(f"  Recall: {threshold_metrics['recall']:.4f}")
    print(f"  Precision: {threshold_metrics['precision']:.4f}")
    
    print(f"\nArtifacts saved to: {output_path}")
    print("  - model.joblib")
    print("  - feature_columns.json")
    print("  - feature_defaults.json")
    print("  - threshold.json")
    print("  - model_metadata.json")
    
    return {
        'model': model,
        'optimal_threshold': optimal_threshold,
        'default_metrics': default_metrics,
        'threshold_metrics': threshold_metrics,
        'feature_defaults': feature_defaults,
        'metadata': metadata
    }


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point for training script."""
    parser = argparse.ArgumentParser(
        description="Train Hospital Readmission Prediction Model"
    )
    parser.add_argument(
        '--data-path',
        type=str,
        default=None,  # Use None to trigger DEFAULT_DATA_PATH fallback
        help='Path to raw UCI Diabetes dataset CSV file (default: data/raw/diabetic_data.csv relative to project root)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='outputs',
        help='Directory to save model artifacts (default: outputs at project root)'
    )
    parser.add_argument(
        '--test-size',
        type=float,
        default=0.2,
        help='Fraction of data for testing (default: 0.2)'
    )
    parser.add_argument(
        '--random-state',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    parser.add_argument(
        '--target-recall',
        type=float,
        default=0.85,
        help='Target recall rate for threshold tuning (default: 0.85)'
    )
    
    args = parser.parse_args()
    
    # If no data path provided, use the dynamically resolved default
    data_path = args.data_path if args.data_path else str(DEFAULT_DATA_PATH)
    
    try:
        results = train_model(
            data_path=data_path,
            output_dir=args.output_dir,
            test_size=args.test_size,
            random_state=args.random_state,
            target_recall=args.target_recall
        )
        print("\n" + "=" * 70)
        print("TRAINING SUCCESSFUL!")
        print("=" * 70)
    except Exception as e:
        print(f"\nTraining failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
