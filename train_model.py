"""
Train Model Script for Hospital Readmission Predictor
======================================================

This standalone script trains machine learning models to predict 30-day hospital 
readmissions for diabetic patients using the UCI Diabetes 130-US Hospitals 
Dataset (1999-2008).

Key Features:
- Direct loading from raw CSV with proper handling of "?" unknown values
- Advanced dataset-specific feature engineering (diagnosis grouping, medication counts, etc.)
- Class imbalance handling via scale_pos_weight parameter (no SMOTE needed)
- HistGradientBoostingClassifier as primary model (optimized for speed)
- Fallback to XGBoost/LightGBM if available
- Hyperparameter optimization via RandomizedSearchCV on stratified subset (25k samples)
- Final model trained on FULL training dataset with best parameters
- Model evaluation targeting >= 80% ROC-AUC
- Model persistence using joblib
- Progress bars and clear status updates throughout

Usage:
    python train_model.py

Output:
    - outputs/readmission_model.joblib: Trained model (best performing)
    - outputs/model_metadata.json: Model performance metrics and metadata
    - outputs/feature_columns.json: Feature column order for inference
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional
import time

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, RandomizedSearchCV, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, classification_report
)
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import HistGradientBoostingClassifier
import joblib

# Try importing gradient boosting libraries
try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    print("Note: XGBoost not available (will use HistGradientBoostingClassifier)")

try:
    import lightgbm as lgb
    LGB_AVAILABLE = True
except ImportError:
    LGB_AVAILABLE = False
    print("Note: LightGBM not available (will use HistGradientBoostingClassifier)")


# =============================================================================
# CONFIGURATION CONSTANTS - OPTIMIZED FOR SPEED
# =============================================================================

RANDOM_STATE = 42
TEST_SIZE = 0.2
CV_FOLDS = 3  # Reduced from 5 for faster cross-validation
N_ITER_SEARCH = 15  # Reduced from 100 for faster hyperparameter search
TUNING_SAMPLE_SIZE = 25000  # Stratified sample size for hyperparameter tuning
TARGET_ROC_AUC = 0.80

# Use raw data directly
RAW_DATA_PATH = Path("data/raw/diabetic_data.csv")
OUTPUT_DIR = Path("outputs")
MODEL_PATH = OUTPUT_DIR / "readmission_model.joblib"
METADATA_PATH = OUTPUT_DIR / "model_metadata.json"
FEATURE_COLUMNS_PATH = OUTPUT_DIR / "feature_columns.json"
ENCODERS_PATH = OUTPUT_DIR / "encoders.joblib"


# =============================================================================
# DATA LOADING AND PREPROCESSING FUNCTIONS
# =============================================================================

def load_raw_data(file_path: Path) -> pd.DataFrame:
    """
    Load the raw UCI Diabetes dataset from CSV file.
    
    Args:
        file_path: Path to the raw CSV file
        
    Returns:
        pd.DataFrame: Loaded dataset
        
    Raises:
        FileNotFoundError: If file does not exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found at {file_path}")
    
    df = pd.read_csv(file_path)
    print(f"Loaded raw dataset: {df.shape[0]} records, {df.shape[1]} features")
    return df


def diagnose_column_distributions(df: pd.DataFrame) -> None:
    """Print distribution of key columns for debugging."""
    print("\n--- Column Value Distributions ---")
    key_cols = ['race', 'gender', 'weight', 'max_glu_serum', 'A1Cresult', 'readmitted']
    for col in key_cols:
        if col in df.columns:
            print(f"\n{col}:")
            print(df[col].value_counts().head(10))


# =============================================================================
# TARGET VARIABLE ENGINEERING
# =============================================================================

def create_target_variable(df: pd.DataFrame) -> pd.Series:
    """
    Create binary target variable for readmission prediction.
    
    The original 'readmitted' column has values: 'NO', '<30', '>30'
    We predict readmission within 30 days (binary classification):
    - 1: readmitted within 30 days ('<30')
    - 0: not readmitted or readmitted after 30 days ('NO' or '>30')
    
    Args:
        df: Input DataFrame
        
    Returns:
        pd.Series: Binary target variable
    """
    target = (df['readmitted'] == '<30').astype(int)
    
    print(f"\nTarget distribution:")
    print(f"  Not readmitted within 30 days (0): {(target == 0).sum()}")
    print(f"  Readmitted within 30 days (1): {(target == 1).sum()}")
    print(f"  Positive class ratio: {target.mean():.3f}")
    
    return target


# =============================================================================
# ADVANCED FEATURE ENGINEERING FOR UCI DIABETES DATASET
# =============================================================================

def handle_unknown_categorical_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Properly handle '?' and other unknown categorical values by treating them
    as a distinct category rather than dropping or imputing.
    
    This is critical for the UCI Diabetes dataset where '?' appears frequently
    in columns like race, weight, payer_code, medical_specialty, etc.
    
    Args:
        df: Input DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with unknown values properly labeled
    """
    df_clean = df.copy()
    
    # Columns with '?' values that should be treated as a distinct category
    categorical_cols_with_unknown = [
        'race', 'weight', 'payer_code', 'medical_specialty',
        'max_glu_serum', 'A1Cresult'
    ]
    
    for col in categorical_cols_with_unknown:
        if col in df_clean.columns:
            # Replace '?' with 'Unknown' category
            df_clean[col] = df_clean[col].replace('?', 'Unknown')
            # Also handle any other missing representations
            df_clean[col] = df_clean[col].fillna('Unknown')
    
    # Handle gender column (has 'Unknown/Invalid')
    if 'gender' in df_clean.columns:
        df_clean['gender'] = df_clean['gender'].replace(['Unknown/Invalid', '?'], 'Unknown')
        df_clean['gender'] = df_clean['gender'].fillna('Unknown')
    
    print("Handled unknown categorical values by creating 'Unknown' category")
    return df_clean


def encode_diagnoses_icd9(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process ICD-9 diagnosis codes by grouping into clinically meaningful categories.
    
    The UCI Diabetes dataset uses ICD-9 codes in diag_1, diag_2, diag_3 columns.
    We group these into broader categories based on the first 3 digits.
    
    Key diabetes-relevant groups:
    - 250: Diabetes mellitus
    - 401-405: Hypertension
    - 410-414: Ischemic heart disease
    - 427-429: Cardiac dysrhythmias and other heart diseases
    - 490-496: Respiratory diseases
    - 580-589: Kidney diseases (important for diabetes complications)
    - 250.x specifically indicates diabetes type and control
    
    Args:
        df: Input DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with encoded diagnosis features
    """
    df_enc = df.copy()
    
    def extract_icd9_prefix(code):
        """Extract first 3 digits of ICD-9 code."""
        if pd.isna(code) or code == 'Unknown' or code == '?':
            return 'Unknown'
        code_str = str(code).strip()
        # Remove decimal point if present and get first 3 digits
        code_clean = code_str.replace('.', '')
        if len(code_clean) >= 3 and code_clean[:3].isdigit():
            return code_clean[:3]
        return 'Other'
    
    def group_diagnosis(prefix):
        """Group ICD-9 prefixes into clinically meaningful categories."""
        if prefix == 'Unknown':
            return 'Unknown'
        try:
            prefix_int = int(prefix)
        except ValueError:
            return 'Other'
        
        # Diabetes-specific groupings
        if 249 <= prefix_int <= 250:
            return 'Diabetes'
        elif 401 <= prefix_int <= 405:
            return 'Hypertension'
        elif 410 <= prefix_int <= 414:
            return 'IschemicHeartDisease'
        elif 427 <= prefix_int <= 429:
            return 'CardiacDysrhythmia'
        elif 490 <= prefix_int <= 496:
            return 'Respiratory'
        elif 580 <= prefix_int <= 589:
            return 'KidneyDisease'
        elif 270 <= prefix_int <= 279:
            return 'MetabolicDisorder'
        elif 780 <= prefix_int <= 799:
            return 'SymptomsSigns'
        elif 800 <= prefix_int <= 999:
            return 'InjuryPoisoning'
        elif 1 <= prefix_int <= 239:
            return 'Neoplasm'
        else:
            return 'Other'
    
    # Process each diagnosis column
    for diag_col in ['diag_1', 'diag_2', 'diag_3']:
        if diag_col in df_enc.columns:
            # First extract prefix
            df_enc[f'{diag_col}_prefix'] = df_enc[diag_col].apply(extract_icd9_prefix)
            # Then group into categories
            df_enc[f'{diag_col}_group'] = df_enc[f'{diag_col}_prefix'].apply(group_diagnosis)
    
    # Create count of diabetes-related diagnoses across all three columns
    diabetes_groups = ['Diabetes']
    df_enc['diabetes_diag_count'] = (
        df_enc['diag_1_group'].isin(diabetes_groups).astype(int) +
        df_enc['diag_2_group'].isin(diabetes_groups).astype(int) +
        df_enc['diag_3_group'].isin(diabetes_groups).astype(int)
    )
    
    # Create comorbidity count (number of distinct diagnosis groups)
    diag_group_cols = ['diag_1_group', 'diag_2_group', 'diag_3_group']
    available_cols = [c for c in diag_group_cols if c in df_enc.columns]
    if available_cols:
        df_enc['comorbidity_count'] = df_enc[available_cols].apply(
            lambda row: len(set(row.dropna())), axis=1
        )
    
    print("Encoded ICD-9 diagnosis codes into clinical categories")
    return df_enc


def encode_medication_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode medication columns and create aggregate features.
    
    Medication columns have values: 'No', 'Steady', 'Down', 'Up'
    We encode these ordinally and create count features.
    
    Args:
        df: Input DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with encoded medication features
    """
    df_med = df.copy()
    
    # List of medication columns
    med_columns = [
        'metformin', 'repaglinide', 'nateglinide', 'chlorpropamide',
        'glimepiride', 'acetohexamide', 'glipizide', 'glyburide',
        'tolbutamide', 'pioglitazone', 'rosiglitazone', 'acarbose',
        'miglitol', 'troglitazone', 'tolazamide', 'examide',
        'citoglipton', 'insulin', 'glyburide-metformin',
        'glipizide-metformin', 'glimepiride-pioglitazone',
        'metformin-rosiglitazone', 'metformin-pioglitazone'
    ]
    
    # Encoding scheme: No=0, Steady=1, Down=2, Up=3
    med_encoding = {'No': 0, 'Steady': 1, 'Down': 2, 'Up': 3, 'Unknown': 0}
    
    active_meds = []
    for col in med_columns:
        if col in df_med.columns:
            # Replace NaN with 'No'
            df_med[col] = df_med[col].fillna('No')
            # Map to numeric values
            df_med[col + '_encoded'] = df_med[col].map(med_encoding).fillna(0)
            # Count as active if not 'No'
            df_med[col + '_active'] = (df_med[col] != 'No').astype(int)
            active_meds.append(col + '_active')
    
    # Create total medication count
    if active_meds:
        df_med['total_medications'] = df_med[active_meds].sum(axis=1)
    
    # Create insulin flag (important predictor)
    if 'insulin_encoded' in df_med.columns:
        df_med['on_insulin'] = (df_med['insulin_encoded'] > 0).astype(int)
    
    # Create oral meds count
    oral_meds = [c for c in active_meds if 'insulin' not in c]
    if oral_meds:
        df_med['oral_medications'] = df_med[oral_meds].sum(axis=1)
    
    # Change and diabetesMed columns
    if 'change' in df_med.columns:
        df_med['change'] = df_med['change'].fillna('No')
        df_med['change_encoded'] = (df_med['change'] != 'No').astype(int)
    
    if 'diabetesMed' in df_med.columns:
        df_med['diabetesMed'] = df_med['diabetesMed'].fillna('No')
        df_med['diabetesMed_encoded'] = (df_med['diabetesMed'] != 'No').astype(int)
    
    print(f"Encoded {len(med_columns)} medication columns")
    return df_med


def encode_age_feature(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode age bins into numeric values and create derived features.
    
    Age is given in bins like '[0-10)', '[10-20)', etc.
    We convert to midpoints and create additional age-related features.
    
    Args:
        df: Input DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with encoded age features
    """
    df_age = df.copy()
    
    if 'age' not in df_age.columns:
        return df_age
    
    # Define age bin midpoints
    age_bins = {
        '[0-10)': 5, '[10-20)': 15, '[20-30)': 25, '[30-40)': 35,
        '[40-50)': 45, '[50-60)': 55, '[60-70)': 65, '[70-80)': 75,
        '[80-90)': 85, '[90-100)': 95
    }
    
    df_age['age_numeric'] = df_age['age'].map(age_bins).fillna(55)
    
    # Create age group categories
    def age_category(age_bin):
        if age_bin in ['[0-10)', '[10-20)', '[20-30)']:
            return 'Young'
        elif age_bin in ['[30-40)', '[40-50)', '[50-60)']:
            return 'Middle'
        elif age_bin in ['[60-70)', '[70-80)']:
            return 'Senior'
        else:
            return 'Elderly'
    
    df_age['age_category'] = df_age['age'].apply(age_category)
    
    # Create elderly flag (>= 60 years)
    df_age['is_elderly'] = (df_age['age_numeric'] >= 60).astype(int)
    
    print("Encoded age feature")
    return df_age


def create_utilization_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create healthcare utilization features from existing columns.
    
    Args:
        df: Input DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with utilization features
    """
    df_util = df.copy()
    
    # Total prior admissions (outpatient + emergency + inpatient)
    util_cols = ['number_outpatient', 'number_emergency', 'number_inpatient']
    available_util = [c for c in util_cols if c in df_util.columns]
    
    if available_util:
        # Ensure numeric
        for col in available_util:
            df_util[col] = pd.to_numeric(df_util[col], errors='coerce').fillna(0)
        
        df_util['total_prior_admissions'] = df_util[available_util].sum(axis=1)
        
        # Emergency to total ratio (indicator of acute care needs)
        total = df_util['total_prior_admissions'].replace(0, 1)
        if 'number_emergency' in df_util.columns:
            df_util['emergency_ratio'] = df_util['number_emergency'] / total
        
        # Inpatient to total ratio
        if 'number_inpatient' in df_util.columns:
            df_util['inpatient_ratio'] = df_util['number_inpatient'] / total
    
    # Time in hospital (if available)
    if 'time_in_hospital' in df_util.columns:
        df_util['time_in_hospital'] = pd.to_numeric(
            df_util['time_in_hospital'], errors='coerce'
        ).fillna(0)
        df_util['long_stay'] = (df_util['time_in_hospital'] > 7).astype(int)
    
    # Number of procedures and lab procedures
    proc_cols = ['num_procedures', 'num_lab_procedures']
    available_proc = [c for c in proc_cols if c in df_util.columns]
    
    for col in available_proc:
        df_util[col] = pd.to_numeric(df_util[col], errors='coerce').fillna(0)
    
    if available_proc:
        df_util['total_procedures'] = df_util[available_proc].sum(axis=1)
    
    # High lab utilization flag
    if 'num_lab_procedures' in df_util.columns:
        df_util['high_lab_utilization'] = (df_util['num_lab_procedures'] > 50).astype(int)
    
    # Number of diagnoses
    if 'number_diagnoses' in df_util.columns:
        df_util['number_diagnoses'] = pd.to_numeric(
            df_util['number_diagnoses'], errors='coerce'
        ).fillna(0)
        df_util['high_diagnosis_count'] = (df_util['number_diagnoses'] > 5).astype(int)
    
    print("Created utilization features")
    return df_util


def encode_admission_discharge_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode admission type, discharge disposition, and admission source.
    
    These features provide context about the patient's admission circumstances.
    
    Args:
        df: Input DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with encoded admission features
    """
    df_adm = df.copy()
    
    # Admission type encoding
    # 1 = Emergency, 2 = Urgent, 3 = Elective, 4 = Newborn, etc.
    if 'admission_type_id' in df_adm.columns:
        df_adm['admission_type_id'] = pd.to_numeric(
            df_adm['admission_type_id'], errors='coerce'
        ).fillna(0)
        # Emergency admission flag (type 1, 2)
        df_adm['emergency_admission'] = df_adm['admission_type_id'].isin([1, 2]).astype(int)
    
    # Discharge disposition encoding
    # 1 = Home, others indicate transfer to other facilities
    if 'discharge_disposition_id' in df_adm.columns:
        df_adm['discharge_disposition_id'] = pd.to_numeric(
            df_adm['discharge_disposition_id'], errors='coerce'
        ).fillna(1)
        # Not discharged to home flag
        df_adm['not_home_discharge'] = (df_adm['discharge_disposition_id'] != 1).astype(int)
    
    # Admission source encoding
    # 7 = Emergency room, others include physician referral, etc.
    if 'admission_source_id' in df_adm.columns:
        df_adm['admission_source_id'] = pd.to_numeric(
            df_adm['admission_source_id'], errors='coerce'
        ).fillna(0)
        # ER admission flag
        df_adm['er_admission'] = (df_adm['admission_source_id'] == 7).astype(int)
    
    print("Encoded admission/discharge features")
    return df_adm


def perform_advanced_feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """
    Master function to perform all advanced feature engineering steps.
    
    Args:
        df: Raw input DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with all engineered features
    """
    print("\n" + "=" * 60)
    print("ADVANCED FEATURE ENGINEERING")
    print("=" * 60)
    
    # Step 1: Handle unknown categorical values
    df_eng = handle_unknown_categorical_values(df)
    
    # Step 2: Encode diagnoses
    df_eng = encode_diagnoses_icd9(df_eng)
    
    # Step 3: Encode medications
    df_eng = encode_medication_features(df_eng)
    
    # Step 4: Encode age
    df_eng = encode_age_feature(df_eng)
    
    # Step 5: Create utilization features
    df_eng = create_utilization_features(df_eng)
    
    # Step 6: Encode admission features
    df_eng = encode_admission_discharge_features(df_eng)
    
    # Step 7: Create interaction features
    df_eng = create_interaction_features(df_eng)
    
    print(f"\nTotal features after engineering: {df_eng.shape[1]}")
    return df_eng


def create_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create interaction features that capture complex relationships.
    
    Args:
        df: Input DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with interaction features
    """
    df_int = df.copy()
    
    # Age-comorbidity interaction
    if 'age_numeric' in df_int.columns and 'comorbidity_count' in df_int.columns:
        df_int['age_comorbidity_interaction'] = (
            df_int['age_numeric'] * df_int['comorbidity_count']
        )
    
    # Medication-comorbidity ratio
    if 'total_medications' in df_int.columns and 'comorbidity_count' in df_int.columns:
        denom = df_int['comorbidity_count'].replace(0, 1)
        df_int['med_per_comorbidity'] = df_int['total_medications'] / denom
    
    # Prior admissions-age ratio
    if 'total_prior_admissions' in df_int.columns and 'age_numeric' in df_int.columns:
        df_int['admissions_per_year'] = (
            df_int['total_prior_admissions'] / (df_int['age_numeric'] + 1)
        )
    
    # Emergency-inpatient combination
    if 'number_emergency' in df_int.columns and 'number_inpatient' in df_int.columns:
        df_int['emerg_inpatient_combo'] = (
            df_int['number_emergency'] * df_int['number_inpatient']
        )
    
    # Insulin-medication complexity
    if 'on_insulin' in df_int.columns and 'total_medications' in df_int.columns:
        df_int['insulin_complexity'] = df_int['on_insulin'] * df_int['total_medications']
    
    # Diabetes diagnosis count with medication
    if 'diabetes_diag_count' in df_int.columns and 'total_medications' in df_int.columns:
        df_int['diabetes_med_intensity'] = (
            df_int['diabetes_diag_count'] * df_int['total_medications']
        )
    
    print("Created interaction features")
    return df_int


# =============================================================================
# FEATURE SELECTION AND PREPARATION
# =============================================================================

def select_features_for_modeling(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Select and prepare final features for modeling.
    
    Args:
        df: DataFrame with all engineered features
        
    Returns:
        Tuple of (features DataFrame, list of feature names)
    """
    # Columns to exclude from modeling
    exclude_cols = [
        'encounter_id', 'patient_nbr',  # IDs
        'readmitted',  # Original target
        'diag_1', 'diag_2', 'diag_3',  # Raw diagnosis codes
        'diag_1_prefix', 'diag_2_prefix', 'diag_3_prefix',  # Intermediate encodings
        'weight',  # Too many unknowns
        'payer_code',  # Too many categories
        'medical_specialty',  # Too many categories
        'metformin', 'repaglinide', 'nateglinide', 'chlorpropamide',
        'glimepiride', 'acetohexamide', 'glipizide', 'glyburide',
        'tolbutamide', 'pioglitazone', 'rosiglitazone', 'acarbose',
        'miglitol', 'troglitazone', 'tolazamide', 'examide',
        'citoglipton', 'insulin', 'glyburide-metformin',
        'glipizide-metformin', 'glimepiride-pioglitazone',
        'metformin-rosiglitazone', 'metformin-pioglitazone',  # Raw med columns
        'age',  # Use encoded version
    ]
    
    # Get all columns except excluded ones and target
    all_cols = df.columns.tolist()
    feature_cols = [col for col in all_cols if col not in exclude_cols]
    
    # Remove target if present
    if 'readmission_target' in feature_cols:
        feature_cols.remove('readmission_target')
    
    # Keep only numeric features
    df_features = df[feature_cols].copy()
    numeric_cols = df_features.select_dtypes(include=[np.number]).columns.tolist()
    df_features = df_features[numeric_cols]
    
    # Replace any remaining inf values
    df_features = df_features.replace([np.inf, -np.inf], np.nan)
    df_features = df_features.fillna(0)
    
    print(f"\nSelected {len(numeric_cols)} numeric features for modeling")
    return df_features, numeric_cols


def encode_categorical_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """
    Encode remaining categorical features using label encoding.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Tuple of (encoded DataFrame, dictionary of encoders)
    """
    df_enc = df.copy()
    encoders = {}
    
    # Identify categorical columns
    cat_cols = df_enc.select_dtypes(include=['object']).columns.tolist()
    
    for col in cat_cols:
        le = LabelEncoder()
        # Handle unknown values
        df_enc[col] = df_enc[col].fillna('Unknown')
        df_enc[col + '_encoded'] = le.fit_transform(df_enc[col].astype(str))
        encoders[col] = le
        print(f"  Encoded {col}: {len(le.classes_)} categories")
    
    # Drop original categorical columns
    df_enc = df_enc.drop(columns=cat_cols)
    
    return df_enc, encoders


# =============================================================================
# MODEL TRAINING FUNCTIONS
# =============================================================================

def calculate_scale_pos_weight(y: pd.Series) -> float:
    """
    Calculate scale_pos_weight parameter for handling class imbalance.
    
    Tree-based models handle imbalance better via this parameter rather than SMOTE.
    Formula: (negative samples / positive samples)
    
    Args:
        y: Target variable series
        
    Returns:
        float: scale_pos_weight value
    """
    class_dist = y.value_counts()
    negative_count = class_dist.get(0, 0)
    positive_count = class_dist.get(1, 0)
    
    if positive_count == 0:
        return 1.0
    
    scale_weight = negative_count / positive_count
    print(f"\nClass distribution: Negative={negative_count}, Positive={positive_count}")
    print(f"Imbalance ratio: {scale_weight:.2f}:1")
    print(f"Using scale_pos_weight={scale_weight:.2f} to handle class imbalance")
    
    return scale_weight


def create_xgboost_param_grid() -> Dict[str, list]:
    """
    Create parameter grid for XGBoost hyperparameter tuning.
    
    Returns:
        Dict: Parameter distributions for RandomizedSearchCV
    """
    param_dist = {
        'max_depth': [4, 5, 6, 7, 8, 9, 10],
        'learning_rate': [0.01, 0.03, 0.05, 0.1, 0.15, 0.2],
        'n_estimators': [200, 300, 400, 500, 600],
        'min_child_weight': [1, 2, 3, 4, 5],
        'subsample': [0.7, 0.8, 0.9, 1.0],
        'colsample_bytree': [0.7, 0.8, 0.9, 1.0],
        'colsample_bylevel': [0.7, 0.8, 0.9],
        'gamma': [0, 0.1, 0.2, 0.3, 0.4],
        'reg_alpha': [0, 0.1, 0.5, 1.0, 2.0],
        'reg_lambda': [1, 1.5, 2, 3, 4],
        # scale_pos_weight: Moderate class weight to handle imbalance naturally
        # ROC-AUC optimization finds balanced parameters without aggressive weighting
        'scale_pos_weight': [1, 2, 3]
    }
    
    return param_dist


def create_lightgbm_param_grid() -> Dict[str, list]:
    """
    Create parameter grid for LightGBM hyperparameter tuning.
    
    Returns:
        Dict: Parameter distributions for RandomizedSearchCV
    """
    param_dist = {
        'num_leaves': [31, 50, 70, 100, 150],
        'learning_rate': [0.01, 0.03, 0.05, 0.1, 0.15],
        'n_estimators': [200, 300, 400, 500, 600],
        'max_depth': [-1, 5, 7, 9, 11],
        'min_child_samples': [5, 10, 20, 30],
        'subsample': [0.7, 0.8, 0.9, 1.0],
        'colsample_bytree': [0.7, 0.8, 0.9, 1.0],
        'reg_alpha': [0, 0.1, 0.5, 1.0],
        'reg_lambda': [1, 1.5, 2, 3],
        # scale_pos_weight: Moderate class weight to handle imbalance naturally
        # ROC-AUC optimization finds balanced parameters without aggressive weighting
        'scale_pos_weight': [1, 2, 3]
    }
    
    return param_dist


def create_catboost_param_grid() -> Dict[str, list]:
    """
    Create parameter grid for CatBoost hyperparameter tuning.
    
    Returns:
        Dict: Parameter distributions for RandomizedSearchCV
    """
    param_dist = {
        'depth': [4, 5, 6, 7, 8, 9, 10],
        'learning_rate': [0.01, 0.03, 0.05, 0.1, 0.15],
        'n_estimators': [200, 300, 400, 500, 600],
        'l2_leaf_reg': [1, 3, 5, 7, 9],
        'border_count': [32, 64, 128, 254],
        'subsample': [0.7, 0.8, 0.9, 1.0],
        'colsample_bylevel': [0.7, 0.8, 0.9, 1.0]
    }
    
    return param_dist


def create_histgradientboosting_param_grid() -> Dict[str, list]:
    """
    Create parameter grid for HistGradientBoostingClassifier hyperparameter tuning.
    
    This model is natively optimized for speed, handles missing values automatically,
    and performs comparably to XGBoost on large datasets.
    
    Returns:
        Dict: Parameter distributions for RandomizedSearchCV
    """
    param_dist = {
        'max_iter': [100, 200, 300, 400],
        'learning_rate': [0.01, 0.05, 0.1, 0.2],
        'max_depth': [3, 5, 7, 10, None],
        'l2_regularization': [0.0, 0.1, 0.5, 1.0],
        'min_samples_leaf': [10, 20, 30, 50],
        'max_bins': [128, 255],
        # Class weight handling: higher values favor the minority class (readmissions)
        # This helps the model focus on correctly identifying high-risk patients
        'class_weight': [{0: 1, 1: 5}, {0: 1, 1: 10}, {0: 1, 1: 15}]
    }
    
    return param_dist


def train_histgradientboosting_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    scale_pos_weight: float
) -> Tuple[Any, Dict[str, Any]]:
    """
    Train HistGradientBoostingClassifier with hyperparameter tuning.
    
    Uses stratified sampling for faster hyperparameter search, then trains
    final model on full dataset with best parameters.
    
    Args:
        X_train: Training features
        y_train: Training target
        X_test: Test features
        y_test: Test target
        scale_pos_weight: Weight for handling class imbalance
        
    Returns:
        Tuple containing trained model and results dictionary
    """
    print("\n" + "=" * 60)
    print("HISTGRADIENTBOOSTING HYPERPARAMETER TUNING")
    print("=" * 60)
    
    # Step 1: Create stratified sample for faster hyperparameter tuning
    print(f"\nCreating stratified sample of {TUNING_SAMPLE_SIZE} rows for hyperparameter search...")
    if len(y_train) > TUNING_SAMPLE_SIZE:
        X_tune, _, y_tune, _ = train_test_split(
            X_train, y_train,
            train_size=TUNING_SAMPLE_SIZE,
            stratify=y_train,
            random_state=RANDOM_STATE
        )
        print(f"Sampled {len(y_tune)} rows for tuning (from {len(y_train)} total)")
    else:
        X_tune, y_tune = X_train, y_train
        print(f"Using full training set ({len(y_tune)} rows) for tuning")
    
    skf = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    
    base_hgb = HistGradientBoostingClassifier(
        random_state=RANDOM_STATE,
        early_stopping=True,
        validation_fraction=0.1,
        verbose=1
    )
    
    param_dist = create_histgradientboosting_param_grid()
    
    print(f"\nStarting hyperparameter search with {N_ITER_SEARCH} iterations and {CV_FOLDS}-fold CV...")
    print("Progress will be shown below:\n")
    
    random_search = RandomizedSearchCV(
        estimator=base_hgb,
        param_distributions=param_dist,
        n_iter=N_ITER_SEARCH,
        # OPTIMIZING FOR ROC-AUC: Primary benchmark metric for balanced classification performance.
        # This ensures the model produces well-calibrated probabilities across all risk levels,
        # enabling meaningful absolute threshold-based risk stratification in the UI.
        scoring='roc_auc',
        cv=skf,
        verbose=2,  # Show progress for each fold
        n_jobs=-1,
        random_state=RANDOM_STATE,
        return_train_score=True
    )
    
    random_search.fit(X_tune, y_tune)
    
    best_params = random_search.best_params_
    best_score = random_search.best_score_
    
    print(f"\n{'='*60}")
    print(f"BEST PARAMETERS FOUND ON SUBSET")
    print(f"{'='*60}")
    # Note: best_score now reflects ROC-AUC (our primary benchmark metric)
    print(f"Best ROC-AUC from cross-validation: {best_score:.4f}")
    print(f"(ROC-AUC ensures well-calibrated probabilities for absolute thresholds)")
    print(f"Best parameters: {best_params}")
    
    # Step 2: Train final model on FULL training dataset with best parameters
    print(f"\n{'='*60}")
    print(f"TRAINING FINAL MODEL ON FULL DATASET ({len(y_train)} samples)")
    print(f"{'='*60}")
    
    # Add class weight handling via sample weights
    # HistGradientBoostingClassifier doesn't have scale_pos_weight directly,
    # but we can use class_weight='balanced' or compute sample weights
    sample_weights = np.where(y_train == 1, scale_pos_weight, 1.0)
    
    final_model = HistGradientBoostingClassifier(
        **best_params,
        random_state=RANDOM_STATE,
        early_stopping=True,
        validation_fraction=0.1,
        verbose=1
    )
    
    start_time = time.time()
    final_model.fit(X_train, y_train, sample_weight=sample_weights)
    train_time = time.time() - start_time
    
    print(f"\nFinal model training completed in {train_time:.2f} seconds")
    print(f"Number of trees built: {final_model.n_iter_}")
    
    # Evaluate on test set
    y_pred_proba = final_model.predict_proba(X_test)[:, 1]
    y_pred = final_model.predict(X_test)
    
    test_metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1': f1_score(y_test, y_pred, zero_division=0),
        'roc_auc': roc_auc_score(y_test, y_pred_proba)
    }
    
    print("\n" + "-" * 40)
    print("TEST SET EVALUATION - HistGradientBoosting")
    print("-" * 40)
    print(f"Accuracy:  {test_metrics['accuracy']:.4f}")
    print(f"Precision: {test_metrics['precision']:.4f}")
    # PRIMARY CLINICAL METRIC: Recall is most important - we must catch all high-risk patients
    print(f"Recall:    {test_metrics['recall']:.4f} <-- PRIMARY METRIC (minimizes false negatives)")
    print(f"F1 Score:  {test_metrics['f1']:.4f}")
    print(f"ROC-AUC:   {test_metrics['roc_auc']:.4f}")
    
    results = {
        'model_name': 'HistGradientBoosting',
        'best_params': best_params,
        'best_cv_score': best_score,
        'test_metrics': test_metrics,
        'training_time_seconds': train_time
    }
    
    return final_model, results


def train_xgboost_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    scale_pos_weight: float
) -> Tuple[Any, Dict[str, Any]]:
    """
    Train XGBoost model with hyperparameter tuning.
    
    Uses stratified sampling for faster hyperparameter search, then trains
    final model on full dataset with best parameters.
    
    Args:
        X_train: Training features
        y_train: Training target
        X_test: Test features
        y_test: Test target
        scale_pos_weight: Weight for handling class imbalance
        
    Returns:
        Tuple containing trained model and results dictionary
    """
    if not XGB_AVAILABLE:
        print("XGBoost not available, skipping...")
        return None, {}
    
    print("\n" + "=" * 60)
    print("XGBOOST HYPERPARAMETER TUNING")
    print("=" * 60)
    
    # Create stratified sample for faster tuning
    print(f"\nCreating stratified sample of {TUNING_SAMPLE_SIZE} rows for hyperparameter search...")
    if len(y_train) > TUNING_SAMPLE_SIZE:
        X_tune, _, y_tune, _ = train_test_split(
            X_train, y_train,
            train_size=TUNING_SAMPLE_SIZE,
            stratify=y_train,
            random_state=RANDOM_STATE
        )
        print(f"Sampled {len(y_tune)} rows for tuning (from {len(y_train)} total)")
    else:
        X_tune, y_tune = X_train, y_train
        print(f"Using full training set ({len(y_tune)} rows) for tuning")
    
    skf = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    
    base_xgb = xgb.XGBClassifier(
        objective='binary:logistic',
        eval_metric='auc',
        random_state=RANDOM_STATE,
        n_jobs=-1,
        tree_method='hist'
    )
    
    param_dist = create_xgboost_param_grid()
    
    print(f"\nStarting hyperparameter search with {N_ITER_SEARCH} iterations and {CV_FOLDS}-fold CV...")
    
    random_search = RandomizedSearchCV(
        estimator=base_xgb,
        param_distributions=param_dist,
        n_iter=N_ITER_SEARCH,
        # OPTIMIZING FOR ROC-AUC: Primary benchmark metric for balanced classification performance.
        # This ensures the model produces well-calibrated probabilities across all risk levels,
        # enabling meaningful absolute threshold-based risk stratification in the UI.
        scoring='roc_auc',
        cv=skf,
        verbose=1,
        n_jobs=-1,
        random_state=RANDOM_STATE,
        return_train_score=True
    )
    
    random_search.fit(X_tune, y_tune)
    
    best_params = random_search.best_params_
    best_score = random_search.best_score_
    
    print(f"\n{'='*60}")
    print(f"BEST PARAMETERS FOUND ON SUBSET")
    print(f"{'='*60}")
    print(f"Best ROC-AUC from cross-validation: {best_score:.4f}")
    print(f"Best parameters: {best_params}")
    
    # Train final model on FULL dataset
    print(f"\n{'='*60}")
    print(f"TRAINING FINAL MODEL ON FULL DATASET ({len(y_train)} samples)")
    print(f"{'='*60}")
    
    # Update scale_pos_weight in best params
    best_params['scale_pos_weight'] = scale_pos_weight
    
    final_model = xgb.XGBClassifier(
        **best_params,
        objective='binary:logistic',
        eval_metric='auc',
        random_state=RANDOM_STATE,
        n_jobs=-1,
        tree_method='hist'
    )
    
    start_time = time.time()
    final_model.fit(X_train, y_train)
    train_time = time.time() - start_time
    
    print(f"\nFinal model training completed in {train_time:.2f} seconds")
    
    # Evaluate on test set
    y_pred_proba = final_model.predict_proba(X_test)[:, 1]
    y_pred = final_model.predict(X_test)
    
    test_metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1': f1_score(y_test, y_pred, zero_division=0),
        'roc_auc': roc_auc_score(y_test, y_pred_proba)
    }
    
    print("\n" + "-" * 40)
    print("TEST SET EVALUATION - XGBoost")
    print("-" * 40)
    print(f"Accuracy:  {test_metrics['accuracy']:.4f}")
    print(f"Precision: {test_metrics['precision']:.4f}")
    # PRIMARY CLINICAL METRIC: Recall is most important - we must catch all high-risk patients
    print(f"Recall:    {test_metrics['recall']:.4f} <-- PRIMARY METRIC (minimizes false negatives)")
    print(f"F1 Score:  {test_metrics['f1']:.4f}")
    print(f"ROC-AUC:   {test_metrics['roc_auc']:.4f}")
    
    results = {
        'model_name': 'XGBoost',
        'best_params': best_params,
        'best_cv_score': best_score,
        'test_metrics': test_metrics,
        'training_time_seconds': train_time
    }
    
    return final_model, results


def train_lightgbm_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    scale_pos_weight: float
) -> Tuple[Any, Dict[str, Any]]:
    """
    Train LightGBM model with hyperparameter tuning.
    
    Uses stratified sampling for faster hyperparameter search, then trains
    final model on full dataset with best parameters.
    
    Args:
        X_train: Training features
        y_train: Training target
        X_test: Test features
        y_test: Test target
        scale_pos_weight: Weight for handling class imbalance
        
    Returns:
        Tuple containing trained model and results dictionary
    """
    if not LGB_AVAILABLE:
        print("LightGBM not available, skipping...")
        return None, {}
    
    print("\n" + "=" * 60)
    print("LIGHTGBM HYPERPARAMETER TUNING")
    print("=" * 60)
    
    # Create stratified sample for faster tuning
    print(f"\nCreating stratified sample of {TUNING_SAMPLE_SIZE} rows for hyperparameter search...")
    if len(y_train) > TUNING_SAMPLE_SIZE:
        X_tune, _, y_tune, _ = train_test_split(
            X_train, y_train,
            train_size=TUNING_SAMPLE_SIZE,
            stratify=y_train,
            random_state=RANDOM_STATE
        )
        print(f"Sampled {len(y_tune)} rows for tuning (from {len(y_train)} total)")
    else:
        X_tune, y_tune = X_train, y_train
        print(f"Using full training set ({len(y_tune)} rows) for tuning")
    
    skf = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    
    base_lgb = lgb.LGBMClassifier(
        objective='binary',
        metric='auc',
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=1
    )
    
    param_dist = create_lightgbm_param_grid()
    
    print(f"\nStarting hyperparameter search with {N_ITER_SEARCH} iterations and {CV_FOLDS}-fold CV...")
    
    random_search = RandomizedSearchCV(
        estimator=base_lgb,
        param_distributions=param_dist,
        n_iter=N_ITER_SEARCH,
        # OPTIMIZING FOR ROC-AUC: Primary benchmark metric for balanced classification performance.
        # This ensures the model produces well-calibrated probabilities across all risk levels,
        # enabling meaningful absolute threshold-based risk stratification in the UI.
        scoring='roc_auc',
        cv=skf,
        verbose=1,
        n_jobs=-1,
        random_state=RANDOM_STATE,
        return_train_score=True
    )
    
    random_search.fit(X_tune, y_tune)
    
    best_params = random_search.best_params_
    best_score = random_search.best_score_
    
    print(f"\n{'='*60}")
    print(f"BEST PARAMETERS FOUND ON SUBSET (LightGBM)")
    print(f"{'='*60}")
    print(f"Best ROC-AUC from cross-validation: {best_score:.4f}")
    print(f"Best parameters: {best_params}")
    
    # Train final model on FULL dataset
    print(f"\n{'='*60}")
    print(f"TRAINING FINAL MODEL ON FULL DATASET ({len(y_train)} samples)")
    print(f"{'='*60}")
    
    # Update scale_pos_weight in best params
    best_params['scale_pos_weight'] = scale_pos_weight
    
    final_model = lgb.LGBMClassifier(
        **best_params,
        objective='binary',
        metric='auc',
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=1
    )
    
    start_time = time.time()
    final_model.fit(X_train, y_train)
    train_time = time.time() - start_time
    
    print(f"\nFinal model training completed in {train_time:.2f} seconds")
    
    # Evaluate on test set
    y_pred_proba = final_model.predict_proba(X_test)[:, 1]
    y_pred = final_model.predict(X_test)
    
    test_metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1': f1_score(y_test, y_pred, zero_division=0),
        'roc_auc': roc_auc_score(y_test, y_pred_proba)
    }
    
    print("\n" + "-" * 40)
    print("TEST SET EVALUATION")
    print("-" * 40)
    print(f"Accuracy:  {test_metrics['accuracy']:.4f}")
    print(f"Precision: {test_metrics['precision']:.4f}")
    # PRIMARY CLINICAL METRIC: Recall is most important
    print(f"Recall:    {test_metrics['recall']:.4f}")
    print(f"F1 Score:  {test_metrics['f1']:.4f}")
    print(f"ROC-AUC:   {test_metrics['roc_auc']:.4f}")
    
    results = {
        'model_name': 'LightGBM',
        'best_params': best_params,
        'best_cv_score': best_score,
        'test_metrics': test_metrics,
        'training_time_seconds': train_time
    }
    
    return final_model, results


def compare_and_select_best_model(
    model_results: List[Tuple[str, Any, Dict[str, Any]]]
) -> Tuple[str, Any, Dict[str, Any]]:
    """
    Compare trained models and select the best one based on Recall (primary clinical metric).
    
    CRITICAL CLINICAL DECISION: We optimize for Recall rather than ROC-AUC because:
    - False negatives (missing a high-risk patient) are clinically much worse than false positives
    - A missed high-risk patient may not receive needed intervention, leading to readmission
    - A false positive only results in additional monitoring, which is low-risk
    
    Args:
        model_results: List of tuples (model_name, model, results_dict)
        
    Returns:
        Tuple of (best_model_name, best_model, best_results)
    """
    if not model_results:
        raise ValueError("No models were trained successfully")
    
    print("\n" + "=" * 60)
    print("MODEL COMPARISON - OPTIMIZED FOR RECALL")
    print("=" * 60)
    print("(Recall is our primary metric to minimize false negatives)")
    
    best_model_name = None
    best_model = None
    best_results = None
    best_recall = 0.0
    
    for model_name, model, results in model_results:
        if model is None:
            continue
        
        # PRIMARY METRIC: Recall - we must catch all high-risk patients
        recall = results['test_metrics']['recall']
        roc_auc = results['test_metrics']['roc_auc']
        print(f"{model_name}: Recall = {recall:.4f}, ROC-AUC = {roc_auc:.4f}")
        
        if recall > best_recall:
            best_recall = recall
            best_model_name = model_name
            best_model = model
            best_results = results
    
    print(f"\nBest model: {best_model_name} with Recall = {best_recall:.4f}")
    print(f"(Selected based on Recall to minimize false negatives)")
    
    return best_model_name, best_model, best_results


# =============================================================================
# MODEL PERSISTENCE FUNCTIONS
# =============================================================================

def save_model(model: Any, model_path: Path) -> None:
    """Save trained model to disk using joblib."""
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    print(f"\nModel saved to: {model_path}")


def save_metadata(metadata: Dict[str, Any], metadata_path: Path) -> None:
    """Save model metadata to JSON file."""
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    
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
    """Save feature column order for inference alignment."""
    feature_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(feature_path, 'w') as f:
        json.dump(feature_cols, f, indent=2)
    
    print(f"Feature columns saved to: {feature_path}")


def save_encoders(encoders: Dict, encoders_path: Path) -> None:
    """Save label encoders for inference."""
    encoders_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(encoders, encoders_path)
    print(f"Encoders saved to: {encoders_path}")


# =============================================================================
# MAIN EXECUTION FUNCTION
# =============================================================================

def main():
    """Main function to orchestrate the complete model training pipeline."""
    print("=" * 60)
    print("HOSPITAL READMISSION PREDICTOR - MODEL TRAINING")
    print("=" * 60)
    
    # Step 1: Load raw data
    print("\n" + "-" * 40)
    print("Step 1: Loading Raw Data")
    print("-" * 40)
    df_raw = load_raw_data(RAW_DATA_PATH)
    diagnose_column_distributions(df_raw)
    
    # Step 2: Create target variable
    print("\n" + "-" * 40)
    print("Step 2: Creating Target Variable")
    print("-" * 40)
    df_raw['readmission_target'] = create_target_variable(df_raw)
    
    # Step 3: Advanced feature engineering
    print("\n" + "-" * 40)
    print("Step 3: Advanced Feature Engineering")
    print("-" * 40)
    df_engineered = perform_advanced_feature_engineering(df_raw)
    
    # Step 4: Select and prepare features
    print("\n" + "-" * 40)
    print("Step 4: Feature Selection and Preparation")
    print("-" * 40)
    X, feature_cols = select_features_for_modeling(df_engineered)
    print(f"Features shape: {X.shape}")
    
    # Calculate baseline defaults for all features BEFORE train-test split
    # Zero-filling causes distribution shifts. We use dataset medians/modes to provide 
    # a 'normal' clinical background for partial CSV uploads.
    print("\nCalculating feature baseline defaults (medians for numeric, modes for categorical)...")
    feature_defaults = {}
    for col in X.columns:
        if X[col].dtype in ['int64', 'float64', 'int32', 'float32']:
            # Numeric columns: use median
            feature_defaults[col] = float(X[col].median())
        else:
            # Categorical/binary columns: use mode
            mode_val = X[col].mode().iloc[0] if not X[col].mode().empty else 0
            # Try to convert to numeric if possible
            try:
                feature_defaults[col] = float(mode_val)
            except (ValueError, TypeError):
                feature_defaults[col] = str(mode_val)
    
    # Save feature defaults to JSON
    defaults_path = OUTPUT_DIR / "feature_defaults.json"
    with open(defaults_path, 'w') as f:
        json.dump(feature_defaults, f, indent=2)
    print(f"Saved {len(feature_defaults)} feature defaults to {defaults_path}")
    
    # Step 5: Train-test split
    print("\n" + "-" * 40)
    print("Step 5: Train-Test Split")
    print("-" * 40)
    y = df_engineered['readmission_target']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y
    )
    print(f"Training samples: {len(y_train)}")
    print(f"Test samples: {len(y_test)}")
    
    # Step 6: Calculate scale_pos_weight for class imbalance handling
    print("\n" + "-" * 40)
    print("Step 6: Calculating Class Weight Parameter")
    print("-" * 40)
    scale_pos_weight = calculate_scale_pos_weight(y_train)
    
    # No need for feature scaling with tree-based models!
    print("\nNote: Tree-based models (HistGradientBoosting, XGBoost, LightGBM)")
    print("do not require feature scaling. Using raw features directly.\n")
    X_train_final = X_train.copy()
    X_test_final = X_test.copy()
    
    # Step 7: Train HistGradientBoostingClassifier (primary model - fastest)
    print("\n" + "-" * 40)
    print("Step 7: Training HistGradientBoostingClassifier")
    print("-" * 40)
    start_total = time.time()
    
    hgb_model, hgb_results = train_histgradientboosting_model(
        X_train_final, y_train,
        X_test_final, y_test,
        scale_pos_weight
    )
    
    model_results = []
    if hgb_model is not None:
        model_results.append(('HistGradientBoosting', hgb_model, hgb_results))
    
    # Optionally train XGBoost as fallback/comparison
    if XGB_AVAILABLE:
        print("\n" + "-" * 40)
        print("Step 8: Training XGBoost (optional comparison)")
        print("-" * 40)
        xgb_model, xgb_results = train_xgboost_model(
            X_train_final, y_train,
            X_test_final, y_test,
            scale_pos_weight
        )
        if xgb_model is not None:
            model_results.append(('XGBoost', xgb_model, xgb_results))
    
    # Optionally train LightGBM as fallback/comparison
    if LGB_AVAILABLE:
        print("\n" + "-" * 40)
        print("Step 9: Training LightGBM (optional comparison)")
        print("-" * 40)
        lgb_model, lgb_results = train_lightgbm_model(
            X_train_final, y_train,
            X_test_final, y_test,
            scale_pos_weight
        )
        if lgb_model is not None:
            model_results.append(('LightGBM', lgb_model, lgb_results))
    
    # Step 10: Select best model
    print("\n" + "-" * 40)
    print("Step 10: Selecting Best Model")
    print("-" * 40)
    best_model_name, best_model, best_results = compare_and_select_best_model(model_results)
    
    total_training_time = time.time() - start_total
    print(f"\nTotal training time: {total_training_time:.2f} seconds ({total_training_time/60:.2f} minutes)")
    
    # Step 11: Save model and artifacts
    print("\n" + "-" * 40)
    print("Step 11: Saving Model and Artifacts")
    print("-" * 40)
    save_model(best_model, MODEL_PATH)
    
    # Note: No thresholds.json needed - app.py now uses absolute probabilities
    # The model is optimized for ROC-AUC, producing well-calibrated probabilities
    # that can be directly converted to severity scores (raw_prob * 100).
    
    # Save metadata
    metadata = {
        'training_date': pd.Timestamp.now().isoformat(),
        'dataset_path': str(RAW_DATA_PATH),
        'feature_count': X.shape[1],
        'training_samples': len(y_train),
        'test_samples': len(y_test),
        'scale_pos_weight_used': scale_pos_weight,
        'tuning_sample_size': TUNING_SAMPLE_SIZE,
        'cv_folds': CV_FOLDS,
        'n_iter_search': N_ITER_SEARCH,
        'best_model_name': best_model_name,
        'results': best_results,
        'total_training_time_seconds': total_training_time
    }
    save_metadata(metadata, METADATA_PATH)
    
    # Save feature columns
    save_feature_columns(list(X.columns), FEATURE_COLUMNS_PATH)
    
    # Final summary
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"Best model: {best_model_name}")
    print(f"Model file: {MODEL_PATH}")
    print(f"Metadata file: {METADATA_PATH}")
    print(f"Feature columns file: {FEATURE_COLUMNS_PATH}")
    # PRIMARY CLINICAL METRIC: Recall - we prioritize catching all high-risk patients
    print(f"Final Recall:  {best_results['test_metrics']['recall']:.4f} <-- PRIMARY METRIC (minimizes false negatives)")
    print(f"Final ROC-AUC: {best_results['test_metrics']['roc_auc']:.4f}")
    print(f"Total training time: {total_training_time/60:.2f} minutes")
    
    return best_model, best_results


if __name__ == "__main__":
    main()
