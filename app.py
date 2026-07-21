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


# =============================================================================
# SIDEBAR - PATIENT INFORMATION
# =============================================================================

with st.sidebar:
    st.header("Patient Information")
    st.markdown("---")
    
    st.subheader("Clinical Features")
    
    # 6 Clinical Features from the dataset
    prior_admissions = st.number_input(
        "Prior Admissions (last 12 months)",
        min_value=0,
        max_value=50,
        value=1,
        help="Number of hospital admissions in the past 12 months"
    )
    
    comorbidity_count = st.number_input(
        "Comorbidity Count",
        min_value=0,
        max_value=20,
        value=3,
        help="Number of co-existing medical conditions"
    )
    
    age_group = st.selectbox(
        "Age Group",
        options=["0-10", "10-20", "20-30", "30-40", "40-50", "50-60", "60-70", "70-80", "80-90", "90-100"],
        index=6,
        help="Patient age group (mapped to dataset encoding)"
    )
    
    medication_count = st.number_input(
        "Medication Count",
        min_value=0,
        max_value=50,
        value=5,
        help="Number of medications prescribed"
    )
    
    discharge_diagnosis = st.text_input(
        "Discharge Diagnosis (ICD Code)",
        value="250.01",
        help="Primary diagnosis code at discharge (e.g., 250.01 for diabetes)"
    )
    
    high_risk_flag = st.selectbox(
        "High Risk Flag",
        options=["No", "Yes"],
        index=0,
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
    
    # Build patient data dictionary matching training features
    patient_data = {
        'prior_admissions': prior_admissions,
        'comorbidity_count': comorbidity_count,
        'age': age_encoded,
        'medication_count': medication_count,
        'discharge_diagnosis': diagnosis_float,
        'age_comorbidity_interaction': age_comorbidity_interaction,
        'medication_comorbidity_interaction': medication_comorbidity_interaction,
        'admissions_comorbidity_interaction': admissions_comorbidity_interaction,
        'age_medication_interaction': age_medication_interaction,
        'high_risk_flag': 1 if high_risk_flag == "Yes" else 0
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
                        
                        # Generate advice using Gen AI
                        advice = assistant.generate_advice(
                            patient_symptoms=symptom_list,
                            ml_risk_score=risk_score,
                            risk_category=risk_category
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
