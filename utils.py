"""
Utility Functions and Constants for Hospital Readmission Predictor
===================================================================

This module contains shared utilities, constants, mappings, and helper functions
used across the application. It centralizes:
- Feature display names for human-readable labels
- CSV to model feature mappings for data alignment
- Clinical severity adjustment logic
- Data parsing and validation helpers
- Symptom options and validation lists

Usage:
    from utils import (
        FEATURE_DISPLAY_NAMES,
        CSV_TO_MODEL_MAPPING,
        SYMPTOM_OPTIONS,
        calculate_clinical_adjustment,
        parse_uploaded_file
    )
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import pandas as pd
import numpy as np


# =============================================================================
# CSV TO MODEL FEATURE MAPPING
# =============================================================================
# This dictionary provides explicit, strict mapping from CSV column names 
# to the exact 82 model feature names expected by the trained model.
# This ensures proper feature alignment during inference.
# =============================================================================

CSV_TO_MODEL_MAPPING: Dict[str, str] = {
    # Base admission features
    'prior_admissions': 'total_prior_admissions',
    'admission_type_id': 'admission_type_id',
    'discharge_disposition_id': 'discharge_disposition_id',
    'admission_source_id': 'admission_source_id',
    
    # Hospital stay features
    'time_in_hospital': 'time_in_hospital',
    'num_lab_procedures': 'num_lab_procedures',
    'num_procedures': 'num_procedures',
    
    # Medication features
    'num_medications': 'total_medications',
    'medication_count': 'total_medications',
    'total_medications': 'total_medications',
    
    # Visit count features
    'number_outpatient': 'number_outpatient',
    'outpatient_visits': 'number_outpatient',
    'number_emergency': 'number_emergency',
    'emergency_visits': 'number_emergency',
    'number_inpatient': 'number_inpatient',
    'inpatient_visits': 'number_inpatient',
    'inpatient_admissions': 'number_inpatient',
    
    # Diagnosis features
    'number_diagnoses': 'number_diagnoses',
    'diagnoses_count': 'number_diagnoses',
    'diabetes_diag_count': 'diabetes_diag_count',
    'diabetes_diagnoses': 'diabetes_diag_count',
    'comorbidity_count': 'comorbidity_count',
    'comorbidities': 'comorbidity_count',
    'num_comorbidities': 'comorbidity_count',
    
    # Age features
    'age_numeric': 'age_numeric',
    'age': 'age_numeric',
    'patient_age': 'age_numeric',
    
    # Medication encoding features (individual drugs)
    'metformin_encoded': 'metformin_encoded',
    'metformin': 'metformin_encoded',
    'metformin_active': 'metformin_active',
    'repaglinide_encoded': 'repaglinide_encoded',
    'repaglinide_active': 'repaglinide_active',
    'nateglinide_encoded': 'nateglinide_encoded',
    'nateglinide_active': 'nateglinide_active',
    'chlorpropamide_encoded': 'chlorpropamide_encoded',
    'chlorpropamide_active': 'chlorpropamide_active',
    'glimepiride_encoded': 'glimepiride_encoded',
    'glimepiride_active': 'glimepiride_active',
    'acetohexamide_encoded': 'acetohexamide_encoded',
    'acetohexamide_active': 'acetohexamide_active',
    'glipizide_encoded': 'glipizide_encoded',
    'glipizide_active': 'glipizide_active',
    'glyburide_encoded': 'glyburide_encoded',
    'glyburide_active': 'glyburide_active',
    'tolbutamide_encoded': 'tolbutamide_encoded',
    'tolbutamide_active': 'tolbutamide_active',
    'pioglitazone_encoded': 'pioglitazone_encoded',
    'pioglitazone_active': 'pioglitazone_active',
    'rosiglitazone_encoded': 'rosiglitazone_encoded',
    'rosiglitazone_active': 'rosiglitazone_active',
    'acarbose_encoded': 'acarbose_encoded',
    'acarbose_active': 'acarbose_active',
    'miglitol_encoded': 'miglitol_encoded',
    'miglitol_active': 'miglitol_active',
    'troglitazone_encoded': 'troglitazone_encoded',
    'troglitazone_active': 'troglitazone_active',
    'tolazamide_encoded': 'tolazamide_encoded',
    'tolazamide_active': 'tolazamide_active',
    'examide_encoded': 'examide_encoded',
    'examide_active': 'examide_active',
    'citoglipton_encoded': 'citoglipton_encoded',
    'citoglipton_active': 'citoglipton_active',
    'insulin_encoded': 'insulin_encoded',
    'insulin': 'insulin_encoded',
    'insulin_active': 'insulin_active',
    'insulin_therapy': 'on_insulin',
    'on_insulin': 'on_insulin',
    'glyburide-metformin_encoded': 'glyburide-metformin_encoded',
    'glyburide-metformin_active': 'glyburide-metformin_active',
    'glipizide-metformin_encoded': 'glipizide-metformin_encoded',
    'glipizide-metformin_active': 'glipizide-metformin_active',
    'glimepiride-pioglitazone_encoded': 'glimepiride-pioglitazone_encoded',
    'glimepiride-pioglitazone_active': 'glimepiride-pioglitazone_active',
    'metformin-rosiglitazone_encoded': 'metformin-rosiglitazone_encoded',
    'metformin-rosiglitazone_active': 'metformin-rosiglitazone_active',
    'metformin-pioglitazone_encoded': 'metformin-pioglitazone_encoded',
    'metformin-pioglitazone_active': 'metformin-pioglitazone_active',
    
    # Derived medication features
    'oral_medications': 'oral_medications',
    'change_encoded': 'change_encoded',
    'medication_change': 'change_encoded',
    'diabetesMed_encoded': 'diabetesMed_encoded',
    'diabetes_medication': 'diabetesMed_encoded',
    
    # num_medications maps to itself for consistency (also mapped to total_medications)
    'num_medications': 'num_medications',
    
    # Age-derived features
    'is_elderly': 'is_elderly',
    
    # Pre-computed engineered features (can be provided in CSV or calculated)
    'total_prior_admissions': 'total_prior_admissions',
    'emergency_ratio': 'emergency_ratio',
    'inpatient_ratio': 'inpatient_ratio',
    'long_stay': 'long_stay',
    'total_procedures': 'total_procedures',
    'high_lab_utilization': 'high_lab_utilization',
    'high_diagnosis_count': 'high_diagnosis_count',
    'emergency_admission': 'emergency_admission',
    'not_home_discharge': 'not_home_discharge',
    'er_admission': 'er_admission',
    
    # Interaction features
    'age_comorbidity_interaction': 'age_comorbidity_interaction',
    'med_per_comorbidity': 'med_per_comorbidity',
    'admissions_per_year': 'admissions_per_year',
    'emerg_inpatient_combo': 'emerg_inpatient_combo',
    'insulin_complexity': 'insulin_complexity',
    'diabetes_med_intensity': 'diabetes_med_intensity',
    
    # User-facing form fields (for manual input / simplified CSV)
    'discharge_diagnosis': 'discharge_diagnosis',
    'primary_diagnosis': 'discharge_diagnosis',
    'diagnosis_code': 'discharge_diagnosis',
    'high_risk_flag': 'high_risk_flag',
    'high_risk': 'high_risk_flag',
    'risk_flag': 'high_risk_flag',
    'symptoms': 'symptoms',
    'patient_symptoms': 'symptoms',
    'reported_symptoms': 'symptoms',
}


# =============================================================================
# FEATURE DISPLAY NAMES - HUMAN-READABLE LABELS FOR PATIENTS
# =============================================================================

FEATURE_DISPLAY_NAMES: Dict[str, str] = {
    # Core clinical features
    'time_in_hospital': 'Days Spent in Hospital',
    'num_lab_procedures': 'Number of Lab Tests',
    'num_procedures': 'Number of Medical Procedures',
    'num_medications': 'Total Medications Count',
    'number_outpatient': 'Outpatient Visits',
    'number_emergency': 'Emergency Room Visits',
    'number_inpatient': 'Inpatient Admissions',
    'number_diagnoses': 'Total Diagnoses Count',
    'diabetes_diag_count': 'Diabetes-Related Diagnoses',
    'comorbidity_count': 'Number of Other Health Conditions',
    
    # Medication features
    'metformin_encoded': 'Metformin Prescribed',
    'metformin_active': 'Metformin Active',
    'repaglinide_encoded': 'Repaglinide Prescribed',
    'repaglinide_active': 'Repaglinide Active',
    'nateglinide_encoded': 'Nateglinide Prescribed',
    'nateglinide_active': 'Nateglinide Active',
    'chlorpropamide_encoded': 'Chlorpropamide Prescribed',
    'chlorpropamide_active': 'Chlorpropamide Active',
    'glimepiride_encoded': 'Glimepiride Prescribed',
    'glimepiride_active': 'Glimepiride Active',
    'acetohexamide_encoded': 'Acetohexamide Prescribed',
    'acetohexamide_active': 'Acetohexamide Active',
    'glipizide_encoded': 'Glipizide Prescribed',
    'glipizide_active': 'Glipizide Active',
    'glyburide_encoded': 'Glyburide Prescribed',
    'glyburide_active': 'Glyburide Active',
    'tolbutamide_encoded': 'Tolbutamide Prescribed',
    'tolbutamide_active': 'Tolbutamide Active',
    'pioglitazone_encoded': 'Pioglitazone Prescribed',
    'pioglitazone_active': 'Pioglitazone Active',
    'rosiglitazone_encoded': 'Rosiglitazone Prescribed',
    'rosiglitazone_active': 'Rosiglitazone Active',
    'acarbose_encoded': 'Acarbose Prescribed',
    'acarbose_active': 'Acarbose Active',
    'miglitol_encoded': 'Miglitol Prescribed',
    'miglitol_active': 'Miglitol Active',
    'troglitazone_encoded': 'Troglitazone Prescribed',
    'troglitazone_active': 'Troglitazone Active',
    'tolazamide_encoded': 'Tolazamide Prescribed',
    'tolazamide_active': 'Tolazamide Active',
    'examide_encoded': 'Examide Prescribed',
    'examide_active': 'Examide Active',
    'citoglipton_encoded': 'Citoglipton Prescribed',
    'citoglipton_active': 'Citoglipton Active',
    'insulin_encoded': 'Insulin Therapy',
    'insulin_active': 'Insulin Active',
    'glyburide-metformin_encoded': 'Glyburide-Metformin Prescribed',
    'glyburide-metformin_active': 'Glyburide-Metformin Active',
    'glipizide-metformin_encoded': 'Glipizide-Metformin Prescribed',
    'glipizide-metformin_active': 'Glipizide-Metformin Active',
    'glimepiride-pioglitazone_encoded': 'Glimepiride-Pioglitazone Prescribed',
    'glimepiride-pioglitazone_active': 'Glimepiride-Pioglitazone Active',
    'metformin-rosiglitazone_encoded': 'Metformin-Rosiglitazone Prescribed',
    'metformin-rosiglitazone_active': 'Metformin-Rosiglitazone Active',
    'metformin-pioglitazone_encoded': 'Metformin-Pioglitazone Prescribed',
    'metformin-pioglitazone_active': 'Metformin-Pioglitazone Active',
    
    # Derived features
    'total_medications': 'Total Medications',
    'on_insulin': 'Currently on Insulin',
    'oral_medications': 'Taking Oral Medications',
    'change_encoded': 'Medication Change at Discharge',
    'diabetesMed_encoded': 'Diabetes Medication Prescribed',
    'age_numeric': 'Patient Age',
    'is_elderly': 'Elderly Patient (65+)',
    'total_prior_admissions': 'Total Prior Admissions',
    'emergency_ratio': 'Emergency Visit Ratio',
    'inpatient_ratio': 'Inpatient Stay Ratio',
    'long_stay': 'Extended Hospital Stay',
    'total_procedures': 'Total Procedures Performed',
    'high_lab_utilization': 'High Lab Test Usage',
    'high_diagnosis_count': 'Multiple Diagnoses',
    'emergency_admission': 'Emergency Admission',
    'not_home_discharge': 'Discharged to Non-Home Location',
    'er_admission': 'ER Admission',
    
    # Interaction features
    'age_comorbidity_interaction': 'Age × Health Conditions Interaction',
    'med_per_comorbidity': 'Medications per Health Condition',
    'admissions_per_year': 'Admissions per Year',
    'emerg_inpatient_combo': 'Emergency + Inpatient Combined',
    'insulin_complexity': 'Insulin Treatment Complexity',
    'diabetes_med_intensity': 'Diabetes Medication Intensity',
    
    # Administrative features
    'admission_type_id': 'Admission Type',
    'discharge_disposition_id': 'Discharge Location',
    'admission_source_id': 'Admission Source',
    
    # User-facing form fields
    'prior_admissions': 'Previous Hospital Admissions (Last 12 Months)',
    'discharge_diagnosis': 'Primary Discharge Diagnosis Code',
    'high_risk_flag': 'High Risk Patient Flag',
}


# =============================================================================
# SYMPTOM OPTIONS - VALID SYMPTOMS FOR MULTIPLE SELECT WIDGET
# =============================================================================

SYMPTOM_OPTIONS: List[str] = [
    "Fatigue",
    "Frequent urination",
    "Excessive thirst",
    "Blurred vision",
    "Slow-healing sores",
    "Tingling in hands/feet",
    "Increased hunger",
    "Unexplained weight loss",
    "Dry skin",
    "Frequent infections",
    "Irritability",
    "Nausea",
]

# Normalized symptom list for case-insensitive comparison
SYMPTOM_OPTIONS_NORMALIZED: List[str] = [s.lower() for s in SYMPTOM_OPTIONS]


# =============================================================================
# AGE GROUP MAPPINGS
# =============================================================================

AGE_GROUPS: List[str] = [
    "0-10", "10-20", "20-30", "30-40", "40-50",
    "50-60", "60-70", "70-80", "80-90", "90-100"
]


def age_numeric_to_age_group(age: int) -> Tuple[str, int]:
    """
    Convert numeric age to age group display string and selectbox index.
    
    Args:
        age: Patient's age in years
        
    Returns:
        Tuple of (age_group_display, age_group_index)
        
    Examples:
        >>> age_numeric_to_age_group(25)
        ('20-30', 2)
        >>> age_numeric_to_age_group(75)
        ('70-80', 7)
    """
    if age < 10:
        return ("0-10", 0)
    elif age < 20:
        return ("10-20", 1)
    elif age < 30:
        return ("20-30", 2)
    elif age < 40:
        return ("30-40", 3)
    elif age < 50:
        return ("40-50", 4)
    elif age < 60:
        return ("50-60", 5)
    elif age < 70:
        return ("60-70", 6)
    elif age < 80:
        return ("70-80", 7)
    elif age < 90:
        return ("80-90", 8)
    else:
        return ("90-100", 9)


# =============================================================================
# CLINICAL SEVERITY ADJUSTMENT LOGIC
# =============================================================================

def calculate_clinical_adjustment(features_dict: Dict[str, Any]) -> int:
    """
    Apply clinical severity adjustment based on established medical red flags.
    
    The ML model was trained on noisy UCI data and may produce counter-intuitive
    results (e.g., penalizing extremely high lab procedures). This post-processing
    layer ensures that clinically severe patients receive appropriate risk scores
    by adding heuristic bonuses for known risk factors.
    
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
        
    Example:
        >>> features = {'number_inpatient': 4, 'number_emergency': 2, 'age_numeric': 75}
        >>> calculate_clinical_adjustment(features)
        20  # 15 for inpatient + 5 for elderly
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
# FILE PARSING UTILITIES
# =============================================================================

def load_feature_columns(feature_columns_path: str = 'outputs/feature_columns.json') -> List[str]:
    """
    Load expected feature columns from JSON file.
    
    Args:
        feature_columns_path: Path to the feature columns JSON file
        
    Returns:
        List of feature column names
        
    Raises:
        FileNotFoundError: If feature columns file does not exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    try:
        path = Path(feature_columns_path)
        if not path.exists():
            raise FileNotFoundError(f"Feature columns file not found at {path}")
        
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load feature columns: {str(e)}")


def parse_uploaded_file(uploaded_file) -> Optional[Dict[str, Any]]:
    """
    Parse uploaded Excel or CSV file and extract patient features.
    
    This function:
    1. Reads the uploaded file (CSV or Excel)
    2. Maps CSV columns to model features using CSV_TO_MODEL_MAPPING
    3. Calculates data completeness percentage
    4. Handles special cases (age conversion, symptoms parsing, high_risk_flag)
    
    Args:
        uploaded_file: Streamlit UploadedFile object (CSV or Excel)
        
    Returns:
        Dictionary containing:
        - Mapped feature values
        - data_completeness_pct: Percentage of key clinical features provided
        - is_low_completeness: Boolean flag if completeness < 20%
        - age_group_display: Age group string (if age_numeric provided)
        - high_risk_display: "Yes"/"No" string (if high_risk_flag provided)
        - symptoms_list: List of validated symptom strings
        
    Raises:
        ValueError: If file format is unsupported or file is empty
    """
    try:
        # Determine file format and read accordingly
        file_name = uploaded_file.name.lower()
        if file_name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif file_name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            raise ValueError("Unsupported file format. Please upload .csv or .xlsx files.")
        
        if df.empty:
            raise ValueError("Uploaded file is empty.")
        
        # Get the first row as patient data
        patient_row = df.iloc[0]
        
        extracted_data: Dict[str, Any] = {}
        
        # Map CSV columns to model features using explicit mapping
        for csv_col, model_feature in CSV_TO_MODEL_MAPPING.items():
            if csv_col in df.columns:
                value = patient_row[csv_col]
                # Handle NaN values
                if pd.isna(value):
                    value = 0
                extracted_data[model_feature] = value
        
        # Special handling for 'prior_admissions' which maps to 'total_prior_admissions'
        # but also needs to set number_inpatient for derived feature calculation
        if 'prior_admissions' in df.columns:
            val = patient_row['prior_admissions']
            if not pd.isna(val):
                extracted_data['number_inpatient'] = int(val)
        
        # Special handling for 'num_medications' which maps to 'total_medications'
        # but we also need num_medications for consistency
        if 'num_medications' in df.columns:
            val = patient_row['num_medications']
            if not pd.isna(val):
                extracted_data['num_medications'] = int(val)
        
        # Calculate actual data completeness based on key clinical features
        key_clinical_features = [
            'total_prior_admissions', 'comorbidity_count', 'age_numeric',
            'total_medications', 'time_in_hospital', 'number_diagnoses'
        ]
        features_provided = sum(1 for f in key_clinical_features if f in extracted_data)
        data_completeness_pct = (features_provided / len(key_clinical_features)) * 100
        
        # Store completeness info for UI display
        extracted_data['data_completeness_pct'] = data_completeness_pct
        extracted_data['is_low_completeness'] = data_completeness_pct < 20.0
        
        # Special handling for age group conversion
        if 'age_numeric' in extracted_data:
            age = extracted_data['age_numeric']
            age_group, _ = age_numeric_to_age_group(int(age))
            extracted_data['age_group_display'] = age_group
        
        # Handle high_risk_flag conversion
        if 'high_risk_flag' in extracted_data:
            flag_val = extracted_data['high_risk_flag']
            extracted_data['high_risk_display'] = "Yes" if (
                flag_val == 1 or (isinstance(flag_val, str) and flag_val.lower() == 'yes')
            ) else "No"
        
        # Handle symptoms column - split by comma and map to symptom options
        if 'symptoms' in extracted_data:
            symptoms_str = str(extracted_data['symptoms'])
            if symptoms_str and symptoms_str.lower() != 'nan' and symptoms_str.strip():
                # Split by comma and strip whitespace to get individual symptoms
                raw_symptom_list = [s.strip() for s in symptoms_str.split(',')]
                
                # Validate against known symptom options (case-insensitive)
                validated_symptoms = []
                for symptom in raw_symptom_list:
                    symptom_lower = symptom.lower()
                    if symptom_lower in SYMPTOM_OPTIONS_NORMALIZED:
                        # Find the properly capitalized version
                        idx = SYMPTOM_OPTIONS_NORMALIZED.index(symptom_lower)
                        validated_symptoms.append(SYMPTOM_OPTIONS[idx])
                    else:
                        # Keep unrecognized symptoms as-is but capitalize first letter
                        validated_symptoms.append(symptom.title())
                
                extracted_data['symptoms_list'] = validated_symptoms
            else:
                extracted_data['symptoms_list'] = []
        else:
            extracted_data['symptoms_list'] = []
        
        return extracted_data
        
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to parse uploaded file: {str(e)}")


def validate_symptoms(symptoms_input: Any) -> List[str]:
    """
    Validate and normalize symptom input against known symptom options.
    
    Args:
        symptoms_input: Can be a string (comma-separated), list, or None
        
    Returns:
        List of validated symptom strings matching SYMPTOM_OPTIONS
    """
    if symptoms_input is None:
        return []
    
    if isinstance(symptoms_input, str):
        if not symptoms_input.strip() or symptoms_input.lower() == 'nan':
            return []
        symptoms_input = [s.strip() for s in symptoms_input.split(',')]
    
    if not isinstance(symptoms_input, list):
        return []
    
    validated_symptoms = []
    for symptom in symptoms_input:
        symptom_lower = str(symptom).lower().strip()
        if symptom_lower in SYMPTOM_OPTIONS_NORMALIZED:
            idx = SYMPTOM_OPTIONS_NORMALIZED.index(symptom_lower)
            validated_symptoms.append(SYMPTOM_OPTIONS[idx])
        else:
            # Keep unrecognized symptoms but capitalize properly
            validated_symptoms.append(str(symptom).title())
    
    return validated_symptoms
