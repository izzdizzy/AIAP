import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file at the very top
load_dotenv()

# Get API key from environment variable
api_key = os.getenv("GEMINI_API_KEY")

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

from model import ReadmissionPredictor
from gen_ai import CareNavigationAssistant


# =============================================================================
# FEATURE DISPLAY NAMES - HUMAN-READABLE LABELS FOR PATIENTS
# =============================================================================

FEATURE_DISPLAY_NAMES = {
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
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Diabetes Care Navigation Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# INITIALIZATION
# =============================================================================

@st.cache_resource
def load_model():
    """Load the ML model once and cache it."""
    try:
        predictor = ReadmissionPredictor()
        return predictor
    except FileNotFoundError as e:
        st.error(f"Model not found. Please run train_model.py first. Error: {e}")
        return None


@st.cache_resource
def load_assistant():
    """Load the Gen AI assistant once and cache it."""
    if not api_key:
        st.warning("GEMINI_API_KEY not found in environment. Gen AI features will be unavailable.")
        return None
    try:
        assistant = CareNavigationAssistant(api_key=api_key)
        return assistant
    except Exception as e:
        st.error(f"Failed to initialize Gen AI assistant: {e}")
        return None


# Initialize session state for chat history and form data
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_risk_score' not in st.session_state:
    st.session_state.current_risk_score = None
if 'current_symptoms' not in st.session_state:
    st.session_state.current_symptoms = []
if 'form_initialized' not in st.session_state:
    st.session_state.form_initialized = False
if 'parsed_patient_data' not in st.session_state:
    st.session_state.parsed_patient_data = {}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_feature_columns() -> list:
    """Load expected feature columns from JSON file."""
    try:
        with open('outputs/feature_columns.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Failed to load feature columns: {e}")
        return []


def parse_uploaded_file(uploaded_file) -> Optional[Dict[str, Any]]:
    """
    Parse uploaded Excel or CSV file and extract patient features.
    
    Returns a dictionary of feature values that can be used to pre-fill the form.
    """
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file format. Please upload .csv or .xlsx files.")
            return None
        
        if df.empty:
            st.error("Uploaded file is empty.")
            return None
        
        # Get the first row as patient data
        patient_row = df.iloc[0]
        
        # Map common column names to our expected features
        # This handles variations in column naming
        feature_mapping = {
            'prior_admissions': ['prior_admissions', 'num_prior_admissions', 'previous_admissions', 'admissions'],
            'comorbidity_count': ['comorbidity_count', 'comorbidities', 'num_comorbidities'],
            'age_numeric': ['age_numeric', 'age', 'patient_age'],
            'num_medications': ['num_medications', 'medication_count', 'medications', 'total_medications'],
            'discharge_diagnosis': ['discharge_diagnosis', 'primary_diagnosis', 'diagnosis_code'],
            'high_risk_flag': ['high_risk_flag', 'high_risk', 'risk_flag'],
            'time_in_hospital': ['time_in_hospital', 'hospital_days', 'length_of_stay'],
            'num_lab_procedures': ['num_lab_procedures', 'lab_procedures', 'lab_tests'],
            'num_procedures': ['num_procedures', 'procedures'],
            'number_outpatient': ['number_outpatient', 'outpatient_visits'],
            'number_emergency': ['number_emergency', 'emergency_visits'],
            'number_inpatient': ['number_inpatient', 'inpatient_visits'],
            'number_diagnoses': ['number_diagnoses', 'diagnoses_count'],
            'diabetes_diag_count': ['diabetes_diag_count', 'diabetes_diagnoses'],
            'metformin_encoded': ['metformin_encoded', 'metformin'],
            'insulin_encoded': ['insulin_encoded', 'insulin'],
            'on_insulin': ['on_insulin', 'insulin_therapy'],
            'change_encoded': ['change_encoded', 'medication_change'],
            'diabetesMed_encoded': ['diabetesMed_encoded', 'diabetes_medication'],
            'symptoms': ['symptoms', 'patient_symptoms', 'reported_symptoms'],
        }
        
        extracted_data = {}
        
        for target_feature, possible_names in feature_mapping.items():
            for col_name in possible_names:
                if col_name in df.columns:
                    value = patient_row[col_name]
                    # Handle NaN values
                    if pd.isna(value):
                        value = 0
                    extracted_data[target_feature] = value
                    break
        
        # Special handling for age group conversion
        if 'age_numeric' in extracted_data:
            age = extracted_data['age_numeric']
            # Convert numeric age to age group index for the selectbox
            if age < 10:
                extracted_data['age_group_display'] = "0-10"
            elif age < 20:
                extracted_data['age_group_display'] = "10-20"
            elif age < 30:
                extracted_data['age_group_display'] = "20-30"
            elif age < 40:
                extracted_data['age_group_display'] = "30-40"
            elif age < 50:
                extracted_data['age_group_display'] = "40-50"
            elif age < 60:
                extracted_data['age_group_display'] = "50-60"
            elif age < 70:
                extracted_data['age_group_display'] = "60-70"
            elif age < 80:
                extracted_data['age_group_display'] = "70-80"
            elif age < 90:
                extracted_data['age_group_display'] = "80-90"
            else:
                extracted_data['age_group_display'] = "90-100"
        
        # Handle high_risk_flag conversion
        if 'high_risk_flag' in extracted_data:
            flag_val = extracted_data['high_risk_flag']
            extracted_data['high_risk_display'] = "Yes" if flag_val == 1 or (isinstance(flag_val, str) and flag_val.lower() == 'yes') else "No"
        
        # Handle symptoms column - split by comma and map to symptom options
        if 'symptoms' in extracted_data:
            symptoms_str = str(extracted_data['symptoms'])
            if symptoms_str and symptoms_str.lower() != 'nan' and symptoms_str.strip():
                # Split by comma and strip whitespace to get individual symptoms
                raw_symptom_list = [s.strip() for s in symptoms_str.split(',')]
                
                # Define the valid symptom options that match the multiselect widget
                # These must exactly match the options defined in app.py symptom_options list
                # Note: We use lower() for case-insensitive comparison since .title() 
                # converts "frequent urination" to "Frequent Urination" (not "Frequent urination")
                valid_symptom_options_lower = [
                    "fatigue", "frequent urination", "excessive thirst",
                    "blurred vision", "slow-healing sores", "tingling in hands/feet",
                    "increased hunger", "unexplained weight loss", "dry skin",
                    "frequent infections", "irritability", "nausea",
                    "headache", "dizziness", "shortness of breath",
                    "chest pain", "swelling in legs", "vision changes"
                ]
                
                # Original symptom options for proper display (matching multiselect widget)
                valid_symptom_options_display = [
                    "Fatigue", "Frequent urination", "Excessive thirst",
                    "Blurred vision", "Slow-healing sores", "Tingling in hands/feet",
                    "Increased hunger", "Unexplained weight loss", "Dry skin",
                    "Frequent infections", "Irritability", "Nausea",
                    "Headache", "Dizziness", "Shortness of breath",
                    "Chest pain", "Swelling in legs", "Vision changes"
                ]
                
                # Filter to only include symptoms that match the available options
                # Use lower() for case-insensitive matching, then map back to display format
                valid_symptoms_list = []
                for symptom in raw_symptom_list:
                    if symptom:  # Skip empty strings
                        symptom_lower = symptom.lower()
                        if symptom_lower in valid_symptom_options_lower:
                            # Find the index and get the properly formatted display version
                            idx = valid_symptom_options_lower.index(symptom_lower)
                            valid_symptoms_list.append(valid_symptom_options_display[idx])
                
                extracted_data['symptoms_list'] = valid_symptoms_list
        
        return extracted_data
        
    except Exception as e:
        st.error(f"Error parsing file: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None


# =============================================================================
# SIDEBAR - PATIENT INFORMATION
# =============================================================================

with st.sidebar:
    st.header("Patient Information")
    st.markdown("---")
    
    # Excel/CSV File Upload Section
    st.subheader("📁 Upload Discharge Data")
    uploaded_file = st.file_uploader(
        "Upload patient discharge Excel/CSV file",
        type=['xlsx', 'csv'],
        help="Upload an Excel or CSV file containing patient baseline data from hospital discharge"
    )
    
    if uploaded_file is not None:
        parsed_data = parse_uploaded_file(uploaded_file)
        if parsed_data:
            # Store parsed data in session state - widgets will read from this during initialization
            st.session_state['parsed_patient_data'] = parsed_data
            
            st.success(f"✅ Successfully loaded data from {uploaded_file.name}")
            
            # Show preview with human-readable labels
            with st.expander("View loaded data"):
                # Display with friendly names where available
                friendly_data = {}
                for key, value in parsed_data.items():
                    display_name = FEATURE_DISPLAY_NAMES.get(key, key)
                    friendly_data[display_name] = value
                st.json(friendly_data)
    
    st.markdown("---")
    st.subheader("Clinical Features")
    
    # Initialize session state keys for all form widgets BEFORE the widgets are declared
    # This follows Streamlit's best practices to avoid widget warnings
    if "prior_admissions_input" not in st.session_state:
        st.session_state.prior_admissions_input = 1
    if "comorbidity_count_input" not in st.session_state:
        st.session_state.comorbidity_count_input = 3
    if "age_group_input" not in st.session_state:
        st.session_state.age_group_input = 6  # Default to 60-70
    if "medication_count_input" not in st.session_state:
        st.session_state.medication_count_input = 5
    if "discharge_diagnosis_input" not in st.session_state:
        st.session_state.discharge_diagnosis_input = "250.01"
    if "high_risk_flag_input" not in st.session_state:
        st.session_state.high_risk_flag_input = 0
    if "symptoms_multiselect" not in st.session_state:
        st.session_state.symptoms_multiselect = []
    
    # Handle uploaded file data - update session state before widgets render
    parsed_data = st.session_state.get('parsed_patient_data', {})
    if parsed_data:
        if 'prior_admissions' in parsed_data:
            st.session_state.prior_admissions_input = int(parsed_data['prior_admissions'])
        if 'comorbidity_count' in parsed_data:
            st.session_state.comorbidity_count_input = int(parsed_data['comorbidity_count'])
        if 'num_medications' in parsed_data:
            st.session_state.medication_count_input = int(parsed_data['num_medications'])
        if 'discharge_diagnosis' in parsed_data:
            st.session_state.discharge_diagnosis_input = str(parsed_data['discharge_diagnosis'])
        if 'age_group_display' in parsed_data:
            age_options = ["0-10", "10-20", "20-30", "30-40", "40-50", "50-60", "60-70", "70-80", "80-90", "90-100"]
            if parsed_data['age_group_display'] in age_options:
                st.session_state.age_group_input = age_options.index(parsed_data['age_group_display'])
        if 'high_risk_display' in parsed_data:
            st.session_state.high_risk_flag_input = 1 if parsed_data['high_risk_display'] == "Yes" else 0
        # Handle symptoms from uploaded file
        if 'symptoms_list' in parsed_data:
            st.session_state.symptoms_multiselect = parsed_data['symptoms_list']
    
    # 6 Clinical Features from the dataset - using human-readable labels
    # NOTE: Do NOT pass value=st.session_state[...] - let Streamlit manage widget state via key
    prior_admissions = st.number_input(
        FEATURE_DISPLAY_NAMES.get('prior_admissions', "Prior Admissions (last 12 months)"),
        min_value=0,
        max_value=50,
        key="prior_admissions_input",
        help="Number of hospital admissions in the past 12 months"
    )
    
    comorbidity_count = st.number_input(
        FEATURE_DISPLAY_NAMES.get('comorbidity_count', "Comorbidity Count"),
        min_value=0,
        max_value=20,
        key="comorbidity_count_input",
        help="Number of co-existing medical conditions"
    )
    
    age_group = st.selectbox(
        "Age Group",
        options=["0-10", "10-20", "20-30", "30-40", "40-50", "50-60", "60-70", "70-80", "80-90", "90-100"],
        key="age_group_input",
        help="Patient age group (mapped to dataset encoding)"
    )
    
    medication_count = st.number_input(
        FEATURE_DISPLAY_NAMES.get('num_medications', "Medication Count"),
        min_value=0,
        max_value=50,
        key="medication_count_input",
        help="Number of medications prescribed"
    )
    
    discharge_diagnosis = st.text_input(
        FEATURE_DISPLAY_NAMES.get('discharge_diagnosis', "Discharge Diagnosis (ICD Code)"),
        key="discharge_diagnosis_input",
        help="Primary diagnosis code at discharge (e.g., 250.01 for diabetes)"
    )
    
    high_risk_flag = st.selectbox(
        FEATURE_DISPLAY_NAMES.get('high_risk_flag', "High Risk Flag"),
        options=["No", "Yes"],
        key="high_risk_flag_input",
        help="Whether patient is flagged as high risk"
    )
    
    st.markdown("---")
    st.subheader("Reported Symptoms")
    st.caption("Select symptoms currently experienced")
    
    symptom_options = [
        "Fatigue", "Frequent urination", "Excessive thirst",
        "Blurred vision", "Slow-healing sores", "Tingling in hands/feet",
        "Increased hunger", "Unexplained weight loss", "Dry skin",
        "Frequent infections", "Irritability", "Nausea",
        "Headache", "Dizziness", "Shortness of breath",
        "Chest pain", "Swelling in legs", "Vision changes"
    ]
    
    selected_symptoms = st.multiselect(
        "Current Symptoms",
        options=symptom_options,
        key="symptoms_multiselect",
        help="Select all symptoms that apply"
    )
    
    st.session_state.current_symptoms = selected_symptoms


# =============================================================================
# MAIN APP - TWO TABS
# =============================================================================

st.title("🏥 Diabetes Care Navigation Assistant")
st.markdown("""
This application combines **ML-based risk prediction** with **Gen AI-powered care navigation** 
to help diabetic patients manage their health after hospital discharge.
""")

tab1, tab2 = st.tabs(["📊 Patient Risk Assessment", "💬 Care Navigation"])

# Load model and assistant
predictor = load_model()
assistant = load_assistant()


# =============================================================================
# TAB 1: PATIENT RISK ASSESSMENT
# =============================================================================

with tab1:
    st.header("Hospital Readmission Risk Assessment")
    
    if predictor is None:
        st.error("ML Model not available. Please ensure the model has been trained.")
        st.stop()
    
    # Load expected feature columns from JSON file
    expected_features = load_feature_columns()
    
    # Prepare input data
    age_mapping = {
        "0-10": 0, "10-20": 10, "20-30": 20, "30-40": 30, "40-50": 40,
        "50-60": 50, "60-70": 60, "70-80": 70, "80-90": 80, "90-100": 90
    }
    age_encoded = age_mapping.get(age_group, 60)
    
    # Calculate interaction features (as done in training)
    age_comorbidity_interaction = age_encoded * comorbidity_count
    medication_comorbidity_interaction = medication_count * comorbidity_count
    admissions_comorbidity_interaction = prior_admissions * comorbidity_count
    age_medication_interaction = age_encoded * medication_count
    
    # Convert diagnosis to float
    try:
        diagnosis_float = float(discharge_diagnosis)
    except ValueError:
        diagnosis_float = 250.01  # Default diabetes code
    
    # Build patient data dictionary with ALL expected features from feature_columns.json
    # This ensures the DataFrame matches exactly what the model expects
    patient_data = {
        'admission_type_id': 1,  # Default value - elective admission
        'discharge_disposition_id': 1,  # Default - discharged to home
        'admission_source_id': 1,  # Default - physician referral
        'time_in_hospital': 5,  # Default - 5 days
        'num_lab_procedures': 50,  # Default average
        'num_procedures': 5,  # Default
        'num_medications': medication_count,  # From user input
        'number_outpatient': 0,  # Default
        'number_emergency': prior_admissions // 2,  # Estimate based on prior admissions
        'number_inpatient': prior_admissions,  # From user input
        'number_diagnoses': comorbidity_count + 1,  # At least primary diagnosis
        'diabetes_diag_count': 1,  # At least 1 diabetes diagnosis
        'comorbidity_count': comorbidity_count,  # From user input
        'metformin_encoded': 1,  # Default - prescribed
        'metformin_active': 1,  # Default - active
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
        'insulin_encoded': 1 if high_risk_flag == "Yes" else 0,
        'insulin_active': 1 if high_risk_flag == "Yes" else 0,
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
        'total_medications': medication_count,
        'on_insulin': 1 if high_risk_flag == "Yes" else 0,
        'oral_medications': 1 if high_risk_flag == "No" else 0,
        'change_encoded': 0,  # Default - no change
        'diabetesMed_encoded': 1,  # Default - on diabetes meds
        'age_numeric': age_encoded,  # From user input
        'is_elderly': 1 if age_encoded >= 65 else 0,
        'total_prior_admissions': prior_admissions,
        'emergency_ratio': 0.3,  # Default estimate
        'inpatient_ratio': 0.7,  # Default estimate
        'long_stay': 0,  # Default - not long stay
        'total_procedures': 5,  # Default
        'high_lab_utilization': 0,  # Default
        'high_diagnosis_count': 1 if comorbidity_count > 5 else 0,
        'emergency_admission': 0,  # Default
        'not_home_discharge': 0,  # Default - discharged home
        'er_admission': 0,  # Default
        'age_comorbidity_interaction': age_comorbidity_interaction,
        'med_per_comorbidity': medication_count / max(comorbidity_count, 1),
        'admissions_per_year': prior_admissions,
        'emerg_inpatient_combo': prior_admissions + (prior_admissions // 2),
        'insulin_complexity': 1 if high_risk_flag == "Yes" else 0,
        'diabetes_med_intensity': 1,  # Default
    }
    
    # Display input summary with human-readable labels
    st.markdown("### 📋 Patient Data Summary")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Clinical Input Values")
        # Create a human-readable summary instead of raw JSON
        summary_data = {
            FEATURE_DISPLAY_NAMES.get('prior_admissions', 'Prior Admissions'): prior_admissions,
            FEATURE_DISPLAY_NAMES.get('comorbidity_count', 'Comorbidity Count'): comorbidity_count,
            "Age Group": age_group,
            FEATURE_DISPLAY_NAMES.get('num_medications', 'Medication Count'): medication_count,
            FEATURE_DISPLAY_NAMES.get('discharge_diagnosis', 'Discharge Diagnosis'): discharge_diagnosis,
            FEATURE_DISPLAY_NAMES.get('high_risk_flag', 'High Risk Flag'): high_risk_flag,
        }
        st.json(summary_data)
    
    with col2:
        st.subheader("Reported Symptoms")
        if selected_symptoms:
            symptoms_text = ", ".join(selected_symptoms)
            st.info(f"💬 {symptoms_text}")
        else:
            st.caption("No symptoms reported")
    
    st.markdown("---")
    
    # Generate prediction button
    if st.button("Calculate Risk Score", type="primary", use_container_width=True):
        with st.spinner("Analyzing patient data..."):
            try:
                # Get prediction
                result = predictor.predict(patient_data, return_shap=True)
                
                # Store in session state for Tab 2
                st.session_state.current_risk_score = result['risk_score']
                
                # Display results
                st.subheader("Patient Risk Assessment")
                
                # Clinical severity score display - reframed from probability to relative severity
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Convert risk score to 0-100 Clinical Severity Scale
                    severity_score = result['risk_score'] * 100
                    st.metric(
                        "Clinical Severity Score",
                        f"{severity_score:.0f}/100",
                        delta=None
                    )
                
                with col2:
                    # Map internal risk categories to clinical urgency levels
                    urgency_mapping = {
                        "Low": "Routine Monitoring",
                        "Moderate": "Increased Surveillance",
                        "High": "Immediate Intervention"
                    }
                    urgency_level = urgency_mapping.get(result['risk_category'], result['risk_category'])
                    color_map = {"Low": "green", "Moderate": "orange", "High": "red"}
                    st.metric(
                        "Urgency Level",
                        urgency_level,
                        delta=None,
                        delta_color="normal"
                    )
                
                with col3:
                    st.metric(
                        "Prediction",
                        result['prediction_label'],
                        delta=None
                    )
                
                # Clinical philosophy explanation - critical for user understanding
                st.info(
                    "💡 **Clinical Philosophy:** This model is optimized for 100% Recall to ensure no at-risk patient is missed. "
                    "Your score reflects clinical severity and urgency for intervention relative to the patient population, "
                    "rather than an absolute mathematical probability."
                )
                
                # Updated risk interpretation with clinical urgency framing
                st.markdown("### Clinical Interpretation")
                
                if result['risk_category'] == "Low":
                    st.success("""
                    **Routine Monitoring**: Patient shows low clinical severity relative to the population. 
                    Continue current management plan with standard follow-up schedule.
                    Maintain regular appointments with your healthcare provider and adhere to prescribed medications.
                    """)
                elif result['risk_category'] == "Moderate":
                    st.warning("""
                    **Increased Surveillance**: Patient shows moderate clinical severity. Enhanced monitoring recommended.
                    Consider scheduling an earlier follow-up appointment to review care plan and medication adherence.
                    Pay close attention to any changes in symptoms or condition.
                    """)
                else:
                    st.error("""
                    **Immediate Intervention**: Patient shows high clinical severity requiring urgent attention.
                    Strongly recommend immediate consultation with your healthcare provider to assess potential complications
                    and adjust treatment plan. Do not delay seeking medical advice.
                    """)
                
                # SHAP Analysis with human-readable feature names and high-contrast visualization
                if 'feature_importance' in result and result['feature_importance']:
                    st.markdown("### 🔍 Key Risk Factors (SHAP Analysis)")
                    
                    importance_df = pd.DataFrame(result['feature_importance'])
                    
                    # Add human-readable display names to the dataframe
                    importance_df['display_name'] = importance_df['feature'].apply(
                        lambda x: FEATURE_DISPLAY_NAMES.get(x, x)
                    )
                    
                    # Create a high-contrast matplotlib bar chart for SHAP values
                    import matplotlib.pyplot as plt
                    
                    # Set up the figure with explicit white background and dark text
                    fig, ax = plt.subplots(figsize=(10, 6), facecolor='white')
                    ax.set_facecolor('white')
                    
                    # Get top 10 features by absolute importance
                    top_n = min(10, len(importance_df))
                    top_features = importance_df.nlargest(top_n, 'importance')
                    
                    # Create color palette: deep red for positive (increasing risk), deep blue for negative (decreasing risk)
                    colors = []
                    for _, row in top_features.iterrows():
                        shap_val = row.get('shap_value', 0)
                        if shap_val >= 0:
                            colors.append('#D32F2F')  # Deep red for positive/risk-increasing
                        else:
                            colors.append('#1976D2')  # Deep blue for negative/risk-decreasing
                    
                    # Create horizontal bar chart with high contrast
                    y_pos = range(len(top_features))
                    ax.barh(y_pos, top_features['importance'], color=colors, edgecolor='black', linewidth=0.5)
                    
                    # Set labels with dark gray/black color for readability
                    ax.set_yticks(y_pos)
                    ax.set_yticklabels(top_features['display_name'], fontsize=11, color='#212121')
                    ax.set_xlabel('SHAP Importance Value', fontsize=12, color='#212121', fontweight='bold')
                    ax.set_title('Key Risk Factors Contributing to Readmission Risk', fontsize=14, color='#212121', fontweight='bold')
                    
                    # Invert y-axis to show highest importance at top
                    ax.invert_yaxis()
                    
                    # Add grid lines for better readability
                    ax.grid(axis='x', linestyle='--', alpha=0.3, color='#424242')
                    
                    # Ensure tight layout
                    plt.tight_layout()
                    
                    # Display the plot in Streamlit
                    st.pyplot(fig, bbox_inches='tight')
                    
                    # Also display text summary
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Top Contributing Factors:**")
                        for i, (_, row) in enumerate(top_features.head(5).iterrows()):
                            # Color-code based on risk direction - using black background as specified
                            if row.get('shap_value', 0) >= 0:
                                st.markdown(
                                    f"""
                                    <div style="background-color: #000000; color: #FFFFFF; padding: 8px; margin: 5px 0; border-radius: 5px; border-left: 4px solid #D32F2F;">
                                        <strong>{row['display_name']}</strong><br/>
                                        <small style="color: #CCCCCC;">({row['feature']})</small>: {row['importance']:.4f}
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                            else:
                                st.markdown(
                                    f"""
                                    <div style="background-color: #000000; color: #FFFFFF; padding: 8px; margin: 5px 0; border-radius: 5px; border-left: 4px solid #1976D2;">
                                        <strong>{row['display_name']}</strong><br/>
                                        <small style="color: #CCCCCC;">({row['feature']})</small>: {row['importance']:.4f}
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                    
                    with col2:
                        st.write("**Positive/Negative Impact:**")
                        positive = [f for f in result['feature_importance'] if f.get('shap_value', 0) > 0][:3]
                        negative = [f for f in result['feature_importance'] if f.get('shap_value', 0) < 0][:3]
                        
                        if positive:
                            st.info("**Factors Increasing Risk:**")
                            for f in positive:
                                display_name = FEATURE_DISPLAY_NAMES.get(f['feature'], f['feature'])
                                st.write(f"• {display_name}")
                        
                        if negative:
                            st.success("**Factors Decreasing Risk:**")
                            for f in negative:
                                display_name = FEATURE_DISPLAY_NAMES.get(f['feature'], f['feature'])
                                st.write(f"• {display_name}")
                
                st.success("✅ Risk assessment complete! Switch to the **Care Navigation** tab for personalized guidance.")
                
            except Exception as e:
                st.error(f"Error generating prediction: {str(e)}")
                import traceback
                st.code(traceback.format_exc())


# =============================================================================
# TAB 2: CARE NAVIGATION (CHAT INTERFACE)
# =============================================================================

with tab2:
    st.header("AI Care Navigation Assistant")
    
    if assistant is None:
        st.warning("""
        ⚠️ **Gen AI Assistant Unavailable**
        
        The Gemini API key is not configured. To enable this feature:
        1. Obtain an API key from https://makersuite.google.com/app/apikey
        2. Set the GEMINI_API_KEY environment variable or create a .env file
        3. Restart the application
        
        You can still use the Risk Assessment tab without Gen AI features.
        """)
        st.stop()
    
    # Chat interface
    st.markdown("### Chat with Care Navigator")
    st.caption("Ask questions about your symptoms, risk factors, and care recommendations")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # User input
    user_input = st.chat_input("Type your question here...")
    
    if user_input:
        # Add user message to history (for display only)
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Generate response
        with st.chat_message("assistant"):
            if st.session_state.current_risk_score is None:
                st.warning("Please calculate your risk score in the 'Patient Risk Assessment' tab first.")
            else:
                with st.spinner("Generating personalized guidance..."):
                    try:
                        # Get current symptoms and risk score
                        symptom_list = st.session_state.current_symptoms
                        risk_score = st.session_state.current_risk_score
                        
                        # Determine risk category using the same dynamic thresholds as model.py
                        # Import predictor to get the actual thresholds
                        from model import ReadmissionPredictor, DEFAULT_THRESHOLD_LOW_MODERATE, DEFAULT_THRESHOLD_MODERATE_HIGH
                        
                        # Try to load predictor to get dynamic thresholds, fallback to defaults
                        try:
                            predictor_temp = ReadmissionPredictor()
                            threshold_low = predictor_temp.threshold_low_moderate
                            threshold_high = predictor_temp.threshold_moderate_high
                        except Exception:
                            # Fallback to default percentile-based thresholds
                            threshold_low = DEFAULT_THRESHOLD_LOW_MODERATE
                            threshold_high = DEFAULT_THRESHOLD_MODERATE_HIGH
                        
                        # Categorize using dynamic thresholds
                        if risk_score < threshold_low:
                            risk_category = "Low"
                        elif risk_score < threshold_high:
                            risk_category = "Moderate"
                        else:
                            risk_category = "High"
                        
                        # Generate advice using Gen AI - completely stateless call
                        # Only pass current context, NOT chat history
                        # The gen_ai.py now uses non-streaming mode (stream=False) to prevent truncation
                        advice = assistant.generate_advice(
                            patient_symptoms=symptom_list,
                            ml_risk_score=risk_score,
                            risk_category=risk_category,
                            user_question=user_input
                        )
                        
                        # Display full response using st.markdown - no streaming chunks
                        # This ensures the complete text is rendered at once without truncation
                        st.markdown(advice)
                        
                        # Add to chat history (for display only)
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": advice
                        })
                        
                    except Exception as e:
                        error_msg = f"Error generating response: {str(e)}"
                        st.error(error_msg)
                        import traceback
                        st.code(traceback.format_exc())
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": error_msg
                        })
    
    # Context display with improved layout
    st.markdown("---")
    st.subheader("📋 Current Patient Context")
    
    # Use metric cards for better visual presentation - updated to show Clinical Severity
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.current_risk_score is not None:
            # Convert to Clinical Severity Score (0-100 scale)
            severity_score = st.session_state.current_risk_score * 100
            st.metric(
                label="Clinical Severity Score",
                value=f"{severity_score:.0f}/100",
                delta=None
            )
        else:
            st.info("⚠️ Calculate risk score in Tab 1 first")
    
    with col2:
        symptom_count = len(st.session_state.current_symptoms) if st.session_state.current_symptoms else 0
        st.metric(
            label="Reported Symptoms",
            value=symptom_count
        )
    
    with col3:
        if st.session_state.current_risk_score is not None:
            # Use dynamic percentile-based thresholds from the trained model
            # Import predictor to get the actual thresholds
            from model import ReadmissionPredictor, DEFAULT_THRESHOLD_LOW_MODERATE, DEFAULT_THRESHOLD_MODERATE_HIGH
            
            # Try to load predictor to get dynamic thresholds, fallback to defaults
            try:
                predictor_temp = ReadmissionPredictor()
                threshold_low = predictor_temp.threshold_low_moderate
                threshold_high = predictor_temp.threshold_moderate_high
            except Exception:
                # Fallback to default percentile-based thresholds
                threshold_low = DEFAULT_THRESHOLD_LOW_MODERATE
                threshold_high = DEFAULT_THRESHOLD_MODERATE_HIGH
            
            # Map to clinical urgency levels
            urgency_mapping = {
                "Low": "Routine Monitoring",
                "Moderate": "Increased Surveillance", 
                "High": "Immediate Intervention"
            }
            
            # Categorize using dynamic thresholds
            if st.session_state.current_risk_score < threshold_low:
                st.success("**Urgency Level:** ROUTINE MONITORING")
            elif st.session_state.current_risk_score < threshold_high:
                st.warning("**Urgency Level:** INCREASED SURVEILLANCE")
            else:
                st.error("**Urgency Level:** IMMEDIATE INTERVENTION")
        else:
            st.caption("Pending assessment")
    
    # Show symptoms list if any
    if st.session_state.current_symptoms:
        with st.expander("View Reported Symptoms"):
            symptoms_display = ", ".join(st.session_state.current_symptoms)
            st.write(f"💬 {symptoms_display}")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History", use_container_width=False):
        st.session_state.chat_history = []
        st.rerun()


# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.caption("""
**Disclaimer**: This application provides AI-generated guidance for informational purposes only. 
It does NOT constitute medical advice. Always consult with qualified healthcare professionals 
for medical decisions. In emergencies, call 995 or go to the nearest A&E.
""")
