"""
Utility Functions for Hospital Readmission Predictor API
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import pandas as pd
import numpy as np


def convert_to_native(obj: Any) -> Any:
    """
    Recursively convert numpy/pandas types to native Python types.
    
    This is required because Pydantic v2 cannot serialize numpy types like
    np.int64, np.float64, np.bool_, np.ndarray, pd.Timestamp, etc.
    
    Args:
        obj: Object to convert (dict, list, or scalar value)
        
    Returns:
        Object with all numpy/pandas types converted to native Python types
    """
    if isinstance(obj, dict):
        return {k: convert_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_native(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, (pd.Series, pd.DataFrame)):
        return convert_to_native(obj.to_dict())
    elif pd.isna(obj):
        return None
    else:
        return obj


CSV_TO_MODEL_MAPPING: Dict[str, str] = {
    'prior_admissions': 'total_prior_admissions',
    'admission_type_id': 'admission_type_id',
    'discharge_disposition_id': 'discharge_disposition_id',
    'admission_source_id': 'admission_source_id',
    'time_in_hospital': 'time_in_hospital',
    'num_lab_procedures': 'num_lab_procedures',
    'num_procedures': 'num_procedures',
    'num_medications': 'total_medications',
    'medication_count': 'total_medications',
    'total_medications': 'total_medications',
    'number_outpatient': 'number_outpatient',
    'outpatient_visits': 'number_outpatient',
    'number_emergency': 'number_emergency',
    'emergency_visits': 'number_emergency',
    'number_inpatient': 'number_inpatient',
    'inpatient_visits': 'number_inpatient',
    'inpatient_admissions': 'number_inpatient',
    'number_diagnoses': 'number_diagnoses',
    'diagnoses_count': 'number_diagnoses',
    'diabetes_diag_count': 'diabetes_diag_count',
    'diabetes_diagnoses': 'diabetes_diag_count',
    'comorbidity_count': 'comorbidity_count',
    'comorbidities': 'comorbidity_count',
    'num_comorbidities': 'comorbidity_count',
    'age_numeric': 'age_numeric',
    'age': 'age_numeric',
    'patient_age': 'age_numeric',
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
    'oral_medications': 'oral_medications',
    'change_encoded': 'change_encoded',
    'medication_change': 'change_encoded',
    'diabetesMed_encoded': 'diabetesMed_encoded',
    'diabetes_medication': 'diabetesMed_encoded',
    'num_medications': 'num_medications',
    'is_elderly': 'is_elderly',
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
    'age_comorbidity_interaction': 'age_comorbidity_interaction',
    'med_per_comorbidity': 'med_per_comorbidity',
    'admissions_per_year': 'admissions_per_year',
    'emerg_inpatient_combo': 'emerg_inpatient_combo',
    'insulin_complexity': 'insulin_complexity',
    'diabetes_med_intensity': 'diabetes_med_intensity',
    'discharge_diagnosis': 'discharge_diagnosis',
    'primary_diagnosis': 'discharge_diagnosis',
    'diagnosis_code': 'discharge_diagnosis',
    'high_risk_flag': 'high_risk_flag',
    'high_risk': 'high_risk_flag',
    'risk_flag': 'high_risk_flag',
    'symptoms': 'symptoms',
    'patient_symptoms': 'symptoms',
    'reported_symptoms': 'symptoms',
    'chas_tier': 'chas_tier',
    'chas_plan': 'chas_tier',
    'diagnosis': 'number_diagnoses',
    'condition': 'number_diagnoses',
    'diagnoses': 'number_diagnoses',
    'bp': 'blood_pressure_display',
    'systolic_bp': 'blood_pressure_display',
    'blood_pressure': 'blood_pressure_display',
    'hba1c': 'hba1c_display',
    'a1c': 'hba1c_display',
    'hemoglobin_a1c': 'hba1c_display',
}

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

SYMPTOM_OPTIONS_NORMALIZED: List[str] = [s.lower() for s in SYMPTOM_OPTIONS]


def calculate_clinical_adjustment(features_dict: Dict[str, Any]) -> int:
    adjustment_points: int = 0

    if features_dict.get('number_inpatient', 0) >= 3:
        adjustment_points += 15

    if features_dict.get('number_emergency', 0) >= 3:
        adjustment_points += 10

    if features_dict.get('num_lab_procedures', 0) >= 60:
        adjustment_points += 10

    if features_dict.get('num_medications', 0) >= 15:
        adjustment_points += 10

    if features_dict.get('age_numeric', 0) >= 70:
        adjustment_points += 5

    return adjustment_points


AGE_GROUPS: List[str] = [
    "0-10", "10-20", "20-30", "30-40", "40-50",
    "50-60", "60-70", "70-80", "80-90", "90-100"
]


def age_numeric_to_age_group(age: int) -> Tuple[str, int]:
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


def parse_uploaded_file_bytes(file_bytes: bytes, file_name: str) -> Dict[str, Any]:
    try:
        file_name_lower = file_name.lower()
        if file_name_lower.endswith('.csv'):
            df = pd.read_csv(pd.io.common.BytesIO(file_bytes), encoding='utf-8')
        elif file_name_lower.endswith('.xlsx'):
            df = pd.read_excel(pd.io.common.BytesIO(file_bytes))
        else:
            raise ValueError("Unsupported file format. Please upload .csv or .xlsx files.")

        if df.empty:
            raise ValueError("Uploaded file is empty.")

        patient_row = df.iloc[0]
        extracted_data: Dict[str, Any] = {}

        for csv_col, model_feature in CSV_TO_MODEL_MAPPING.items():
            if csv_col in df.columns:
                value = patient_row[csv_col]
                if pd.isna(value):
                    value = 0
                extracted_data[model_feature] = value

        if 'prior_admissions' in df.columns:
            val = patient_row['prior_admissions']
            if not pd.isna(val):
                extracted_data['number_inpatient'] = int(val)

        if 'num_medications' in df.columns:
            val = patient_row['num_medications']
            if not pd.isna(val):
                extracted_data['num_medications'] = int(val)

        key_clinical_features = [
            'total_prior_admissions', 'comorbidity_count', 'age_numeric',
            'total_medications', 'time_in_hospital', 'number_diagnoses'
        ]
        features_provided = sum(1 for f in key_clinical_features if f in extracted_data)
        data_completeness_pct = (features_provided / len(key_clinical_features)) * 100

        extracted_data['data_completeness_pct'] = data_completeness_pct
        extracted_data['is_low_completeness'] = data_completeness_pct < 20.0

        if 'age_numeric' in extracted_data:
            age = extracted_data['age_numeric']
            age_group, _ = age_numeric_to_age_group(int(age))
            extracted_data['age_group_display'] = age_group
            extracted_data['age_group'] = age_group

        if 'high_risk_flag' in extracted_data:
            flag_val = extracted_data['high_risk_flag']
            extracted_data['high_risk_display'] = "Yes" if (
                flag_val == 1 or (isinstance(flag_val, str) and str(flag_val).lower() == 'yes')
            ) else "No"

        if 'symptoms' in extracted_data:
            symptoms_str = str(extracted_data['symptoms'])
            if symptoms_str and symptoms_str.lower() != 'nan' and symptoms_str.strip():
                raw_symptom_list = [s.strip() for s in symptoms_str.split(',')]
                validated_symptoms = []
                for symptom in raw_symptom_list:
                    symptom_lower = symptom.lower()
                    if symptom_lower in SYMPTOM_OPTIONS_NORMALIZED:
                        idx = SYMPTOM_OPTIONS_NORMALIZED.index(symptom_lower)
                        validated_symptoms.append(SYMPTOM_OPTIONS[idx])
                    else:
                        validated_symptoms.append(symptom.title())

                extracted_data['symptoms_list'] = validated_symptoms
                extracted_data['symptoms'] = validated_symptoms
            else:
                extracted_data['symptoms_list'] = []
                extracted_data['symptoms'] = []
        else:
            extracted_data['symptoms_list'] = []
            extracted_data['symptoms'] = []

        if 'chas_tier' in extracted_data:
            chas_val = str(extracted_data['chas_tier']).strip()
            valid_tiers = ['Blue', 'Orange', 'Pioneer', 'Merdeka', 'None']
            if chas_val not in valid_tiers:
                extracted_data['chas_tier'] = 'None'
        else:
            extracted_data['chas_tier'] = 'None'

        # Convert all numpy/pandas types to native Python types before returning
        # This is required for Pydantic v2 serialization compatibility
        extracted_data = convert_to_native(extracted_data)

        return extracted_data

    except Exception as e:
        raise ValueError(f"Failed to parse uploaded file: {str(e)}")
