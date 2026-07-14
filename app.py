"""
app.py - Streamlit Application for Hospital Readmission Prediction

This module provides:
- Patient Risk Assessment tab with dynamic form generation
- Cached model loading for performance
- Interactive risk prediction interface
- Care Navigation tab (placeholder for Phase 3)
- Comprehensive error handling and user feedback
"""

import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import json
from datetime import datetime
import warnings

# Suppress warnings for cleaner UI
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Hospital Readmission Predictor",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def load_model(model_path):
    """
    Load trained model from disk with caching for performance.
    
    Args:
        model_path (str): Path to model directory
        
    Returns:
        tuple: (model, scaler, metadata) or (None, None, None) if loading fails
    """
    try:
        # Load model
        model_file = os.path.join(model_path, 'model.joblib')
        if not os.path.exists(model_file):
            st.error(f"Model file not found: {model_file}")
            return None, None, None
        model = joblib.load(model_file)
        
        # Load scaler
        scaler_file = os.path.join(model_path, 'scaler.joblib')
        if not os.path.exists(scaler_file):
            st.error(f"Scaler file not found: {scaler_file}")
            return None, None, None
        scaler = joblib.load(scaler_file)
        
        # Load metadata
        metadata_file = os.path.join(model_path, 'metadata.json')
        if not os.path.exists(metadata_file):
            st.warning("Metadata file not found, using defaults")
            metadata = {}
        else:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        
        return model, scaler, metadata
    
    except Exception as e:
        st.error(f"Error loading model: {str(e)}")
        return None, None, None


def find_latest_model(models_dir='models'):
    """
    Find the most recently saved model in the models directory.
    
    Args:
        models_dir (str): Directory containing model folders
        
    Returns:
        str or None: Path to latest model directory
    """
    if not os.path.exists(models_dir):
        return None
    
    model_folders = [
        os.path.join(models_dir, folder) 
        for folder in os.listdir(models_dir) 
        if os.path.isdir(os.path.join(models_dir, folder))
    ]
    
    if not model_folders:
        return None
    
    # Sort by modification time, get latest
    latest_model = max(model_folders, key=os.path.getmtime)
    return latest_model


def get_risk_category(probability):
    """
    Categorize risk based on probability threshold.
    
    Args:
        probability (float): Readmission probability (0-1)
        
    Returns:
        tuple: (category, color, description)
    """
    if probability < 0.3:
        return "Low Risk", "green", "Patient has low likelihood of readmission. Standard follow-up care recommended."
    elif probability < 0.6:
        return "Medium Risk", "orange", "Patient has moderate likelihood of readmission. Enhanced monitoring advised."
    else:
        return "High Risk", "red", "Patient has high likelihood of readmission. Intensive intervention required."


def generate_patient_form(feature_names):
    """
    Generate dynamic input form based on model features.
    
    Args:
        feature_names (list): List of feature names from model
        
    Returns:
        dict: User input values
    """
    input_data = {}
    
    # Group features by type for better organization
    demographic_features = []
    clinical_features = []
    medication_features = []
    history_features = []
    other_features = []
    
    for feature in feature_names:
        feature_lower = feature.lower()
        if any(x in feature_lower for x in ['age', 'gender', 'sex', 'race', 'ethnicity']):
            demographic_features.append(feature)
        elif any(x in feature_lower for x in ['comorbidity', 'chronic', 'diagnosis', 'condition', 'lab', 'blood', 'test', 'hba1c', 'creatinine', 'cholesterol', 'pressure', 'bmi', 'weight', 'height']):
            clinical_features.append(feature)
        elif any(x in feature_lower for x in ['medication', 'drug', 'prescription', 'polypharmacy']):
            medication_features.append(feature)
        elif any(x in feature_lower for x in ['admission', 'previous', 'history', 'prior', 'readmit']):
            history_features.append(feature)
        else:
            other_features.append(feature)
    
    # Demographics section
    st.subheader("Demographics")
    for feature in demographic_features:
        if 'age' in feature.lower():
            input_data[feature] = st.number_input(
                f"{feature.replace('_', ' ').title()}",
                min_value=0,
                max_value=120,
                value=65,
                step=1,
                key=f"input_{feature}"
            )
        elif 'gender' in feature.lower() or 'sex' in feature.lower():
            input_data[feature] = st.selectbox(
                f"{feature.replace('_', ' ').title()}",
                options=['Male', 'Female', 'Other'],
                key=f"input_{feature}"
            )
        else:
            input_data[feature] = st.text_input(
                f"{feature.replace('_', ' ').title()}",
                value="",
                key=f"input_{feature}"
            )
    
    # Clinical Features section
    if clinical_features:
        st.subheader("Clinical Information")
        for feature in clinical_features:
            if any(x in feature.lower() for x in ['comorbidity', 'chronic', 'condition']):
                input_data[feature] = st.checkbox(
                    f"{feature.replace('_', ' ').title()}",
                    value=False,
                    key=f"input_{feature}"
                )
            elif any(x in feature.lower() for x in ['lab', 'blood', 'test', 'hba1c', 'creatinine', 'cholesterol']):
                input_data[feature] = st.number_input(
                    f"{feature.replace('_', ' ').title()}",
                    min_value=0.0,
                    max_value=10000.0,
                    value=0.0,
                    step=0.1,
                    key=f"input_{feature}"
                )
            else:
                input_data[feature] = st.number_input(
                    f"{feature.replace('_', ' ').title()}",
                    min_value=0.0,
                    max_value=10000.0,
                    value=0.0,
                    step=0.1,
                    key=f"input_{feature}"
                )
    
    # Medication section
    if medication_features:
        st.subheader("Medications")
        for feature in medication_features:
            if any(x in feature.lower() for x in ['polypharmacy', 'count', 'total']):
                input_data[feature] = st.number_input(
                    f"{feature.replace('_', ' ').title()}",
                    min_value=0,
                    max_value=50,
                    value=0,
                    step=1,
                    key=f"input_{feature}"
                )
            else:
                input_data[feature] = st.checkbox(
                    f"{feature.replace('_', ' ').title()}",
                    value=False,
                    key=f"input_{feature}"
                )
    
    # Medical History section
    if history_features:
        st.subheader("Medical History")
        for feature in history_features:
            if any(x in feature.lower() for x in ['admission', 'previous', 'prior', 'count', 'total']):
                input_data[feature] = st.number_input(
                    f"{feature.replace('_', ' ').title()}",
                    min_value=0,
                    max_value=50,
                    value=0,
                    step=1,
                    key=f"input_{feature}"
                )
            else:
                input_data[feature] = st.checkbox(
                    f"{feature.replace('_', ' ').title()}",
                    value=False,
                    key=f"input_{feature}"
                )
    
    # Other features section
    if other_features:
        st.subheader("Additional Information")
        for feature in other_features:
            # Try to infer the type of input needed
            if 'is_' in feature.lower() or 'has_' in feature.lower():
                input_data[feature] = st.checkbox(
                    f"{feature.replace('_', ' ').title()}",
                    value=False,
                    key=f"input_{feature}"
                )
            else:
                input_data[feature] = st.number_input(
                    f"{feature.replace('_', ' ').title()}",
                    min_value=0.0,
                    max_value=10000.0,
                    value=0.0,
                    step=0.1,
                    key=f"input_{feature}"
                )
    
    return input_data


def create_sample_input(feature_names):
    """
    Create a sample input dictionary for testing/demo purposes.
    
    Args:
        feature_names (list): List of feature names
        
    Returns:
        dict: Sample input data
    """
    sample_data = {}
    for feature in feature_names:
        feature_lower = feature.lower()
        if 'age' in feature_lower:
            sample_data[feature] = 72
        elif 'gender_male' in feature_lower or 'sex_male' in feature_lower:
            sample_data[feature] = 1
        elif 'gender_female' in feature_lower or 'sex_female' in feature_lower:
            sample_data[feature] = 0
        elif any(x in feature_lower for x in ['comorbidity', 'chronic', 'condition', 'is_', 'has_']):
            sample_data[feature] = 1 if np.random.random() > 0.5 else 0
        elif any(x in feature_lower for x in ['count', 'total', 'number', 'previous']):
            sample_data[feature] = np.random.randint(0, 5)
        else:
            sample_data[feature] = np.random.uniform(0, 100)
    
    return sample_data


def main():
    """Main application function."""
    
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.5rem;
            color: #2c3e50;
            margin-top: 2rem;
        }
        .risk-box {
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
            text-align: center;
        }
        .risk-low {
            background-color: #d4edda;
            border: 2px solid #28a745;
        }
        .risk-medium {
            background-color: #fff3cd;
            border: 2px solid #ffc107;
        }
        .risk-high {
            background-color: #f8d7da;
            border: 2px solid #dc3545;
        }
        .metric-card {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<div class="main-header">🏥 Hospital Readmission Predictor</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Create tabs
    tab1, tab2 = st.tabs(["Patient Risk Assessment", "Care Navigation"])
    
    # Tab 1: Patient Risk Assessment
    with tab1:
        st.markdown("### Assess Patient Readmission Risk")
        st.write("Enter patient information below to predict the likelihood of hospital readmission within 30 days.")
        
        # Sidebar for model selection
        with st.sidebar:
            st.header("Model Configuration")
            
            # Find and load model
            models_dir = 'models'
            model_path = st.text_input(
                "Model Path",
                value=find_latest_model(models_dir) or "",
                help="Path to the trained model directory"
            )
            
            if st.button("Load Model"):
                with st.spinner("Loading model..."):
                    model, scaler, metadata = load_model(model_path)
                    if model is not None:
                        st.success("Model loaded successfully!")
                        st.session_state['model_loaded'] = True
                        st.session_state['model'] = model
                        st.session_state['scaler'] = scaler
                        st.session_state['metadata'] = metadata
                    else:
                        st.error("Failed to load model")
                        st.session_state['model_loaded'] = False
            
            # Display model info if loaded
            if st.session_state.get('model_loaded', False):
                st.subheader("Model Information")
                metadata = st.session_state.get('metadata', {})
                if metadata:
                    st.info(f"Created: {metadata.get('created_at', 'Unknown')}")
                    if 'training_metrics' in metadata:
                        metrics = metadata['training_metrics']
                        st.metric("ROC-AUC", f"{metrics.get('roc_auc', 'N/A'):.4f}" if isinstance(metrics.get('roc_auc'), float) else metrics.get('roc_auc', 'N/A'))
                        st.metric("Accuracy", f"{metrics.get('accuracy', 'N/A'):.4f}" if isinstance(metrics.get('accuracy'), float) else metrics.get('accuracy', 'N/A'))
        
        # Main content area
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Check if model is loaded
            if not st.session_state.get('model_loaded', False):
                st.warning("⚠️ Please load a model from the sidebar to begin predictions.")
                
                # Demo mode option
                if st.button("Use Demo Mode"):
                    # Create demo data for demonstration
                    st.info("Demo mode activated with sample features")
                    demo_features = [
                        'age', 'is_elderly', 'previous_admissions', 'total_comorbidities',
                        'polypharmacy', 'prolonged_stay', 'frequent_admitter'
                    ]
                    st.session_state['demo_mode'] = True
                    st.session_state['demo_features'] = demo_features
            else:
                # Get feature names from loaded model
                metadata = st.session_state.get('metadata', {})
                feature_names = metadata.get('feature_names', [])
                
                if not feature_names:
                    st.error("No feature names found in model metadata")
                    st.stop()
                
                st.session_state['demo_mode'] = False
                
                # Generate input form
                with st.form("patient_input_form"):
                    st.subheader("Patient Information")
                    
                    # Create organized sections for input
                    input_data = {}
                    
                    # Key clinical features (common across most datasets)
                    st.markdown("**Demographics**")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        input_data['age'] = st.number_input("Age", min_value=0, max_value=120, value=65, step=1)
                    with col_b:
                        gender = st.selectbox("Gender", options=['Male', 'Female'])
                        input_data['gender_Male'] = 1 if gender == 'Male' else 0
                        input_data['gender_Female'] = 1 if gender == 'Female' else 0
                    
                    st.markdown("**Clinical History**")
                    col_c, col_d = st.columns(2)
                    with col_c:
                        input_data['previous_admissions'] = st.number_input("Previous Admissions (last 12 months)", min_value=0, max_value=50, value=0, step=1)
                        input_data['total_comorbidities'] = st.number_input("Number of Comorbidities", min_value=0, max_value=20, value=0, step=1)
                    with col_d:
                        input_data['length_of_stay'] = st.number_input("Length of Stay (days)", min_value=0.0, max_value=365.0, value=5.0, step=0.5)
                        input_data['total_medications'] = st.number_input("Number of Medications", min_value=0, max_value=50, value=0, step=1)
                    
                    st.markdown("**Risk Factors**")
                    col_e, col_f = st.columns(2)
                    with col_e:
                        input_data['is_elderly'] = 1 if st.checkbox("Elderly (≥65 years)", value=True) else 0
                        input_data['has_diabetes'] = 1 if st.checkbox("Diabetes") else 0
                        input_data['has_hypertension'] = 1 if st.checkbox("Hypertension") else 0
                    with col_f:
                        input_data['has_heart_disease'] = 1 if st.checkbox("Heart Disease") else 0
                        input_data['has_copd'] = 1 if st.checkbox("COPD") else 0
                        input_data['has_ckd'] = 1 if st.checkbox("Chronic Kidney Disease") else 0
                    
                    # Add remaining features as numeric inputs
                    additional_features = [f for f in feature_names if f not in input_data.keys() and f not in ['gender_Male', 'gender_Female']]
                    if additional_features:
                        st.markdown("**Additional Features**")
                        for feature in additional_features[:10]:  # Limit to first 10 to avoid overwhelming UI
                            if any(x in feature.lower() for x in ['is_', 'has_', 'comorbidity', 'chronic']):
                                input_data[feature] = 1 if st.checkbox(feature.replace('_', ' ').title(), value=False) else 0
                            else:
                                input_data[feature] = st.number_input(feature.replace('_', ' ').title(), min_value=0.0, value=0.0, step=0.1)
                    
                    submit_button = st.form_submit_button("Predict Readmission Risk", use_container_width=True)
                
                if submit_button:
                    with st.spinner("Analyzing patient risk..."):
                        try:
                            model = st.session_state['model']
                            scaler = st.session_state['scaler']
                            
                            # Prepare input data
                            input_df = pd.DataFrame([input_data])
                            
                            # Ensure all features are present
                            for feature in feature_names:
                                if feature not in input_df.columns:
                                    input_df[feature] = 0
                            
                            # Reorder columns to match training data
                            input_df = input_df[feature_names]
                            
                            # Scale features
                            input_scaled = scaler.transform(input_df)
                            
                            # Make prediction
                            prediction = model.predict(input_scaled)[0]
                            probability = model.predict_proba(input_scaled)[0][1]
                            
                            # Get risk category
                            risk_category, risk_color, risk_description = get_risk_category(probability)
                            
                            # Display results
                            st.markdown("---")
                            st.subheader("Prediction Results")
                            
                            # Main result display
                            result_col1, result_col2, result_col3 = st.columns(3)
                            
                            with result_col1:
                                st.metric(
                                    "Readmission Probability",
                                    f"{probability:.2%}"
                                )
                            
                            with result_col2:
                                st.metric(
                                    "Risk Category",
                                    risk_category
                                )
                            
                            with result_col3:
                                st.metric(
                                    "Prediction",
                                    "Will Readmit" if prediction == 1 else "Won't Readmit"
                                )
                            
                            # Detailed risk assessment
                            risk_class = f"risk-{risk_category.lower().replace(' ', '-')}"
                            st.markdown(f"""
                                <div class="risk-box {risk_class}">
                                    <h3>{risk_category}</h3>
                                    <p><strong>Probability:</strong> {probability:.2%}</p>
                                    <p>{risk_description}</p>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Feature contribution (if SHAP available)
                            if hasattr(model, 'feature_importances_'):
                                st.markdown("### Top Risk Factors")
                                importance_df = pd.DataFrame({
                                    'Feature': feature_names,
                                    'Importance': model.feature_importances_
                                }).sort_values('Importance', ascending=False).head(10)
                                
                                st.bar_chart(importance_df.set_index('Feature'))
                            
                        except Exception as e:
                            st.error(f"Error during prediction: {str(e)}")
                            st.exception(e)
        
        with col2:
            # Information panel
            st.markdown("### About This Tool")
            st.info("""
            This ML-powered tool predicts the likelihood of hospital readmission within 30 days for patients with chronic diseases.
            
            **Key Features:**
            - XGBoost-based prediction model
            - Optimized for Singapore healthcare context
            - Handles class imbalance with SMOTE
            - Interpretable with SHAP analysis
            
            **Intended Use:**
            - Support clinical decision-making
            - Identify high-risk patients early
            - Guide resource allocation
            - NOT a replacement for clinical judgment
            """)
            
            st.markdown("### Quick Stats")
            if st.session_state.get('model_loaded', False):
                metadata = st.session_state.get('metadata', {})
                if 'training_metrics' in metadata:
                    metrics = metadata['training_metrics']
                    st.markdown(f"""
                    <div class="metric-card">
                        <strong>Model Performance:</strong><br>
                        • ROC-AUC: {metrics.get('roc_auc', 'N/A'):.4f}<br>
                        • Accuracy: {metrics.get('accuracy', 'N/A'):.4f}<br>
                        • Precision: {metrics.get('precision', 'N/A'):.4f}<br>
                        • Recall: {metrics.get('recall', 'N/A'):.4f}
                    </div>
                    """, unsafe_allow_html=True)
    
    # Tab 2: Care Navigation (Placeholder for Phase 3)
    with tab2:
        st.markdown("### Care Navigation Assistant")
        st.write("Get personalized care recommendations and navigate Singapore's healthcare system.")
        
        st.info("""
        **Coming Soon!**
        
        This feature will provide:
        - AI-powered care navigation assistant
        - Personalized recommendations based on risk profile
        - Guidance on CHAS tiers and subsidies
        - Polyclinic and specialist routing
        - Healthier SG enrollment information
        - Medication adherence support
        
        Please check back after Phase 3 deployment.
        """)
        
        # Placeholder for future Gen AI integration
        st.markdown("---")
        st.markdown("#### Quick Links (Singapore Healthcare)")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            - [Ministry of Health (MOH)](https://www.moh.gov.sg/)
            - [HealthHub](https://www.healthhub.sg/)
            - [CHAS Information](https://www.chas.sg/)
            """)
        with col2:
            st.markdown("""
            - [Healthier SG](https://www.healthier.sg/)
            - [Polyclinic Locator](https://www.nhgp.com.sg/)
            - [Emergency Services](tel:995)
            """)


if __name__ == "__main__":
    # Initialize session state
    if 'model_loaded' not in st.session_state:
        st.session_state['model_loaded'] = False
    if 'model' not in st.session_state:
        st.session_state['model'] = None
    if 'scaler' not in st.session_state:
        st.session_state['scaler'] = None
    if 'metadata' not in st.session_state:
        st.session_state['metadata'] = {}
    if 'demo_mode' not in st.session_state:
        st.session_state['demo_mode'] = False
    
    main()
