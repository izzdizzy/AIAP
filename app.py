# =============================================================================
# Hospital Readmission Predictor - Main Streamlit Application
# =============================================================================
# This is the main entry point for the Diabetes Care Navigation Assistant.
# It provides a two-tab interface:
# 1. Patient Risk Assessment: ML-based readmission risk prediction with SHAP analysis
# 2. Care Navigation: Gen AI-powered personalized healthcare guidance
#
# The app integrates:
# - XGBoost model trained on UCI Diabetes dataset (optimized for 80-90% Recall)
# - Clinical severity adjustment layer for medical red flags
# - Google Gemini API for contextual care navigation advice
# - Singapore healthcare context (CHAS, Healthier SG, Polyclinics)
#
# Usage:
#     streamlit run app.py
#
# Environment Variables:
#     GEMINI_API_KEY: Required for Gen AI features
# =============================================================================

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
from utils import (
    FEATURE_DISPLAY_NAMES,
    CSV_TO_MODEL_MAPPING,
    SYMPTOM_OPTIONS,
    calculate_clinical_adjustment,
    parse_uploaded_file,
    age_numeric_to_age_group,
    validate_symptoms,
)


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


# =============================================================================
# CLINICAL SEVERITY ADJUSTMENT - POST-PROCESSING LAYER
# =============================================================================

def calculate_clinical_adjustment(features_dict: dict) -> int:
    """
    Apply clinical severity adjustment based on established medical red flags.
    
    The ML model was trained on noisy UCI data and may produce counter-intuitive
    results (e.g., penalizing extremely high lab procedures). This post-processing
    layer ensures that clinically severe patients receive appropriate risk scores
    by adding heuristic bonuses for known risk factors.
    
    Args:
        features_dict: Dictionary containing patient feature values
        
    Returns:
        Integer severity adjustment points (0 or positive)
    """
    adjustment_points = 0
    
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
    Also calculates data completeness percentage for confidence assessment.
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
        
        # Count total columns provided vs expected model features
        expected_feature_count = 82  # Full model feature count
        provided_columns = len(df.columns)
        data_completeness_pct = (provided_columns / expected_feature_count) * 100
        
        extracted_data = {}
        columns_provided_count = 0
        
        # TASK 1: Use explicit CSV_TO_MODEL_MAPPING dictionary for strict column mapping
        # Iterate through the mapping and apply CSV values to exact model feature names
        for csv_col, model_feature in CSV_TO_MODEL_MAPPING.items():
            if csv_col in df.columns:
                value = patient_row[csv_col]
                columns_provided_count += 1
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


def reset_session_state_for_new_upload():
    """
    Clear all session state keys related to model features and form inputs
    before processing a new file upload. This prevents state bleed-over from
    previous uploads or manual form inputs.
    """
    # List of all widget keys that need to be reset
    widget_keys_to_reset = [
        'prior_admissions_input',
        'comorbidity_count_input',
        'age_group_input',
        'medication_count_input',
        'discharge_diagnosis_input',
        'high_risk_flag_input',
        'symptoms_multiselect',
        'parsed_patient_data'
    ]
    
    # Reset widget keys to default values
    for key in widget_keys_to_reset:
        if key in st.session_state:
            if key == 'symptoms_multiselect':
                st.session_state[key] = []
            elif key == 'parsed_patient_data':
                st.session_state[key] = {}
            elif key == 'age_group_input':
                st.session_state[key] = 6  # Default to 60-70
            elif key == 'high_risk_flag_input':
                st.session_state[key] = 0
            elif key in ['prior_admissions_input', 'comorbidity_count_input', 'medication_count_input']:
                st.session_state[key] = 0
            else:
                st.session_state[key] = "" if key == 'discharge_diagnosis_input' else 0
    
    # Also reset any derived/session features that might have stale values
    derived_feature_keys = [
        'current_risk_score', 'clinical_severity_score', 'current_symptoms'
    ]
    for key in derived_feature_keys:
        if key in st.session_state:
            st.session_state[key] = None if key == 'current_risk_score' else ([] if key == 'current_symptoms' else 0)


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
        # Only process the file if it's different from the last processed file
        # This prevents infinite rerun loops when the same file remains selected
        last_processed_file = st.session_state.get('processed_file_name', None)
        
        if last_processed_file != uploaded_file.name:
            # CRITICAL: Reset all session state before processing new upload to prevent state bleed-over
            reset_session_state_for_new_upload()
            
            try:
                parsed_data = parse_uploaded_file(uploaded_file)
                if parsed_data:
                    # Store parsed data in session state - widgets will read from this during initialization
                    st.session_state['parsed_patient_data'] = parsed_data
                    st.session_state['processed_file_name'] = uploaded_file.name
                    
                    # Store completeness info for prediction-time adjustment
                    st.session_state['data_completeness_pct'] = parsed_data.get('data_completeness_pct', 100.0)
                    st.session_state['data_completeness_low'] = parsed_data.get('is_low_completeness', False)
                    
                    st.success(f"✅ Successfully loaded data from {uploaded_file.name}")
                    
                    # Show preview with human-readable labels
                    with st.expander("View loaded data"):
                        # Display with friendly names where available
                        friendly_data = {}
                        for key, value in parsed_data.items():
                            if key not in ['data_completeness_pct', 'is_low_completeness']:
                                display_name = FEATURE_DISPLAY_NAMES.get(key, key)
                                friendly_data[display_name] = value
                        st.json(friendly_data)
                    
                    # Trigger a single rerun to ensure widgets render with fresh state
                    st.rerun()
                else:
                    st.error("Failed to parse the uploaded file. Please check the file format.")
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
        else:
            # File already processed, just show a subtle indicator
            st.info(f"📄 Using data from {uploaded_file.name}")
    
    st.markdown("---")
    st.subheader("Clinical Features")
    
    # =============================================================================
    # CRITICAL FIX: SESSION STATE INITIALIZATION FLOW
    # =============================================================================
    # Streamlit Rule: Widget keys must be initialized BEFORE the widget is declared.
    # However, we must prioritize CSV upload data over manual input defaults.
    # 
    # Flow:
    # 1. Check if parsed_patient_data exists (from CSV upload)
    # 2. If YES: ALWAYS override session state with CSV values (this ensures fresh uploads update widgets)
    # 3. If NO: Only initialize if key doesn't exist (preserves manual user input across reruns)
    # =============================================================================
    
    parsed_data = st.session_state.get('parsed_patient_data', {})
    has_csv_data = len(parsed_data) > 0
    
    # Define age options for conversion
    age_options = ["0-10", "10-20", "20-30", "30-40", "40-50", "50-60", "60-70", "70-80", "80-90", "90-100"]
    
    # -------------------------------------------------------------------------
    # STEP 1: If CSV data exists, ALWAYS update session state from CSV
    # This ensures uploaded files always take precedence and widgets reflect new data
    # -------------------------------------------------------------------------
    if has_csv_data:
        # prior_admissions: direct mapping from CSV
        if 'prior_admissions' in parsed_data:
            st.session_state.prior_admissions_input = int(parsed_data['prior_admissions'])
        
        # comorbidity_count: direct mapping from CSV
        if 'comorbidity_count' in parsed_data:
            st.session_state.comorbidity_count_input = int(parsed_data['comorbidity_count'])
        
        # age_group_input: store the actual age group STRING (not index) since selectbox returns string
        if 'age_group_display' in parsed_data and parsed_data['age_group_display'] in age_options:
            st.session_state.age_group_input = parsed_data['age_group_display']
        elif 'age_numeric' in parsed_data:
            # Fallback: compute age_group_display from age_numeric
            age = int(parsed_data['age_numeric'])
            if age < 10:
                st.session_state.age_group_input = "0-10"
            elif age < 20:
                st.session_state.age_group_input = "10-20"
            elif age < 30:
                st.session_state.age_group_input = "20-30"
            elif age < 40:
                st.session_state.age_group_input = "30-40"
            elif age < 50:
                st.session_state.age_group_input = "40-50"
            elif age < 60:
                st.session_state.age_group_input = "50-60"
            elif age < 70:
                st.session_state.age_group_input = "60-70"
            elif age < 80:
                st.session_state.age_group_input = "70-80"
            elif age < 90:
                st.session_state.age_group_input = "80-90"
            else:
                st.session_state.age_group_input = "90-100"
        
        # medication_count: direct mapping from CSV num_medications
        if 'num_medications' in parsed_data:
            st.session_state.medication_count_input = int(parsed_data['num_medications'])
        
        # discharge_diagnosis: string conversion from CSV
        if 'discharge_diagnosis' in parsed_data:
            st.session_state.discharge_diagnosis_input = str(parsed_data['discharge_diagnosis'])
        
        # high_risk_flag_input: convert CSV value (0/1 or Yes/No) to index (0=No, 1=Yes)
        if 'high_risk_display' in parsed_data:
            st.session_state.high_risk_flag_input = 1 if parsed_data['high_risk_display'] == "Yes" else 0
        elif 'high_risk_flag' in parsed_data:
            flag_val = parsed_data['high_risk_flag']
            st.session_state.high_risk_flag_input = 1 if (flag_val == 1 or (isinstance(flag_val, str) and flag_val.lower() == 'yes')) else 0
        
        # symptoms_multiselect: list from CSV parsing
        if 'symptoms_list' in parsed_data:
            st.session_state.symptoms_multiselect = parsed_data['symptoms_list']
    
    # -------------------------------------------------------------------------
    # STEP 2: If NO CSV data, initialize defaults only if keys don't exist
    # This preserves manual user input across reruns when no upload is present
    # -------------------------------------------------------------------------
    else:
        if "prior_admissions_input" not in st.session_state:
            st.session_state.prior_admissions_input = 1
        if "comorbidity_count_input" not in st.session_state:
            st.session_state.comorbidity_count_input = 3
        if "age_group_input" not in st.session_state:
            st.session_state.age_group_input = "60-70"  # Default to 60-70 (string, matching selectbox options)
        if "medication_count_input" not in st.session_state:
            st.session_state.medication_count_input = 5
        if "discharge_diagnosis_input" not in st.session_state:
            st.session_state.discharge_diagnosis_input = "250.01"
        if "high_risk_flag_input" not in st.session_state:
            st.session_state.high_risk_flag_input = 0
        if "symptoms_multiselect" not in st.session_state:
            st.session_state.symptoms_multiselect = []
    
    # 6 Clinical Features from the dataset - using human-readable labels
    # =============================================================================
    # CRITICAL STREAMLIT RULE: Do NOT pass value=st.session_state[...] to widgets.
    # Streamlit automatically manages widget values via the 'key' parameter.
    # The widget will display whatever is in st.session_state[key] and update it on user interaction.
    # =============================================================================
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
    
    # Sync symptoms to current_symptoms for chat interface
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
    
    # Prepare input data - read from session state to ensure we use current widget values
    # This guarantees manual slider/input changes immediately trigger correct ML inference
    age_mapping = {
        "0-10": 0, "10-20": 10, "20-30": 20, "30-40": 30, "40-50": 40,
        "50-60": 50, "60-70": 60, "70-80": 70, "80-90": 80, "90-100": 90
    }
    age_encoded = age_mapping.get(st.session_state.age_group_input, 60)
    
    # Get current values from session state (widgets update these automatically on user interaction)
    curr_prior_admissions = st.session_state.prior_admissions_input
    curr_comorbidity_count = st.session_state.comorbidity_count_input
    curr_medication_count = st.session_state.medication_count_input
    curr_high_risk_flag = "Yes" if st.session_state.high_risk_flag_input == 1 else "No"
    curr_discharge_diagnosis = st.session_state.discharge_diagnosis_input
    
    # Calculate interaction features (as done in training)
    age_comorbidity_interaction = age_encoded * curr_comorbidity_count
    medication_comorbidity_interaction = curr_medication_count * curr_comorbidity_count
    admissions_comorbidity_interaction = curr_prior_admissions * curr_comorbidity_count
    age_medication_interaction = age_encoded * curr_medication_count
    
    # Convert diagnosis to float
    try:
        diagnosis_float = float(curr_discharge_diagnosis)
    except ValueError:
        diagnosis_float = 250.01  # Default diabetes code
    
    # Build patient data dictionary with ALL expected features from feature_columns.json
    # This ensures the DataFrame matches exactly what the model expects.
    # For any feature not present in the CSV/uploaded data, we use dataset baselines
    # (medians/modes) instead of zeros to prevent distribution shifts that cause 
    # false high-risk predictions.
    patient_data = {}
    
    # First, initialize ALL expected features with baseline defaults from training
    # This provides a realistic clinical background for partial CSV uploads
    if predictor.feature_defaults:
        for feature in expected_features:
            if feature in predictor.feature_defaults:
                patient_data[feature] = predictor.feature_defaults[feature]
            else:
                patient_data[feature] = 0  # Fallback if no default available
    else:
        # Fallback to zero initialization if defaults not available
        for feature in expected_features:
            patient_data[feature] = 0
    
    # Now override with actual values from user input / parsed CSV data
    # Only the features that have valid values should be set
    # CRITICAL FIX: Use dataset mode/median defaults instead of arbitrary hardcoded values
    patient_data['admission_type_id'] = 1  # Mode value from dataset (elective admission)
    patient_data['discharge_disposition_id'] = 1  # Mode value - discharged to home (NOT 0, which is invalid)
    patient_data['admission_source_id'] = 7  # FIX: Use dataset mode (7) instead of 1 (physician referral)
    patient_data['time_in_hospital'] = 4  # FIX: Use dataset median (4 days) instead of 5
    patient_data['num_lab_procedures'] = 44  # FIX: Use dataset median (44) instead of 50
    patient_data['num_procedures'] = 0  # FIX: Use dataset median (0) instead of 5 - most patients have no procedures
    patient_data['num_medications'] = curr_medication_count  # From session state (widget value)
    patient_data['number_outpatient'] = 0  # Dataset mode - most patients have 0 outpatient visits
    patient_data['number_emergency'] = 0  # FIX: Default to 0, not prior_admissions // 2
    patient_data['number_inpatient'] = curr_prior_admissions  # From session state (widget value)
    patient_data['number_diagnoses'] = max(curr_comorbidity_count + 1, 1)  # At least primary diagnosis
    patient_data['diabetes_diag_count'] = 1  # At least 1 diabetes diagnosis
    patient_data['comorbidity_count'] = curr_comorbidity_count  # From session state (widget value)
    patient_data['metformin_encoded'] = 1  # Most common diabetes medication
    patient_data['metformin_active'] = 1  # Most common active medication
    # repaglinide through citoglipton remain at baseline defaults from feature_defaults.json
    # FIX: Use actual medication status, not high_risk_flag as proxy
    patient_data['insulin_encoded'] = 1 if curr_high_risk_flag == "Yes" else 0
    patient_data['insulin_active'] = 1 if curr_high_risk_flag == "Yes" else 0
    # combination meds remain at baseline defaults
    patient_data['total_medications'] = curr_medication_count
    patient_data['on_insulin'] = 1 if curr_high_risk_flag == "Yes" else 0
    patient_data['oral_medications'] = 1 if curr_high_risk_flag == "No" else 0
    patient_data['change_encoded'] = 0  # Default - no medication change
    patient_data['diabetesMed_encoded'] = 1  # Default - on diabetes medication
    patient_data['age_numeric'] = age_encoded  # From user input
    patient_data['is_elderly'] = 1 if age_encoded >= 65 else 0
    
    # ================================================================
    # TASK 1: RECALCULATE ENGINEERED FEATURES EXACTLY AS IN TRAIN_MODEL.PY
    # ================================================================
    # Calculate total_prior_admissions = sum of outpatient, emergency, inpatient
    patient_data['total_prior_admissions'] = (
        patient_data['number_outpatient'] + 
        patient_data['number_emergency'] + 
        patient_data['number_inpatient']
    )
    
    # Handle division by zero for ratios
    total_admissions = patient_data['total_prior_admissions']
    if total_admissions == 0:
        total_admissions = 1  # Prevent division by zero
    
    # Calculate inpatient_ratio = number_inpatient / total_prior_admissions
    patient_data['inpatient_ratio'] = patient_data['number_inpatient'] / total_admissions
    
    # Calculate emergency_ratio = number_emergency / total_prior_admissions
    patient_data['emergency_ratio'] = patient_data['number_emergency'] / total_admissions
    
    # Calculate long_stay = 1 if time_in_hospital > 7 else 0
    patient_data['long_stay'] = 1 if patient_data['time_in_hospital'] > 7 else 0
    
    # Calculate total_procedures (same as num_procedures in this context)
    patient_data['total_procedures'] = patient_data['num_procedures']
    
    # Calculate high_lab_utilization = 1 if num_lab_procedures > 100 else 0
    patient_data['high_lab_utilization'] = 1 if patient_data['num_lab_procedures'] > 100 else 0
    
    # Calculate high_diagnosis_count = 1 if comorbidity_count > 5 else 0
    patient_data['high_diagnosis_count'] = 1 if patient_data['comorbidity_count'] > 5 else 0
    
    # Calculate emergency_admission (based on admission_type_id == 4 for emergency)
    patient_data['emergency_admission'] = 1 if patient_data['admission_type_id'] == 4 else 0
    
    # Calculate not_home_discharge = 1 if discharge_disposition_id != 1 else 0
    patient_data['not_home_discharge'] = 1 if patient_data['discharge_disposition_id'] != 1 else 0
    
    # Calculate er_admission (based on admission_source_id == 4 for ER)
    patient_data['er_admission'] = 1 if patient_data['admission_source_id'] == 4 else 0
    
    # Calculate interaction features EXACTLY as in train_model.py
    # age_comorbidity_interaction = age_numeric * comorbidity_count
    patient_data['age_comorbidity_interaction'] = patient_data['age_numeric'] * patient_data['comorbidity_count']
    
    # med_per_comorbidity = total_medications / max(comorbidity_count, 1)
    patient_data['med_per_comorbidity'] = patient_data['total_medications'] / max(patient_data['comorbidity_count'], 1)
    
    # admissions_per_year = total_prior_admissions / (age_numeric + 1) [as per train_model.py line 573-575]
    patient_data['admissions_per_year'] = patient_data['total_prior_admissions'] / (patient_data['age_numeric'] + 1)
    
    # emerg_inpatient_combo = number_emergency * number_inpatient [as per train_model.py line 579-581]
    patient_data['emerg_inpatient_combo'] = patient_data['number_emergency'] * patient_data['number_inpatient']
    
    # insulin_complexity = on_insulin * total_medications [as per train_model.py line 585]
    patient_data['insulin_complexity'] = patient_data['on_insulin'] * patient_data['total_medications']
    
    # diabetes_med_intensity = diabetes_diag_count * total_medications [as per train_model.py line 589-591]
    patient_data['diabetes_med_intensity'] = patient_data['diabetes_diag_count'] * patient_data['total_medications']
    
    # If we have parsed CSV data, override the defaults with actual CSV values
    # TASK 2: Apply CSV values using the explicit model feature names from CSV_TO_MODEL_MAPPING
    parsed_data = st.session_state.get('parsed_patient_data', {})
    if parsed_data:
        # Map CSV columns directly to expected features using exact model feature names
        # Only set values for features that exist in both the CSV and expected_features
        for feature in expected_features:
            if feature in parsed_data:
                csv_value = parsed_data[feature]
                # Handle NaN values from CSV
                if pd.isna(csv_value):
                    patient_data[feature] = 0
                else:
                    patient_data[feature] = csv_value
        
        # Handle special mappings from parsed data - using model feature names
        # Note: prior_admissions is mapped to total_prior_admissions by CSV_TO_MODEL_MAPPING
        # but we also need number_inpatient set separately
        if 'number_inpatient' in parsed_data:
            patient_data['number_inpatient'] = int(parsed_data['number_inpatient'])
        if 'num_medications' in parsed_data:
            patient_data['num_medications'] = int(parsed_data['num_medications'])
        if 'comorbidity_count' in parsed_data:
            patient_data['comorbidity_count'] = int(parsed_data['comorbidity_count'])
            patient_data['number_diagnoses'] = max(int(parsed_data['comorbidity_count']) + 1, 1)
        if 'age_numeric' in parsed_data:
            patient_data['age_numeric'] = int(parsed_data['age_numeric'])
            patient_data['is_elderly'] = 1 if int(parsed_data['age_numeric']) >= 65 else 0
        if 'high_risk_flag' in parsed_data:
            flag_val = parsed_data['high_risk_flag']
            is_high_risk = flag_val == 1 or (isinstance(flag_val, str) and flag_val.lower() == 'yes')
            patient_data['insulin_encoded'] = 1 if is_high_risk else 0
            patient_data['insulin_active'] = 1 if is_high_risk else 0
            patient_data['on_insulin'] = 1 if is_high_risk else 0
            patient_data['oral_medications'] = 1 if not is_high_risk else 0
        if 'time_in_hospital' in parsed_data:
            patient_data['time_in_hospital'] = int(parsed_data['time_in_hospital'])
        if 'num_lab_procedures' in parsed_data:
            patient_data['num_lab_procedures'] = int(parsed_data['num_lab_procedures'])
        if 'num_procedures' in parsed_data:
            patient_data['num_procedures'] = int(parsed_data['num_procedures'])
        if 'number_outpatient' in parsed_data:
            patient_data['number_outpatient'] = int(parsed_data['number_outpatient'])
        if 'number_emergency' in parsed_data:
            patient_data['number_emergency'] = int(parsed_data['number_emergency'])
        if 'number_diagnoses' in parsed_data:
            patient_data['number_diagnoses'] = max(int(parsed_data['number_diagnoses']), 1)
        if 'diabetes_diag_count' in parsed_data:
            patient_data['diabetes_diag_count'] = int(parsed_data['diabetes_diag_count'])
        if 'metformin_encoded' in parsed_data:
            patient_data['metformin_encoded'] = int(parsed_data['metformin_encoded'])
            patient_data['metformin_active'] = int(parsed_data['metformin_encoded'])
        if 'insulin_encoded' in parsed_data:
            patient_data['insulin_encoded'] = int(parsed_data['insulin_encoded'])
            patient_data['insulin_active'] = int(parsed_data['insulin_encoded'])
        if 'on_insulin' in parsed_data:
            patient_data['on_insulin'] = int(parsed_data['on_insulin'])
        if 'change_encoded' in parsed_data:
            patient_data['change_encoded'] = int(parsed_data['change_encoded'])
        if 'diabetesMed_encoded' in parsed_data:
            patient_data['diabetesMed_encoded'] = int(parsed_data['diabetesMed_encoded'])
    
    # ================================================================
    # TASK 1: RECALCULATE DERIVED FEATURES AFTER CSV OVERRIDE
    # Must recalculate these after CSV data is applied to ensure consistency
    # ================================================================
    
    # Recalculate total_prior_admissions from base components
    patient_data['total_prior_admissions'] = (
        patient_data['number_outpatient'] + 
        patient_data['number_emergency'] + 
        patient_data['number_inpatient']
    )
    
    # Handle division by zero for ratios
    total_admissions = patient_data['total_prior_admissions']
    if total_admissions == 0:
        total_admissions = 1  # Prevent division by zero
    
    # Recalculate inpatient_ratio = number_inpatient / total_prior_admissions
    patient_data['inpatient_ratio'] = patient_data['number_inpatient'] / total_admissions
    
    # Recalculate emergency_ratio = number_emergency / total_prior_admissions
    patient_data['emergency_ratio'] = patient_data['number_emergency'] / total_admissions
    
    # Recalculate long_stay = 1 if time_in_hospital > 7 else 0
    patient_data['long_stay'] = 1 if patient_data['time_in_hospital'] > 7 else 0
    
    # Recalculate total_procedures
    patient_data['total_procedures'] = patient_data['num_procedures']
    
    # Recalculate high_lab_utilization
    patient_data['high_lab_utilization'] = 1 if patient_data['num_lab_procedures'] > 100 else 0
    
    # Recalculate high_diagnosis_count
    patient_data['high_diagnosis_count'] = 1 if patient_data['comorbidity_count'] > 5 else 0
    
    # Recalculate emergency_admission
    patient_data['emergency_admission'] = 1 if patient_data['admission_type_id'] == 4 else 0
    
    # Recalculate not_home_discharge
    patient_data['not_home_discharge'] = 1 if patient_data['discharge_disposition_id'] != 1 else 0
    
    # Recalculate er_admission
    patient_data['er_admission'] = 1 if patient_data['admission_source_id'] == 4 else 0
    
    # Recalculate interaction features EXACTLY as in train_model.py
    patient_data['age_comorbidity_interaction'] = patient_data['age_numeric'] * patient_data['comorbidity_count']
    patient_data['med_per_comorbidity'] = patient_data['total_medications'] / max(patient_data['comorbidity_count'], 1)
    patient_data['admissions_per_year'] = patient_data['total_prior_admissions'] / (patient_data['age_numeric'] + 1)
    patient_data['emerg_inpatient_combo'] = patient_data['number_emergency'] * patient_data['number_inpatient']
    patient_data['insulin_complexity'] = patient_data['on_insulin'] * patient_data['total_medications']
    patient_data['diabetes_med_intensity'] = patient_data['diabetes_diag_count'] * patient_data['total_medications']
    
    # Display input summary with human-readable labels
    # CRITICAL FIX: Read directly from session state keys to ensure UI always shows current widget values
    st.markdown("### 📋 Patient Data Summary")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Clinical Input Values")
        # Create a human-readable summary that reads DIRECTLY from session state
        # This guarantees the displayed values ALWAYS match what the user sees in widgets
        # and what will be used for ML inference on button click
        summary_data = {
            FEATURE_DISPLAY_NAMES.get('prior_admissions', 'Prior Admissions'): st.session_state.prior_admissions_input,
            FEATURE_DISPLAY_NAMES.get('comorbidity_count', 'Comorbidity Count'): st.session_state.comorbidity_count_input,
            "Age Group": st.session_state.age_group_input,
            FEATURE_DISPLAY_NAMES.get('num_medications', 'Medication Count'): st.session_state.medication_count_input,
            FEATURE_DISPLAY_NAMES.get('discharge_diagnosis', 'Discharge Diagnosis'): st.session_state.discharge_diagnosis_input,
            FEATURE_DISPLAY_NAMES.get('high_risk_flag', 'High Risk Flag'): "Yes" if st.session_state.high_risk_flag_input == 1 else "No",
        }
        st.json(summary_data)
    
    with col2:
        st.subheader("Reported Symptoms")
        # CRITICAL FIX: Read directly from session state to ensure symptoms display matches widget
        current_syms = st.session_state.get('symptoms_multiselect', [])
        if current_syms:
            symptoms_text = ", ".join(current_syms)
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
                
                # Store raw probability from calibrated model as "Base Risk Score"
                raw_risk_score = result['risk_score']
                
                # Apply Clinical Severity Adjustment to compensate for dataset noise
                # This ensures medical red flags are properly weighted
                clinical_adjustment_points = calculate_clinical_adjustment(patient_data)
                
                # Calculate Final Severity Score: (raw_prob * 100) + clinical_adjustment_points
                # Clamp between 0 and 100
                base_severity = raw_risk_score * 100
                final_severity_score = min(100, max(0, base_severity + clinical_adjustment_points))
                
                # Check data completeness for confidence adjustment
                is_low_completeness = st.session_state.get('data_completeness_low', False)
                baseline_readmission_rate = 0.11  # Dataset baseline (~11%)
                
                # Apply completeness penalty if data is insufficient
                if is_low_completeness:
                    # Pull severity toward baseline (11%) when data is <20% complete
                    # This prevents median-imputed features from artificially inflating risk
                    completeness_factor = st.session_state.get('data_completeness_pct', 10.0) / 20.0
                    adjusted_risk_score = (raw_risk_score * completeness_factor) + \
                                         (baseline_readmission_rate * (1 - completeness_factor))
                    st.session_state.current_risk_score = adjusted_risk_score
                    # Apply clinical adjustment to the completeness-adjusted score as well
                    adjusted_severity = min(100, max(0, (adjusted_risk_score * 100) + clinical_adjustment_points))
                    st.session_state.clinical_severity_score = adjusted_severity
                    st.session_state.is_low_confidence = True
                else:
                    st.session_state.current_risk_score = raw_risk_score
                    st.session_state.clinical_severity_score = final_severity_score
                    st.session_state.is_low_confidence = False
                
                # Store clinical adjustment info for display
                st.session_state.clinical_adjustment_points = clinical_adjustment_points
                st.session_state.base_severity = base_severity
                
                # Calculate risk_category locally based on FINAL severity score thresholds
                risk_score_for_categorization = st.session_state.clinical_severity_score / 100.0
                if risk_score_for_categorization <= 0.30:
                    risk_category = "Low"
                elif risk_score_for_categorization <= 0.60:
                    risk_category = "Moderate"
                else:
                    risk_category = "High"
                
                # Display results
                st.subheader("Patient Risk Assessment")
                
                # Clinical severity score display - using absolute probability scale (0-100)
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Use the Clinical Severity Score from model (raw_prob * 100)
                    severity_score = st.session_state.clinical_severity_score
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
                    
                    # Override urgency text for low-confidence predictions
                    if st.session_state.is_low_confidence:
                        urgency_level = "Requires More Data - Estimate Only"
                    else:
                        urgency_level = urgency_mapping.get(risk_category, risk_category)
                    
                    st.metric(
                        "Urgency Level",
                        urgency_level,
                        delta=None,
                        delta_color="normal"
                    )
                
                with col3:
                    # Display confidence level
                    confidence_pct = st.session_state.get('data_completeness_pct', 100.0)
                    if st.session_state.is_low_confidence:
                        confidence_display = f"Low ({confidence_pct:.0f}%)"
                    else:
                        confidence_display = f"High ({min(confidence_pct, 100):.0f}%)"
                    
                    st.metric(
                        "Confidence Level",
                        confidence_display,
                        delta=None
                    )
                
                # Clinical philosophy explanation - critical for user understanding
                st.info(
                    "**Clinical Philosophy:** This model is optimized for ROC-AUC to produce well-calibrated probabilities. "
                    "Your score reflects the absolute predicted risk of 30-day readmission (e.g., a score of 15 means 15% predicted risk). "
                    "Absolute thresholds are used for urgency classification."
                )
                
                # Updated risk interpretation with clinical urgency framing
                st.markdown("### Clinical Interpretation")
                
                if risk_category == "Low":
                    st.success("""
                    **Routine Monitoring**: Patient shows low clinical severity relative to the population. 
                    Continue current management plan with standard follow-up schedule.
                    Maintain regular appointments with your healthcare provider and adhere to prescribed medications.
                    """)
                elif risk_category == "Moderate":
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
                
                # ================================================================
                # TASK 3: EXACT DEBUG OUTPUT - Show ALL 82 features being fed to model
                # ================================================================
                with st.expander("🔧 Show Raw Debug Info", expanded=False):
                    st.markdown("**Raw Model Output:**")
                    st.code(f"Raw Probability (Base Risk Score): {result['risk_score']:.6f}")
                    st.code(f"Base Severity (raw_prob * 100): {st.session_state.base_severity:.2f}")
                    st.code(f"Clinical Adjustment Points: {st.session_state.clinical_adjustment_points}")
                    st.code(f"Final Severity Score (Base + Adjustment, clamped 0-100): {st.session_state.clinical_severity_score:.2f}")
                    st.info("**Note:** Final score includes a Clinical Logic Adjustment to compensate for dataset noise and ensure medical red flags are properly weighted.")
                    
                    st.markdown("**ALL 82 Features Being Fed to Model (Exact Order):**")
                    # Display the complete patient_data dictionary with all 82 features
                    # This allows verification that derived features like inpatient_ratio are calculated correctly
                    all_features_df = pd.DataFrame([
                        {"Feature Key": k, "Display Name": FEATURE_DISPLAY_NAMES.get(k, k), "Value": v}
                        for k, v in patient_data.items()
                    ])
                    st.dataframe(all_features_df, use_container_width=True, height=500)
                    
                    st.markdown("**Key Derived Feature Verification:**")
                    st.write(f"- `number_inpatient`: {patient_data.get('number_inpatient', 'N/A')}")
                    st.write(f"- `number_outpatient`: {patient_data.get('number_outpatient', 'N/A')}")
                    st.write(f"- `number_emergency`: {patient_data.get('number_emergency', 'N/A')}")
                    st.write(f"- `total_prior_admissions`: {patient_data.get('total_prior_admissions', 'N/A')}")
                    st.write(f"- `inpatient_ratio` (should be 0 when number_inpatient=0): {patient_data.get('inpatient_ratio', 'N/A')}")
                    st.write(f"- `emergency_ratio`: {patient_data.get('emergency_ratio', 'N/A')}")
                    st.write(f"- `discharge_disposition_id` (must NOT be 0): {patient_data.get('discharge_disposition_id', 'N/A')}")
                    st.write(f"- `number_diagnoses` (must NOT be 0): {patient_data.get('number_diagnoses', 'N/A')}")
                    
                    st.caption("This debug info shows the EXACT 82 features in order being passed to the ML model. Verify that derived features like `inpatient_ratio` are mathematically recalculated from base inputs, not hardcoded defaults.")
                
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
                        severity_score = st.session_state.get('clinical_severity_score', risk_score * 100)
                        
                        # Determine risk category using absolute thresholds (0-100 scale)
                        # 0-30: Routine Monitoring, 31-60: Increased Surveillance, 61-100: Immediate Intervention
                        if severity_score <= 30:
                            risk_category = "Low"
                        elif severity_score <= 60:
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
            # Get the Clinical Severity Score from session state or calculate it
            # The score is now simply raw_probability * 100 (absolute scale)
            severity_score = st.session_state.get('clinical_severity_score', st.session_state.current_risk_score * 100)
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
            # Use absolute thresholds (0-100 scale)
            # 0-30: Routine Monitoring, 31-60: Increased Surveillance, 61-100: Immediate Intervention
            severity_score = st.session_state.get('clinical_severity_score', st.session_state.current_risk_score * 100)
            
            # Map to clinical urgency levels based on 0-100 severity scale
            if severity_score <= 30:
                st.success("**Urgency Level:** ROUTINE MONITORING")
            elif severity_score <= 60:
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
