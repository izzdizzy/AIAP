"""
Streamlit Dashboard for Hospital Readmission Predictor and Care Navigation Assistant
=====================================================================================

This module implements a unified Streamlit dashboard with two tabs:
1. Patient Risk Assessment - ML-based readmission risk prediction with SHAP visualizations
2. Care Navigation - Gen AI-powered care advice chat interface

Application Flow:
1. User inputs patient symptoms and clinical data in Tab 1
2. ML model processes inputs to output readmission risk score and feature insights
3. User can switch to Tab 2 where Gen AI Care Navigator uses the symptoms and ML output
   to provide contextual, actionable healthcare advice for Singapore patients

Usage:
    streamlit run app.py

Environment Variables:
    GEMINI_API_KEY: Required for Gen AI Care Navigation (Tab 2)
                   Obtain from https://makersuite.google.com/app/apikey
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

import streamlit as st
import pandas as pd
import numpy as np

# Import custom modules
from model import ReadmissionPredictor, predict_readmission_risk
from gen_ai import CareNavigationAssistant


# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

DEFAULT_MODEL_PATH = Path("outputs/readmission_model.joblib")
DEFAULT_FEATURE_COLUMNS_PATH = Path("outputs/feature_columns.json")

# Feature configuration based on UCI Diabetes dataset
FEATURE_CONFIG = {
    "prior_admissions": {
        "label": "Prior Hospital Admissions",
        "type": "number",
        "min_value": 0,
        "max_value": 20,
        "value": 1,
        "help": "Number of previous hospital admissions in the past year"
    },
    "comorbidity_count": {
        "label": "Comorbidity Count",
        "type": "number",
        "min_value": 0,
        "max_value": 15,
        "value": 3,
        "help": "Number of co-existing medical conditions (e.g., hypertension, heart disease)"
    },
    "age": {
        "label": "Age (Years)",
        "type": "number",
        "min_value": 18,
        "max_value": 100,
        "value": 65,
        "help": "Patient's age in years"
    },
    "medication_count": {
        "label": "Number of Medications",
        "type": "number",
        "min_value": 0,
        "max_value": 50,
        "value": 5,
        "help": "Total number of different medications currently prescribed"
    },
    "discharge_diagnosis": {
        "label": "Primary Discharge Diagnosis Code",
        "type": "number",
        "min_value": 0.0,
        "max_value": 999.0,
        "value": 250.01,
        "help": "ICD-9-CM code for primary diagnosis at discharge (e.g., 250.01 for diabetes)"
    },
    "high_risk_flag": {
        "label": "High Risk Flag",
        "type": "select",
        "options": [0, 1],
        "value": 0,
        "help": "Clinical indicator for high-risk patient (1=Yes, 0=No)"
    }
}

# Derived interaction features (auto-calculated)
INTERACTION_FEATURES = [
    "age_comorbidity_interaction",
    "medication_comorbidity_interaction",
    "admissions_comorbidity_interaction",
    "age_medication_interaction"
]

# Symptom options for patient input
SYMPTOM_OPTIONS = [
    "Fatigue or weakness",
    "Frequent urination (polyuria)",
    "Excessive thirst (polydipsia)",
    "Blurred vision",
    "Slow-healing wounds",
    "Numbness or tingling in hands/feet",
    "Unexplained weight loss",
    "Increased hunger",
    "Dry skin",
    "Frequent infections",
    "Darkened skin patches (acanthosis nigricans)",
    "Irritability or mood changes",
    "Nausea or vomiting",
    "Shortness of breath",
    "Chest pain or discomfort",
    "Dizziness or lightheadedness",
    "Confusion or difficulty concentrating",
    "Swelling in legs or feet (edema)"
]


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Hospital Readmission Predictor & Care Navigator",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Hospital Readmission Predictor for Chronic Disease Patients in Singapore"
    }
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def calculate_interaction_features(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate derived interaction features based on base patient inputs.
    
    These interaction terms capture combined effects that improve prediction accuracy.
    
    Args:
        patient_data: Dictionary containing base patient features
        
    Returns:
        Updated dictionary with interaction features added
    """
    data = patient_data.copy()
    
    # Age * Comorbidity interaction
    data["age_comorbidity_interaction"] = data.get("age", 0) * data.get("comorbidity_count", 0)
    
    # Medication * Comorbidity interaction
    data["medication_comorbidity_interaction"] = data.get("medication_count", 0) * data.get("comorbidity_count", 0)
    
    # Prior Admissions * Comorbidity interaction
    data["admissions_comorbidity_interaction"] = data.get("prior_admissions", 0) * data.get("comorbidity_count", 0)
    
    # Age * Medication interaction
    data["age_medication_interaction"] = data.get("age", 0) * data.get("medication_count", 0)
    
    return data


def initialize_session_state() -> None:
    """
    Initialize Streamlit session state variables if not already set.
    """
    if "prediction_result" not in st.session_state:
        st.session_state.prediction_result = None
    
    if "patient_symptoms" not in st.session_state:
        st.session_state.patient_symptoms = []
    
    if "patient_inputs" not in st.session_state:
        st.session_state.patient_inputs = {}
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    if "genai_initialized" not in st.session_state:
        st.session_state.genai_initialized = False
    
    if "genai_assistant" not in st.session_state:
        st.session_state.genai_assistant = None


def load_model_safely() -> Optional[ReadmissionPredictor]:
    """
    Attempt to load the ML model with graceful error handling.
    
    Returns:
        ReadmissionPredictor instance if successful, None otherwise
    """
    try:
        # Check if model file exists
        if not DEFAULT_MODEL_PATH.exists():
            st.warning(
                f"Model file not found at {DEFAULT_MODEL_PATH}. "
                "Please run the training script first to generate the model."
            )
            return None
        
        # Check if feature columns file exists
        if not DEFAULT_FEATURE_COLUMNS_PATH.exists():
            st.warning(
                f"Feature columns file not found at {DEFAULT_FEATURE_COLUMNS_PATH}. "
                "Please run the training script first."
            )
            return None
        
        # Attempt to load the predictor
        predictor = ReadmissionPredictor(
            model_path=DEFAULT_MODEL_PATH,
            feature_columns_path=DEFAULT_FEATURE_COLUMNS_PATH
        )
        return predictor
    
    except FileNotFoundError as e:
        st.error(f"File not found: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Failed to load model: {str(e)}")
        return None


def initialize_genai_assistant() -> Optional[CareNavigationAssistant]:
    """
    Initialize the Gen AI Care Navigation Assistant.
    
    Returns:
        CareNavigationAssistant instance if successful, None otherwise
    """
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        
        if not api_key:
            st.warning(
                "GEMINI_API_KEY environment variable not set. "
                "Gen AI features will be unavailable. "
                "Set the environment variable or add it to your .env file."
            )
            return None
        
        assistant = CareNavigationAssistant(api_key=api_key)
        st.session_state.genai_initialized = True
        st.session_state.genai_assistant = assistant
        return assistant
    
    except ValueError as e:
        st.warning(f"API configuration issue: {str(e)}")
        return None
    except ImportError as e:
        st.error(f"Library not available: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Failed to initialize Gen AI assistant: {str(e)}")
        return None


def display_risk_gauge(risk_score: float) -> None:
    """
    Display a visual gauge for risk score.
    
    Args:
        risk_score: Float between 0 and 1 representing readmission risk
    """
    # Convert to percentage
    risk_percentage = risk_score * 100
    
    # Determine color based on risk level
    if risk_score < 0.3:
        color = "green"
        risk_level = "Low Risk"
    elif risk_score < 0.6:
        color = "orange"
        risk_level = "Medium Risk"
    else:
        color = "red"
        risk_level = "High Risk"
    
    # Create gauge visualization using Streamlit metrics
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.metric(
            label="Readmission Risk Score",
            value=f"{risk_percentage:.1f}%",
            delta=risk_level,
            delta_color="inverse" if risk_score >= 0.6 else "normal"
        )
        
        # Progress bar for visual representation
        st.progress(risk_score, text=f"Risk Level: {risk_level}")


def display_shap_insights(result: Dict[str, Any]) -> None:
    """
    Display SHAP-based feature importance insights.
    
    Args:
        result: Prediction result dictionary containing SHAP values
    """
    st.subheader("Feature Importance Insights")
    
    if "feature_importance" not in result or not result["feature_importance"]:
        st.info("SHAP analysis not available. Ensure SHAP library is installed.")
        return
    
    # Display top contributing features
    top_features = result["feature_importance"][:5]
    
    # Create a DataFrame for display
    df_features = pd.DataFrame(top_features)
    df_features["importance"] = df_features["importance"].round(4)
    df_features["shap_value"] = df_features["shap_value"].round(4)
    
    # Display as a table
    st.dataframe(
        df_features[["feature", "importance", "shap_value"]],
        use_container_width=True,
        hide_index=True
    )
    
    # Visual explanation
    st.caption(
        "**How to interpret:** Positive SHAP values increase readmission risk, "
        "while negative values decrease it. Higher absolute importance means "
        "greater impact on the prediction."
    )
    
    # Display positive and negative contributors
    if "top_positive_features" in result and result["top_positive_features"]:
        with st.expander("View Features Increasing Risk", expanded=False):
            for feat in result["top_positive_features"]:
                st.write(f"- **{feat['feature']}**: +{feat['shap_value']:.4f}")
    
    if "top_negative_features" in result and result["top_negative_features"]:
        with st.expander("View Features Decreasing Risk", expanded=False):
            for feat in result["top_negative_features"]:
                st.write(f"- **{feat['feature']}**: {feat['shap_value']:.4f}")


def render_patient_input_form() -> Dict[str, Any]:
    """
    Render the patient input form with dynamic fields.
    
    Returns:
        Dictionary containing patient input values
    """
    st.subheader("Patient Clinical Data")
    st.markdown("Enter the patient's clinical information below:")
    
    patient_inputs = {}
    
    # Create two columns for better layout
    col1, col2 = st.columns(2)
    
    for idx, (feature, config) in enumerate(FEATURE_CONFIG.items()):
        # Alternate between columns
        column = col1 if idx % 2 == 0 else col2
        
        with column:
            if config["type"] == "number":
                patient_inputs[feature] = st.number_input(
                    label=config["label"],
                    min_value=config["min_value"],
                    max_value=config["max_value"],
                    value=config["value"],
                    step=1 if feature != "discharge_diagnosis" else 0.01,
                    help=config["help"]
                )
            elif config["type"] == "select":
                patient_inputs[feature] = st.selectbox(
                    label=config["label"],
                    options=config["options"],
                    index=config["options"].index(config["value"]) if config["value"] in config["options"] else 0,
                    help=config["help"]
                )
    
    return patient_inputs


def render_symptom_selector() -> List[str]:
    """
    Render multi-select widget for patient symptoms.
    
    Returns:
        List of selected symptom strings
    """
    st.subheader("Patient Symptoms")
    st.markdown("Select all symptoms reported by the patient:")
    
    selected_symptoms = st.multiselect(
        label="Reported Symptoms",
        options=SYMPTOM_OPTIONS,
        default=st.session_state.get("patient_symptoms", []),
        placeholder="Choose symptoms...",
        help="Select multiple symptoms if applicable"
    )
    
    # Update session state
    st.session_state.patient_symptoms = selected_symptoms
    
    return selected_symptoms


def render_prediction_results(result: Dict[str, Any]) -> None:
    """
    Render the ML prediction results in a user-friendly format.
    
    Args:
        result: Dictionary containing prediction results from model
    """
    st.subheader("Prediction Results")
    
    # Display risk gauge
    display_risk_gauge(result["risk_score"])
    
    # Display key metrics in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Risk Category",
            result["risk_category"],
            help="Categorized risk level based on prediction score"
        )
    
    with col2:
        st.metric(
            "Prediction",
            result["prediction_label"],
            help="Binary classification outcome"
        )
    
    with col3:
        st.metric(
            "Confidence",
            f"{(1 - abs(result['risk_score'] - 0.5) * 2) * 100:.1f}%",
            help="Model confidence in the prediction"
        )
    
    # Display SHAP insights
    display_shap_insights(result)
    
    # Store result in session state for use in Tab 2
    st.session_state.prediction_result = result


def render_care_navigation_chat() -> None:
    """
    Render the Gen AI Care Navigation chat interface.
    """
    st.subheader("AI Care Navigation Assistant")
    st.markdown(
        "Get personalized healthcare advice based on your risk assessment. "
        "The assistant considers your symptoms and ML risk score to provide "
        "actionable guidance aligned with Singapore's healthcare system."
    )
    
    # Check if Gen AI is available
    if not st.session_state.genai_initialized:
        assistant = initialize_genai_assistant()
        if assistant is None:
            st.info(
                "To enable AI care navigation advice:\n\n"
                "1. Set the GEMINI_API_KEY environment variable\n"
                "2. Or create a `.streamlit/secrets.toml` file with:\n"
                "   ```\n"
                "   GEMINI_API_KEY = \"your-api-key-here\"\n"
                "   ```\n\n"
                "Get your API key from: https://makersuite.google.com/app/apikey"
            )
            return
    
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Chat input
    prompt = st.chat_input(
        "Ask about your care plan, next steps, or healthcare resources...",
        disabled=st.session_state.prediction_result is None
    )
    
    if prompt:
        # Add user message to chat
        st.session_state.chat_messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Generating personalized advice..."):
                try:
                    assistant = st.session_state.genai_assistant
                    
                    # Get patient data from session state
                    symptoms = st.session_state.patient_symptoms
                    prediction = st.session_state.prediction_result
                    
                    if prediction is None:
                        st.error("Please complete risk assessment first.")
                        return
                    
                    # Generate advice
                    advice = assistant.generate_advice(
                        patient_symptoms=symptoms,
                        ml_risk_score=prediction["risk_score"],
                        risk_category=prediction["risk_category"]
                    )
                    
                    st.markdown(advice)
                    
                    # Add assistant response to chat history
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": advice
                    })
                
                except Exception as e:
                    st.error(f"Failed to generate advice: {str(e)}")
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": "I apologize, but I encountered an error generating advice. Please try again or consult your healthcare provider directly."
                    })


def render_quick_recommendations() -> None:
    """
    Render quick healthcare recommendations based on risk level.
    """
    st.subheader("Quick Recommendations")
    
    if st.session_state.prediction_result is None:
        st.info("Complete the risk assessment to see personalized recommendations.")
        return
    
    risk_score = st.session_state.prediction_result["risk_score"]
    risk_category = st.session_state.prediction_result["risk_category"]
    
    # Contextual recommendations based on risk level
    if risk_category == "Low":
        st.success("**Low Risk** - Continue current management:")
        st.markdown("""
        - ✅ Maintain regular follow-ups with your GP (every 3-6 months)
        - ✅ Continue prescribed medications as directed
        - ✅ Monitor blood glucose levels regularly
        - ✅ Enroll in Healthier SG for preventive care benefits
        - ✅ Check CHAS subsidy eligibility for additional support
        """)
    
    elif risk_category == "Medium":
        st.warning("**Medium Risk** - Increase monitoring:")
        st.markdown("""
        - ⚠️ Schedule a review appointment within 2-4 weeks
        - ⚠️ Review medication adherence with your doctor
        - ⚠️ Consider lifestyle modifications (diet, exercise)
        - ⚠️ Visit polyclinic for subsidized chronic disease management
        - ⚠️ Monitor for any worsening symptoms
        """)
    
    else:  # High Risk
        st.error("**High Risk** - Urgent attention recommended:")
        st.markdown("""
        - 🚨 Schedule urgent follow-up within 1 week
        - 🚨 Assess medication adherence immediately
        - 🚨 Check for potential complications
        - 🚨 Consider specialist referral if needed
        - 🚨 Go to A&E if experiencing severe symptoms
        - 📞 Emergency hotline: 995
        """)


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """
    Main Streamlit application entry point.
    """
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.title("🏥 Hospital Readmission Predictor & Care Navigator")
    st.markdown(
        """
        **For Chronic Disease Patients in Singapore**
        
        This integrated platform combines machine learning risk prediction with 
        AI-powered care navigation to help prevent hospital readmissions and 
        improve health outcomes for diabetic patients.
        """
    )
    
    # Create tabs
    tab1, tab2 = st.tabs([
        "📊 Patient Risk Assessment",
        "💬 Care Navigation"
    ])
    
    # =========================================================================
    # TAB 1: PATIENT RISK ASSESSMENT
    # =========================================================================
    with tab1:
        st.header("Patient Risk Assessment")
        st.markdown(
            "Enter patient clinical data to predict hospital readmission risk. "
            "The ML model analyzes multiple factors to provide a risk score and "
            "explain which features contribute most to the prediction."
        )
        
        st.divider()
        
        # Input section
        with st.container():
            patient_inputs = render_patient_input_form()
            
            st.divider()
            
            symptoms = render_symptom_selector()
        
        st.divider()
        
        # Prediction button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            predict_button = st.button(
                "🔍 Calculate Readmission Risk",
                type="primary",
                use_container_width=True
            )
        
        if predict_button:
            with st.spinner("Analyzing patient data..."):
                # Calculate interaction features
                full_patient_data = calculate_interaction_features(patient_inputs)
                
                # Store inputs in session state
                st.session_state.patient_inputs = full_patient_data
                
                # Load model and make prediction
                predictor = load_model_safely()
                
                if predictor is not None:
                    try:
                        result = predictor.predict(
                            patient_data=full_patient_data,
                            return_shap=True
                        )
                        
                        # Display results
                        render_prediction_results(result)
                        
                        st.success("✅ Risk assessment completed successfully!")
                    
                    except Exception as e:
                        st.error(f"Prediction failed: {str(e)}")
                else:
                    st.info(
                        "⚠️ Model not available. Showing demo results...\n\n"
                        "To enable predictions, please run the training script to generate "
                        "`outputs/readmission_model.joblib` and `outputs/feature_columns.json`."
                    )
                    
                    # Demo mode - show sample results
                    demo_result = {
                        "risk_score": 0.45,
                        "risk_percentage": 45.0,
                        "risk_category": "Medium",
                        "prediction": 0,
                        "prediction_label": "Not Readmitted",
                        "feature_importance": [
                            {"feature": "prior_admissions", "importance": 0.15, "shap_value": 0.12},
                            {"feature": "comorbidity_count", "importance": 0.12, "shap_value": 0.08},
                            {"feature": "age", "importance": 0.10, "shap_value": 0.05},
                            {"feature": "medication_count", "importance": 0.08, "shap_value": 0.03},
                            {"feature": "high_risk_flag", "importance": 0.05, "shap_value": 0.02}
                        ],
                        "top_positive_features": [
                            {"feature": "prior_admissions", "shap_value": 0.12},
                            {"feature": "comorbidity_count", "shap_value": 0.08}
                        ],
                        "top_negative_features": [
                            {"feature": "age", "shap_value": -0.05}
                        ]
                    }
                    render_prediction_results(demo_result)
        
        # Show quick recommendations if prediction exists
        if st.session_state.prediction_result is not None:
            st.divider()
            render_quick_recommendations()
    
    # =========================================================================
    # TAB 2: CARE NAVIGATION
    # =========================================================================
    with tab2:
        st.header("Care Navigation Assistant")
        
        # Prerequisites check
        if st.session_state.prediction_result is None:
            st.info(
                "👈 **Step 1:** Please complete the Patient Risk Assessment in Tab 1 first. "
                "The Care Navigator needs your clinical data and risk score to provide "
                "personalized advice."
            )
        else:
            st.success(
                f"✅ **Risk Assessment Complete:** Your readmission risk is "
                f"**{st.session_state.prediction_result['risk_percentage']:.1f}%** "
                f"({st.session_state.prediction_result['risk_category']} Risk)."
            )
            
            st.divider()
            
            # Display current patient context
            with st.expander("View Your Current Health Profile", expanded=False):
                if st.session_state.patient_inputs:
                    st.write("**Clinical Data:**")
                    for key, value in st.session_state.patient_inputs.items():
                        if key not in INTERACTION_FEATURES:  # Hide derived features
                            st.write(f"- {key.replace('_', ' ').title()}: {value}")
                
                if st.session_state.patient_symptoms:
                    st.write("\n**Reported Symptoms:**")
                    for symptom in st.session_state.patient_symptoms:
                        st.write(f"- {symptom}")
                else:
                    st.write("\n**Reported Symptoms:** None selected")
            
            st.divider()
            
            # Render chat interface
            render_care_navigation_chat()
        
        # Additional resources
        st.divider()
        st.subheader("Singapore Healthcare Resources")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **🏥 Polyclinics**
            - Government-subsidized primary care
            - Chronic disease management
            - [Find nearest polyclinic](https://www.moh.gov.sg)
            """)
        
        with col2:
            st.markdown("""
            **🩺 CHAS Clinics**
            - Subsidized care at participating GPs
            - Check your eligibility
            - [CHAS website](https://www.chas.sg)
            """)
        
        with col3:
            st.markdown("""
            **💚 Healthier SG**
            - Enroll with a dedicated GP
            - Free screenings available
            - [Healthier SG portal](https://www.healthiersg.gov.sg)
            """)
        
        # Emergency notice
        st.warning(
            "**🚨 Emergency:** For life-threatening conditions, call **995** immediately "
            "or go to the nearest Accident & Emergency (A&E) department. "
            "Do not wait for AI-generated advice in emergencies."
        )
    
    # Footer
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: gray; font-size: small;'>
        <p>
        <strong>Disclaimer:</strong> This tool is for informational purposes only and does not 
        constitute medical advice. Always consult qualified healthcare professionals for medical 
        decisions. AI-generated content should be verified with your doctor.
        </p>
        <p>Built for Singapore's chronic disease management | Powered by ML & Generative AI</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
