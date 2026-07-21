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


# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_risk_score' not in st.session_state:
    st.session_state.current_risk_score = None
if 'current_symptoms' not in st.session_state:
    st.session_state.current_symptoms = []
if 'form_initialized' not in st.session_state:
    st.session_state.form_initialized = False


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
            # Store parsed data in session state for form pre-filling
            st.session_state['parsed_patient_data'] = parsed_data
            st.success(f"✅ Successfully loaded data from {uploaded_file.name}")
            
            # Show preview
            with st.expander("View loaded data"):
                st.json(parsed_data)
    
    st.markdown("---")
    st.subheader("Clinical Features")
    
    # Initialize form fields from session state or use defaults
    if 'parsed_patient_data' not in st.session_state:
        st.session_state['parsed_patient_data'] = {}
    
    parsed_data = st.session_state['parsed_patient_data']
    
    # 6 Clinical Features from the dataset
    prior_admissions = st.number_input(
        "Prior Admissions (last 12 months)",
        min_value=0,
        max_value=50,
        value=int(parsed_data.get('prior_admissions', 1)),
        key="prior_admissions_input",
        help="Number of hospital admissions in the past 12 months"
    )
    
    comorbidity_count = st.number_input(
        "Comorbidity Count",
        min_value=0,
        max_value=20,
        value=int(parsed_data.get('comorbidity_count', 3)),
        key="comorbidity_count_input",
        help="Number of co-existing medical conditions"
    )
    
    # Age group with pre-filled value from uploaded file
    default_age_index = 6  # Default to 60-70
    if 'age_group_display' in parsed_data:
        age_options = ["0-10", "10-20", "20-30", "30-40", "40-50", "50-60", "60-70", "70-80", "80-90", "90-100"]
        if parsed_data['age_group_display'] in age_options:
            default_age_index = age_options.index(parsed_data['age_group_display'])
    
    age_group = st.selectbox(
        "Age Group",
        options=["0-10", "10-20", "20-30", "30-40", "40-50", "50-60", "60-70", "70-80", "80-90", "90-100"],
        index=default_age_index,
        key="age_group_input",
        help="Patient age group (mapped to dataset encoding)"
    )
    
    medication_count = st.number_input(
        "Medication Count",
        min_value=0,
        max_value=50,
        value=int(parsed_data.get('num_medications', 5)),
        key="medication_count_input",
        help="Number of medications prescribed"
    )
    
    discharge_diagnosis = st.text_input(
        "Discharge Diagnosis (ICD Code)",
        value=str(parsed_data.get('discharge_diagnosis', "250.01")),
        key="discharge_diagnosis_input",
        help="Primary diagnosis code at discharge (e.g., 250.01 for diabetes)"
    )
    
    # High risk flag with pre-filled value
    default_risk_index = 0
    if 'high_risk_display' in parsed_data:
        default_risk_index = 1 if parsed_data['high_risk_display'] == "Yes" else 0
    
    high_risk_flag = st.selectbox(
        "High Risk Flag",
        options=["No", "Yes"],
        index=default_risk_index,
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
        default=[],
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
    
    # Display input summary
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Input Summary")
        st.json(patient_data)
    
    with col2:
        st.subheader("Selected Symptoms")
        if selected_symptoms:
            for symptom in selected_symptoms:
                st.write(f"• {symptom}")
        else:
            st.caption("No symptoms selected")
    
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
                st.subheader("Risk Assessment Results")
                
                # Risk score display
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    risk_percentage = result['risk_score'] * 100
                    st.metric(
                        "Readmission Risk Score",
                        f"{result['risk_score']:.2f}",
                        delta=f"{risk_percentage:.1f}%"
                    )
                
                with col2:
                    risk_cat = result['risk_category']
                    color_map = {"Low": "green", "Medium": "orange", "High": "red"}
                    st.metric(
                        "Risk Category",
                        risk_cat,
                        delta=None,
                        delta_color="normal"
                    )
                
                with col3:
                    st.metric(
                        "Prediction",
                        result['prediction_label'],
                        delta=None
                    )
                
                # Risk interpretation
                st.markdown("### Risk Interpretation")
                if result['risk_category'] == "Low":
                    st.success("""
                    **Low Risk**: Continue current management plan. 
                    Maintain regular follow-ups with your healthcare provider and adhere to prescribed medications.
                    """)
                elif result['risk_category'] == "Medium":
                    st.warning("""
                    **Medium Risk**: Increased monitoring recommended. 
                    Consider scheduling a follow-up appointment to review your care plan and medication adherence.
                    """)
                else:
                    st.error("""
                    **High Risk**: Urgent attention needed. 
                    Strongly recommend immediate consultation with your healthcare provider to assess potential complications
                    and adjust treatment plan.
                    """)
                
                # SHAP Analysis
                if 'feature_importance' in result and result['feature_importance']:
                    st.markdown("### Key Risk Factors (SHAP Analysis)")
                    
                    importance_df = pd.DataFrame(result['feature_importance'])
                    
                    # Display top factors
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Top Contributing Factors:**")
                        for i, row in importance_df.head(5).iterrows():
                            bar_length = min(row['importance'] * 100, 100)
                            st.markdown(
                                f"""
                                <div style="background-color: #f0f2f6; padding: 5px; margin: 3px 0; border-radius: 3px;">
                                    <strong>{row['feature']}</strong>: {row['importance']:.4f}
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
                                st.write(f"• {f['feature']}")
                        
                        if negative:
                            st.success("**Factors Decreasing Risk:**")
                            for f in negative:
                                st.write(f"• {f['feature']}")
                
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
        # Add user message to history
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
                        # Map symptoms to match what user sees
                        symptom_list = st.session_state.current_symptoms
                        
                        # Determine risk category
                        risk_score = st.session_state.current_risk_score
                        if risk_score < 0.3:
                            risk_category = "Low"
                        elif risk_score < 0.6:
                            risk_category = "Medium"
                        else:
                            risk_category = "High"
                        
                        # Create a summarized patient profile for the AI
                        # Only pass current query + patient profile, NOT full chat history
                        # This prevents infinite loops and repetition
                        patient_profile = {
                            'symptoms': symptom_list,
                            'risk_score': risk_score,
                            'risk_category': risk_category
                        }
                        
                        # Generate advice using Gen AI
                        # Pass only the current user query and summarized patient profile
                        advice = assistant.generate_advice(
                            patient_symptoms=symptom_list,
                            ml_risk_score=risk_score,
                            risk_category=risk_category,
                            additional_info=patient_profile
                        )
                        
                        # Display response
                        st.markdown(advice)
                        
                        # Add to chat history
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
    
    # Context display
    st.markdown("---")
    st.subheader("Current Context")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Risk Score:**")
        if st.session_state.current_risk_score is not None:
            st.metric("ML Risk Score", f"{st.session_state.current_risk_score:.2f}")
        else:
            st.caption("Not calculated yet - visit Tab 1")
    
    with col2:
        st.write("**Reported Symptoms:**")
        if st.session_state.current_symptoms:
            for symptom in st.session_state.current_symptoms:
                st.write(f"• {symptom}")
        else:
            st.caption("None selected")
    
    # Clear chat button
    if st.button("Clear Chat History", use_container_width=False):
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
