"""
Train Model Script for Hospital Readmission Predictor
======================================================

This standalone script trains an XGBoost model to predict 30-day hospital 
readmissions for diabetic patients using the UCI Diabetes 130-US Hospitals 
Dataset (1999-2008).

Key Features:
- Advanced feature engineering with interaction terms
- Class imbalance handling using SMOTE
- Hyperparameter optimization via RandomizedSearchCV with StratifiedKFold
- Model evaluation targeting >= 80% ROC-AUC
- Model persistence using joblib

Usage:
    python train_model.py

Output:
    - outputs/readmission_model.joblib: Trained XGBoost model
    - outputs/model_metadata.json: Model performance metrics and metadata
    - outputs/feature_columns.json: Feature column order for inference
"""

import os
import json
from pathlib import Path
from typing import Tuple, Dict, Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, RandomizedSearchCV, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, classification_report
)
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
from imblearn.over_sampling import SMOTE
import joblib


# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

RANDOM_STATE = 42
TEST_SIZE = 0.2
CV_FOLDS = 5
N_ITER_SEARCH = 50
TARGET_ROC_AUC = 0.80

DATA_PATH = Path("data/processed/final_dataset.csv")
OUTPUT_DIR = Path("outputs")
MODEL_PATH = OUTPUT_DIR / "readmission_model.joblib"
METADATA_PATH = OUTPUT_DIR / "model_metadata.json"
FEATURE_COLUMNS_PATH = OUTPUT_DIR / "feature_columns.json"


# =============================================================================
# DATA LOADING AND PREPROCESSING FUNCTIONS
# =============================================================================

def load_data(file_path: Path) -> pd.DataFrame:
    """
    Load the processed dataset from CSV file.
    
    Args:
        file_path: Path to the processed CSV file
        
    Returns:
        pd.DataFrame: Loaded dataset
        
    Raises:
        FileNotFoundError: If file does not exist
        pd.errors.EmptyDataError: If file is empty
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found at {file_path}")
    
    df = pd.read_csv(file_path)
    print(f"Loaded dataset: {df.shape[0]} records, {df.shape[1]} features")
    return df


def prepare_features_and_target(
    df: pd.DataFrame,
    target_col: str = 'readmission_target'
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Separate features and target variable.
    
    Args:
        df: Input DataFrame
        target_col: Name of target column
        
    Returns:
        Tuple containing features DataFrame and target Series
    """
    feature_cols = [col for col in df.columns if col != target_col]
    X = df[feature_cols].copy()
    y = df[target_col].copy()
    
    print(f"Features: {len(feature_cols)} columns")
    print(f"Target distribution: {y.value_counts().to_dict()}")
    
    return X, y


def handle_missing_values(X: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values in features using median imputation.
    
    Args:
        X: Features DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with missing values filled
    """
    numeric_cols = X.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        if X[col].isna().any():
            median_val = X[col].median()
            X[col] = X[col].fillna(median_val)
    
    missing_count = X.isna().sum().sum()
    print(f"Missing values after imputation: {missing_count}")
    
    return X


# =============================================================================
# FEATURE ENGINEERING FUNCTIONS
# =============================================================================

def create_additional_features(X: pd.DataFrame) -> pd.DataFrame:
    """
    Create additional engineered features for better model performance.
    
    Args:
        X: Features DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with additional features
    """
    X_eng = X.copy()
    
    # Create polynomial features for key variables
    if 'age' in X_eng.columns:
        X_eng['age_squared'] = X_eng['age'] ** 2
    
    if 'comorbidity_count' in X_eng.columns:
        X_eng['comorbidity_squared'] = X_eng['comorbidity_count'] ** 2
    
    # Create ratio features
    if 'medication_count' in X_eng.columns and 'comorbidity_count' in X_eng.columns:
        # Avoid division by zero
        denom = X_eng['comorbidity_count'].replace(0, 1)
        X_eng['medication_per_comorbidity'] = X_eng['medication_count'] / denom
    
    if 'prior_admissions' in X_eng.columns and 'age' in X_eng.columns:
        X_eng['admissions_age_ratio'] = X_eng['prior_admissions'] / (X_eng['age'] + 1)
    
    # Create risk composite score
    risk_cols = ['prior_admissions', 'comorbidity_count', 'medication_count']
    available_risk_cols = [col for col in risk_cols if col in X_eng.columns]
    if len(available_risk_cols) >= 2:
        X_eng['risk_composite'] = X_eng[available_risk_cols].sum(axis=1)
    
    print(f"Created additional features. Total features: {X_eng.shape[1]}")
    
    return X_eng


# =============================================================================
# MODEL TRAINING FUNCTIONS
# =============================================================================

def apply_smote(
    X_train: pd.DataFrame,
    y_train: pd.Series
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Apply SMOTE to handle class imbalance in training data.
    
    Args:
        X_train: Training features
        y_train: Training target
        
    Returns:
        Tuple containing resampled training features and target
    """
    # Check class distribution
    class_dist = y_train.value_counts()
    minority_class_count = class_dist.min()
    majority_class_count = class_dist.max()
    imbalance_ratio = majority_class_count / max(minority_class_count, 1)
    
    print(f"Class imbalance ratio before SMOTE: {imbalance_ratio:.2f}:1")
    
    # Apply SMOTE only if there's significant imbalance
    if imbalance_ratio > 1.5:
        smote = SMOTE(random_state=RANDOM_STATE, k_neighbors=5)
        X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
        
        new_dist = pd.Series(y_train_resampled).value_counts()
        new_imbalance_ratio = new_dist.max() / max(new_dist.min(), 1)
        print(f"Class imbalance ratio after SMOTE: {new_imbalance_ratio:.2f}:1")
        print(f"Resampled training size: {len(y_train_resampled)}")
        
        return X_train_resampled, y_train_resampled
    else:
        print("Class imbalance is acceptable, skipping SMOTE")
        return X_train, y_train


def create_xgboost_param_grid() -> Dict[str, list]:
    """
    Create parameter grid for XGBoost hyperparameter tuning.
    
    Returns:
        Dict: Parameter distributions for RandomizedSearchCV
    """
    param_dist = {
        'max_depth': [3, 4, 5, 6, 7, 8],
        'learning_rate': [0.01, 0.05, 0.1, 0.15, 0.2],
        'n_estimators': [100, 150, 200, 250, 300],
        'min_child_weight': [1, 2, 3, 5],
        'subsample': [0.7, 0.8, 0.9, 1.0],
        'colsample_bytree': [0.7, 0.8, 0.9, 1.0],
        'gamma': [0, 0.1, 0.2, 0.3],
        'reg_alpha': [0, 0.1, 0.5, 1.0],
        'reg_lambda': [1, 1.5, 2, 3],
        'scale_pos_weight': [1, 2, 3, 5]
    }
    
    return param_dist


def train_xgboost_with_hyperparameter_tuning(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    cv_folds: int = CV_FOLDS,
    n_iter: int = N_ITER_SEARCH
) -> Tuple[xgb.XGBClassifier, Dict[str, Any]]:
    """
    Train XGBoost model with hyperparameter tuning using RandomizedSearchCV.
    
    Args:
        X_train: Training features
        y_train: Training target
        X_test: Test features
        y_test: Test target
        cv_folds: Number of cross-validation folds
        n_iter: Number of parameter settings to sample
        
    Returns:
        Tuple containing trained model and results dictionary
    """
    print("\n" + "=" * 60)
    print("XGBOOST HYPERPARAMETER TUNING")
    print("=" * 60)
    
    # Create stratified k-fold
    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=RANDOM_STATE)
    
    # Initialize base XGBoost classifier
    base_xgb = xgb.XGBClassifier(
        objective='binary:logistic',
        eval_metric='auc',
        random_state=RANDOM_STATE,
        n_jobs=-1,
        use_label_encoder=False
    )
    
    # Create parameter grid
    param_dist = create_xgboost_param_grid()
    
    # Setup RandomizedSearchCV
    random_search = RandomizedSearchCV(
        estimator=base_xgb,
        param_distributions=param_dist,
        n_iter=n_iter,
        scoring='roc_auc',
        cv=skf,
        verbose=1,
        n_jobs=-1,
        random_state=RANDOM_STATE,
        return_train_score=True
    )
    
    # Fit the model
    print("\nStarting hyperparameter search...")
    random_search.fit(X_train, y_train)
    
    # Get best model
    best_model = random_search.best_estimator_
    best_params = random_search.best_params_
    best_score = random_search.best_score_
    
    print(f"\nBest ROC-AUC from cross-validation: {best_score:.4f}")
    print(f"Best parameters: {best_params}")
    
    # Evaluate on test set
    y_pred = best_model.predict(X_test)
    y_pred_proba = best_model.predict_proba(X_test)[:, 1]
    
    test_metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1': f1_score(y_test, y_pred, zero_division=0),
        'roc_auc': roc_auc_score(y_test, y_pred_proba)
    }
    
    print("\n" + "=" * 60)
    print("TEST SET EVALUATION")
    print("=" * 60)
    print(f"Accuracy:  {test_metrics['accuracy']:.4f}")
    print(f"Precision: {test_metrics['precision']:.4f}")
    print(f"Recall:    {test_metrics['recall']:.4f}")
    print(f"F1 Score:  {test_metrics['f1']:.4f}")
    print(f"ROC-AUC:   {test_metrics['roc_auc']:.4f}")
    
    # Check if target ROC-AUC is achieved
    if test_metrics['roc_auc'] >= TARGET_ROC_AUC:
        print(f"\n✓ Target ROC-AUC ({TARGET_ROC_AUC}) ACHIEVED!")
    else:
        print(f"\n⚠ Target ROC-AUC ({TARGET_ROC_AUC}) not achieved. Current: {test_metrics['roc_auc']:.4f}")
    
    # Compile results
    results = {
        'best_params': best_params,
        'best_cv_score': best_score,
        'test_metrics': test_metrics,
        'cv_folds': cv_folds,
        'n_iter_search': n_iter
    }
    
    return best_model, results


# =============================================================================
# MODEL PERSISTENCE FUNCTIONS
# =============================================================================

def save_model(model: xgb.XGBClassifier, model_path: Path) -> None:
    """
    Save trained model to disk using joblib.
    
    Args:
        model: Trained XGBoost model
        model_path: Path to save the model
    """
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    print(f"\nModel saved to: {model_path}")


def save_metadata(metadata: Dict[str, Any], metadata_path: Path) -> None:
    """
    Save model metadata to JSON file.
    
    Args:
        metadata: Dictionary containing model metadata
        metadata_path: Path to save the metadata
    """
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert numpy types to Python native types for JSON serialization
    def convert_numpy_types(obj):
        if isinstance(obj, dict):
            return {k: convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(i) for i in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj
    
    metadata_clean = convert_numpy_types(metadata)
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata_clean, f, indent=2)
    
    print(f"Metadata saved to: {metadata_path}")


def save_feature_columns(feature_cols: list, feature_path: Path) -> None:
    """
    Save feature column order for inference alignment.
    
    Args:
        feature_cols: List of feature column names
        feature_path: Path to save the feature columns
    """
    feature_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(feature_path, 'w') as f:
        json.dump(feature_cols, f, indent=2)
    
    print(f"Feature columns saved to: {feature_path}")


# =============================================================================
# MAIN EXECUTION FUNCTION
# =============================================================================

def main():
    """
    Main function to orchestrate the complete model training pipeline.
    """
    print("=" * 60)
    print("HOSPITAL READMISSION PREDICTOR - MODEL TRAINING")
    print("=" * 60)
    
    # Step 1: Load data
    print("\n" + "-" * 40)
    print("Step 1: Loading Data")
    print("-" * 40)
    df = load_data(DATA_PATH)
    
    # Step 2: Prepare features and target
    print("\n" + "-" * 40)
    print("Step 2: Preparing Features and Target")
    print("-" * 40)
    X, y = prepare_features_and_target(df)
    
    # Step 3: Handle missing values
    print("\n" + "-" * 40)
    print("Step 3: Handling Missing Values")
    print("-" * 40)
    X = handle_missing_values(X)
    
    # Step 4: Feature engineering
    print("\n" + "-" * 40)
    print("Step 4: Feature Engineering")
    print("-" * 40)
    X = create_additional_features(X)
    
    # Step 5: Train-test split
    print("\n" + "-" * 40)
    print("Step 5: Train-Test Split")
    print("-" * 40)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y
    )
    print(f"Training samples: {len(y_train)}")
    print(f"Test samples: {len(y_test)}")
    
    # Step 6: Apply SMOTE for class imbalance
    print("\n" + "-" * 40)
    print("Step 6: Applying SMOTE")
    print("-" * 40)
    X_train_balanced, y_train_balanced = apply_smote(X_train, y_train)
    
    # Step 7: Scale features (optional for XGBoost but good practice)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_balanced)
    X_test_scaled = scaler.transform(X_test)
    
    # Convert back to DataFrame to preserve column names
    X_train_scaled = pd.DataFrame(X_train_scaled, columns=X_train_balanced.columns)
    X_test_scaled = pd.DataFrame(X_test_scaled, columns=X_test.columns)
    
    # Step 8: Train model with hyperparameter tuning
    print("\n" + "-" * 40)
    print("Step 8: Training XGBoost with Hyperparameter Tuning")
    print("-" * 40)
    model, results = train_xgboost_with_hyperparameter_tuning(
        X_train_scaled, y_train_balanced,
        X_test_scaled, y_test,
        cv_folds=CV_FOLDS,
        n_iter=N_ITER_SEARCH
    )
    
    # Step 9: Save model and artifacts
    print("\n" + "-" * 40)
    print("Step 9: Saving Model and Artifacts")
    print("-" * 40)
    save_model(model, MODEL_PATH)
    
    # Save metadata
    metadata = {
        'training_date': pd.Timestamp.now().isoformat(),
        'dataset_path': str(DATA_PATH),
        'feature_count': X.shape[1],
        'training_samples': len(y_train_balanced),
        'test_samples': len(y_test),
        'results': results
    }
    save_metadata(metadata, METADATA_PATH)
    
    # Save feature columns
    save_feature_columns(list(X.columns), FEATURE_COLUMNS_PATH)
    
    # Final summary
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"Model file: {MODEL_PATH}")
    print(f"Metadata file: {METADATA_PATH}")
    print(f"Feature columns file: {FEATURE_COLUMNS_PATH}")
    print(f"Final ROC-AUC: {results['test_metrics']['roc_auc']:.4f}")
    
    return model, results


if __name__ == "__main__":
    main()
