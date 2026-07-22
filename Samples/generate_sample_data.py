"""
Generate Sample Patient Data for Excel Upload Feature
======================================================

This script generates three distinct sample Excel files with realistic mock data
that matches the UCI Diabetes dataset features and the ML model's expected input columns.

The generated files represent:
1. patient_high_risk.xlsx - Patient with high readmission risk
2. patient_moderate_risk.xlsx - Patient with moderate readmission risk  
3. patient_low_risk.xlsx - Patient with low readmission risk

These files can be uploaded to the Streamlit app to pre-fill patient profiles.
"""

import pandas as pd
import json
from pathlib import Path

# Robust path resolution using the script's actual location, not CWD
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent  # /workspace (since script is in /workspace/Samples/)

# Construct all file paths using PROJECT_ROOT
FEATURE_COLUMNS_PATH = PROJECT_ROOT / "outputs" / "feature_columns.json"
OUTPUT_DIR = SCRIPT_DIR  # Save CSVs and Excel files in the Samples directory


def load_feature_columns() -> list:
    """Load expected feature columns from JSON file."""
    print(f"Script directory: {SCRIPT_DIR}")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Checking for feature columns at: {FEATURE_COLUMNS_PATH.absolute()}")
    
    if not FEATURE_COLUMNS_PATH.exists():
        print(f"Error: Feature columns file not found at {FEATURE_COLUMNS_PATH}")
        print("Please ensure the model has been trained first.")
        return []
    
    with open(FEATURE_COLUMNS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_patient_data(risk_level: str) -> dict:
    """
    Generate realistic patient data based on risk level.
    
    Args:
        risk_level: One of "high", "moderate", or "low"
    
    Returns:
        Dictionary containing patient features matching the model's expected schema
    """
    
    if risk_level == "high":
        # High risk patient profile:
        # - Multiple prior admissions
        # - High comorbidity count
        # - Elderly
        # - Many medications
        # - Insulin therapy
        return {
            'admission_type_id': 1,
            'discharge_disposition_id': 1,
            'admission_source_id': 1,
            'time_in_hospital': 7,
            'num_lab_procedures': 80,
            'num_procedures': 8,
            'num_medications': 18,
            'number_outpatient': 5,
            'number_emergency': 4,
            'number_inpatient': 5,
            'number_diagnoses': 9,
            'diabetes_diag_count': 3,
            'comorbidity_count': 8,
            'metformin_encoded': 1,
            'metformin_active': 1,
            'repaglinide_encoded': 0,
            'repaglinide_active': 0,
            'nateglinide_encoded': 0,
            'nateglinide_active': 0,
            'chlorpropamide_encoded': 0,
            'chlorpropamide_active': 0,
            'glimepiride_encoded': 1,
            'glimepiride_active': 1,
            'acetohexamide_encoded': 0,
            'acetohexamide_active': 0,
            'glipizide_encoded': 0,
            'glipizide_active': 0,
            'glyburide_encoded': 0,
            'glyburide_active': 0,
            'tolbutamide_encoded': 0,
            'tolbutamide_active': 0,
            'pioglitazone_encoded': 0,
            'pioglitazone_active': 0,
            'rosiglitazone_encoded': 0,
            'rosiglitazone_active': 0,
            'acarbose_encoded': 0,
            'acarbose_active': 0,
            'miglitol_encoded': 0,
            'miglitol_active': 0,
            'troglitazone_encoded': 0,
            'troglitazone_active': 0,
            'tolazamide_encoded': 0,
            'tolazamide_active': 0,
            'examide_encoded': 0,
            'examide_active': 0,
            'citoglipton_encoded': 0,
            'citoglipton_active': 0,
            'insulin_encoded': 1,
            'insulin_active': 1,
            'glyburide-metformin_encoded': 0,
            'glyburide-metformin_active': 0,
            'glipizide-metformin_encoded': 0,
            'glipizide-metformin_active': 0,
            'glimepiride-pioglitazone_encoded': 0,
            'glimepiride-pioglitazone_active': 0,
            'metformin-rosiglitazone_encoded': 0,
            'metformin-rosiglitazone_active': 0,
            'metformin-pioglitazone_encoded': 0,
            'metformin-pioglitazone_active': 0,
            'total_medications': 18,
            'on_insulin': 1,
            'oral_medications': 0,
            'change_encoded': 1,
            'diabetesMed_encoded': 1,
            'age_numeric': 75,
            'is_elderly': 1,
            'total_prior_admissions': 5,
            'emergency_ratio': 0.44,
            'inpatient_ratio': 0.56,
            'long_stay': 1,
            'total_procedures': 8,
            'high_lab_utilization': 1,
            'high_diagnosis_count': 1,
            'emergency_admission': 1,
            'not_home_discharge': 0,
            'er_admission': 1,
            'age_comorbidity_interaction': 75 * 8,
            'med_per_comorbidity': 18 / 8,
            'admissions_per_year': 5,
            'emerg_inpatient_combo': 9,
            'insulin_complexity': 1,
            'diabetes_med_intensity': 2,
        }
    
    elif risk_level == "moderate":
        # Moderate risk patient profile:
        # TASK 1: Strictly defined per requirements
        # - age_numeric=55, age_group="[50-60)"
        # - time_in_hospital=4, num_lab_procedures=45
        # - prior_admissions=2, comorbidity_count=4
        # - num_medications=8, chas_tier="Orange"
        # - symptoms="Fatigue, Frequent urination"
        return {
            'admission_type_id': 1,
            'discharge_disposition_id': 1,
            'admission_source_id': 1,
            'time_in_hospital': 4,
            'num_lab_procedures': 45,
            'num_procedures': 3,
            'num_medications': 8,
            'number_outpatient': 2,
            'number_emergency': 1,
            'number_inpatient': 2,
            'number_diagnoses': 5,
            'diabetes_diag_count': 2,
            'comorbidity_count': 4,
            'metformin_encoded': 1,
            'metformin_active': 1,
            'repaglinide_encoded': 0,
            'repaglinide_active': 0,
            'nateglinide_encoded': 0,
            'nateglinide_active': 0,
            'chlorpropamide_encoded': 0,
            'chlorpropamide_active': 0,
            'glimepiride_encoded': 0,
            'glimepiride_active': 0,
            'acetohexamide_encoded': 0,
            'acetohexamide_active': 0,
            'glipizide_encoded': 0,
            'glipizide_active': 0,
            'glyburide_encoded': 0,
            'glyburide_active': 0,
            'tolbutamide_encoded': 0,
            'tolbutamide_active': 0,
            'pioglitazone_encoded': 0,
            'pioglitazone_active': 0,
            'rosiglitazone_encoded': 0,
            'rosiglitazone_active': 0,
            'acarbose_encoded': 0,
            'acarbose_active': 0,
            'miglitol_encoded': 0,
            'miglitol_active': 0,
            'troglitazone_encoded': 0,
            'troglitazone_active': 0,
            'tolazamide_encoded': 0,
            'tolazamide_active': 0,
            'examide_encoded': 0,
            'examide_active': 0,
            'citoglipton_encoded': 0,
            'citoglipton_active': 0,
            'insulin_encoded': 0,
            'insulin_active': 0,
            'glyburide-metformin_encoded': 0,
            'glyburide-metformin_active': 0,
            'glipizide-metformin_encoded': 0,
            'glipizide-metformin_active': 0,
            'glimepiride-pioglitazone_encoded': 0,
            'glimepiride-pioglitazone_active': 0,
            'metformin-rosiglitazone_encoded': 0,
            'metformin-rosiglitazone_active': 0,
            'metformin-pioglitazone_encoded': 0,
            'metformin-pioglitazone_active': 0,
            'total_medications': 8,
            'on_insulin': 0,
            'oral_medications': 1,
            'change_encoded': 0,
            'diabetesMed_encoded': 1,
            'age_numeric': 55,
            'is_elderly': 0,
            'total_prior_admissions': 2,
            'emergency_ratio': 0.33,
            'inpatient_ratio': 0.40,
            'long_stay': 0,
            'total_procedures': 3,
            'high_lab_utilization': 0,
            'high_diagnosis_count': 0,
            'emergency_admission': 0,
            'not_home_discharge': 0,
            'er_admission': 0,
            'age_comorbidity_interaction': 55 * 4,
            'med_per_comorbidity': 8 / 4,
            'admissions_per_year': 2,
            'emerg_inpatient_combo': 3,
            'insulin_complexity': 0,
            'diabetes_med_intensity': 1,
        }
    
    else:  # low risk
        # Low risk patient profile:
        # TASK 1: Strictly defined per requirements
        # - age_numeric=45, age_group="[40-50)"
        # - time_in_hospital=2, num_lab_procedures=15
        # - prior_admissions=0, comorbidity_count=1
        # - num_medications=2, chas_tier="None"
        # - symptoms="Mild thirst"
        return {
            'admission_type_id': 1,  # Elective admission
            'discharge_disposition_id': 1,  # Discharged to home
            'admission_source_id': 7,  # Most common source (not ER)
            'time_in_hospital': 2,
            'num_lab_procedures': 15,
            'num_procedures': 0,
            'num_medications': 2,
            'number_outpatient': 0,
            'number_emergency': 0,
            'number_inpatient': 0,
            'number_diagnoses': 2,
            'diabetes_diag_count': 1,
            'comorbidity_count': 1,
            'metformin_encoded': 1,
            'metformin_active': 1,
            'repaglinide_encoded': 0,
            'repaglinide_active': 0,
            'nateglinide_encoded': 0,
            'nateglinide_active': 0,
            'chlorpropamide_encoded': 0,
            'chlorpropamide_active': 0,
            'glimepiride_encoded': 0,
            'glimepiride_active': 0,
            'acetohexamide_encoded': 0,
            'acetohexamide_active': 0,
            'glipizide_encoded': 0,
            'glipizide_active': 0,
            'glyburide_encoded': 0,
            'glyburide_active': 0,
            'tolbutamide_encoded': 0,
            'tolbutamide_active': 0,
            'pioglitazone_encoded': 0,
            'pioglitazone_active': 0,
            'rosiglitazone_encoded': 0,
            'rosiglitazone_active': 0,
            'acarbose_encoded': 0,
            'acarbose_active': 0,
            'miglitol_encoded': 0,
            'miglitol_active': 0,
            'troglitazone_encoded': 0,
            'troglitazone_active': 0,
            'tolazamide_encoded': 0,
            'tolazamide_active': 0,
            'examide_encoded': 0,
            'examide_active': 0,
            'citoglipton_encoded': 0,
            'citoglipton_active': 0,
            'insulin_encoded': 0,
            'insulin_active': 0,
            'glyburide-metformin_encoded': 0,
            'glyburide-metformin_active': 0,
            'glipizide-metformin_encoded': 0,
            'glipizide-metformin_active': 0,
            'glimepiride-pioglitazone_encoded': 0,
            'glimepiride-pioglitazone_active': 0,
            'metformin-rosiglitazone_encoded': 0,
            'metformin-rosiglitazone_active': 0,
            'metformin-pioglitazone_encoded': 0,
            'metformin-pioglitazone_active': 0,
            'total_medications': 2,
            'on_insulin': 0,
            'oral_medications': 1,
            'change_encoded': 0,
            'diabetesMed_encoded': 1,
            'age_numeric': 45,
            'is_elderly': 0,
            'total_prior_admissions': 0,
            'emergency_ratio': 0.0,
            'inpatient_ratio': 0.0,
            'long_stay': 0,
            'total_procedures': 0,
            'high_lab_utilization': 0,
            'high_diagnosis_count': 0,
            'emergency_admission': 0,
            'not_home_discharge': 0,
            'er_admission': 0,
            'age_comorbidity_interaction': 45 * 1,
            'med_per_comorbidity': 2 / 1,
            'admissions_per_year': 0,
            'emerg_inpatient_combo': 0,
            'insulin_complexity': 0,
            'diabetes_med_intensity': 1 * 2,
        }


def create_simplified_patient_row(patient_data: dict, risk_level: str) -> dict:
    """
    Create a simplified version of patient data for Excel upload.
    This includes only the key features that doctors would typically have in discharge summaries.
    
    The app's parse_uploaded_file function will map these to the full feature set using
    the explicit CSV_TO_MODEL_MAPPING dictionary defined in app.py.
    
    Updated to include a 'symptoms' column with realistic diabetes symptoms based on risk level.
    Updated to include a 'chas_tier' column with Singapore healthcare context values.
    
    TASK 3: Column names now EXACTLY match the keys in CSV_TO_MODEL_MAPPING dictionary
    to ensure perfect compatibility with the app's CSV parsing logic.
    """
    # Define realistic symptom profiles based on risk level
    # TASK 1: Strictly separated profiles per requirements
    symptom_profiles = {
        "high": "Fatigue, Frequent urination, Blurred vision, Slow-healing sores, Tingling in hands/feet, Excessive thirst",
        "moderate": "Fatigue, Frequent urination",
        "low": "Mild thirst"
    }
    
    # Define CHAS Tier assignments based on patient profile (Singapore healthcare context)
    # TASK 1: Strictly assigned per requirements
    # High risk (elderly, age 75): Pioneer tier
    # Moderate risk (middle-aged, age 55): Orange tier
    # Low risk (younger, age 45): None tier
    chas_tier_profiles = {
        "high": "Pioneer",      # Elderly patients (age 75) get Pioneer tier
        "moderate": "Orange",   # Middle-aged patients (age 55) get Orange tier
        "low": "None"           # Younger patients (age 45) get None tier
    }
    
    # Simplified features that are commonly available in discharge summaries
    # Column names MUST exactly match CSV_TO_MODEL_MAPPING keys in app.py
    simplified = {
        'patient_id': f"PATIENT_{risk_level.upper()}_001",
        'risk_profile': f"{risk_level.capitalize()} Risk Patient",
        # Use exact column names from CSV_TO_MODEL_MAPPING
        'prior_admissions': patient_data['number_inpatient'],  # Maps to total_prior_admissions + sets number_inpatient
        'comorbidity_count': patient_data['comorbidity_count'],
        'age_numeric': patient_data['age_numeric'],
        'num_medications': patient_data['num_medications'],  # Maps to total_medications
        'discharge_diagnosis': 250.01,  # Diabetes mellitus type 2 (user-facing field, not mapped to model)
        'high_risk_flag': 1 if risk_level == "high" else 0,
        'time_in_hospital': patient_data['time_in_hospital'],
        'num_lab_procedures': patient_data['num_lab_procedures'],
        'num_procedures': patient_data['num_procedures'],
        'number_outpatient': patient_data['number_outpatient'],
        'number_emergency': patient_data['number_emergency'],
        'number_inpatient': patient_data['number_inpatient'],
        'number_diagnoses': patient_data['number_diagnoses'],
        'diabetes_diag_count': patient_data['diabetes_diag_count'],
        'metformin_encoded': patient_data['metformin_encoded'],
        'insulin_encoded': patient_data['insulin_encoded'],
        'on_insulin': patient_data['on_insulin'],
        'change_encoded': patient_data['change_encoded'],
        'diabetesMed_encoded': patient_data['diabetesMed_encoded'],
        'symptoms': symptom_profiles.get(risk_level, "None"),  # Add symptoms column
        'chas_tier': chas_tier_profiles.get(risk_level, "None"),  # Add CHAS Tier column for Gen AI context
    }
    return simplified


def main():
    """Generate sample Excel files for testing the upload feature."""
    
    print("=" * 60)
    print("GENERATING SAMPLE PATIENT DATA FILES")
    print("=" * 60)
    
    # Load feature columns to validate our data structure
    feature_columns = load_feature_columns()
    if not feature_columns:
        print("Cannot proceed without feature columns. Exiting.")
        return
    
    print(f"\nLoaded {len(feature_columns)} expected feature columns")
    
    # Generate data for each risk level
    risk_levels = ["high", "moderate", "low"]
    
    for risk_level in risk_levels:
        print(f"\nGenerating {risk_level} risk patient data...")
        
        # Generate full patient data matching model schema
        patient_data = generate_patient_data(risk_level)
        
        # Validate all required features are present
        missing_features = set(feature_columns) - set(patient_data.keys())
        if missing_features:
            print(f"Warning: Missing features for {risk_level} risk: {missing_features}")
        
        # Create simplified version for Excel upload (what doctors would provide)
        simplified_data = create_simplified_patient_row(patient_data, risk_level)
        
        # Create DataFrame
        df_full = pd.DataFrame([patient_data])
        df_simplified = pd.DataFrame([simplified_data])
        
        # Save full data (for reference/testing) - use OUTPUT_DIR for robust path
        full_filename = OUTPUT_DIR / f"patient_{risk_level}_risk_full.xlsx"
        df_full.to_excel(full_filename, index=False)
        print(f"  Created: {full_filename} (full feature set)")
        
        # Save simplified data (for actual upload testing) - use OUTPUT_DIR for robust path
        simplified_filename = OUTPUT_DIR / f"patient_{risk_level}_risk.xlsx"
        df_simplified.to_excel(simplified_filename, index=False)
        print(f"  Created: {simplified_filename} (simplified for upload)")
        
        # Also create CSV versions - use OUTPUT_DIR for robust path
        csv_filename = OUTPUT_DIR / f"patient_{risk_level}_risk.csv"
        df_simplified.to_csv(csv_filename, index=False)
        print(f"  Created: {csv_filename} (CSV format)")
    
    print("\n" + "=" * 60)
    print("SAMPLE DATA GENERATION COMPLETE")
    print("=" * 60)
    print("\nGenerated files:")
    print("  - patient_high_risk.xlsx (simplified for upload)")
    print("  - patient_moderate_risk.xlsx (simplified for upload)")
    print("  - patient_low_risk.xlsx (simplified for upload)")
    print("  - patient_high_risk.csv (simplified for upload)")
    print("  - patient_moderate_risk.csv (simplified for upload)")
    print("  - patient_low_risk.csv (simplified for upload)")
    print("  - patient_*_risk_full.xlsx (full feature sets for reference)")
    print("\nUpload the simplified files (without '_full' suffix) to test the Excel upload feature.")


if __name__ == "__main__":
    main()
