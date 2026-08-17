"""
Diabetes Readmission Prediction Router
=======================================

This module defines the FastAPI router for Diabetes Readmission Prediction endpoints.
All routes are prefixed with /api/v1/diabetes to avoid conflicts with CAD routes.

Endpoints:
- POST /api/v1/diabetes/predict - Predict readmission risk
- POST /api/v1/diabetes/chat - Get AI care navigation advice
- POST /api/v1/diabetes/upload - Upload patient data file
- GET /api/v1/diabetes/model-info - Get model information
- GET /api/v1/diabetes/health - Health check
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Optional
import pandas as pd

from backend.schemas.diabetes import (
    DiabetesPatientData,
    DiabetesPredictionResponse,
    DiabetesSHAPValue,
    DiabetesChatRequest,
    DiabetesChatResponse,
    DiabetesUploadResponse,
    DiabetesModelInfoResponse,
)
from backend.services.diabetes.ml_service import get_diabetes_ml_service
from backend.services.diabetes.genai_service import get_diabetes_genai_service


router = APIRouter(prefix="/v1/diabetes", tags=["Diabetes Readmission Prediction"])


# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "module": "diabetes"}


# =============================================================================
# PREDICTION ENDPOINT
# =============================================================================

@router.post("/predict", response_model=DiabetesPredictionResponse)
async def predict_readmission(patient_data: DiabetesPatientData):
    """
    Predict hospital readmission risk for a diabetes patient.
    
    Accepts JSON patient data, runs ML inference, and returns:
    - Raw probability from model
    - Clinical Severity Score (0-100) with adjustments
    - Urgency level classification
    - SHAP values for interpretability
    
    Args:
        patient_data: Patient features (partial data accepted, missing features filled with defaults)
        
    Returns:
        DiabetesPredictionResponse with severity score, urgency level, and SHAP analysis
    """
    try:
        ml_service = get_diabetes_ml_service()
        
        # Convert Pydantic model to dict
        patient_dict = patient_data.model_dump(exclude_unset=True)
        
        # Run prediction
        result = ml_service.predict(patient_dict, return_shap=True)
        
        # Format SHAP values for response
        shap_values = []
        if result.get('shap_values'):
            for sv in result['shap_values']:
                shap_values.append(DiabetesSHAPValue(**sv))
        
        return DiabetesPredictionResponse(
            raw_probability=result['raw_probability'],
            clinical_severity_score=result['clinical_severity_score'],
            urgency_level=result['urgency_level'],
            risk_category=result['risk_category'],
            prediction=result['prediction'],
            prediction_label=result['prediction_label'],
            clinical_adjustment_applied=result['clinical_adjustment_applied'],
            threshold_used=result['threshold_used'],
            shap_values=shap_values if shap_values else None,
            top_positive_features=result.get('top_positive_features'),
            top_negative_features=result.get('top_negative_features')
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=f"Model not available: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


# =============================================================================
# CHAT ENDPOINT
# =============================================================================

@router.post("/chat", response_model=DiabetesChatResponse)
async def chat_with_assistant(chat_request: DiabetesChatRequest):
    """
    Get AI-powered healthcare advice based on diabetes patient context.
    
    Accepts clinical severity score, symptoms, CHAS tier, and user query.
    Returns personalized healthcare advice with Singapore context.
    
    Features:
    - Safety guardrails for dangerous content
    - API failure fallback responses
    - Retry logic with exponential backoff
    
    Args:
        chat_request: DiabetesChatRequest with severity score, symptoms, CHAS tier, and query
        
    Returns:
        DiabetesChatResponse with AI-generated advice
    """
    try:
        genai_service = get_diabetes_genai_service()
        
        # Generate response
        result = genai_service.generate_response(
            clinical_severity_score=chat_request.clinical_severity_score,
            symptoms=chat_request.symptoms,
            chas_tier=chat_request.chas_tier,
            user_query=chat_request.user_query
        )
        
        return DiabetesChatResponse(
            response=result['response'],
            is_fallback=result['is_fallback'],
            safety_warning=result.get('safety_warning')
        )
        
    except Exception as e:
        # CRITICAL: Catch ALL exceptions to prevent 500 errors
        print(f"[Diabetes Router] CHAT ENDPOINT ERROR: {str(e)}")
        return DiabetesChatResponse(
            response="[System Error] Unable to connect to live care navigation. Please follow standard post-discharge protocols. Seek immediate medical attention if symptoms worsen.",
            is_fallback=True,
            safety_warning=None
        )


# =============================================================================
# FILE UPLOAD ENDPOINT
# =============================================================================

@router.post("/upload", response_model=DiabetesUploadResponse)
async def upload_patient_file(file: UploadFile = File(...)):
    """
    Upload and parse patient data from CSV or Excel file.
    
    Accepts CSV or Excel files containing patient data.
    Parses the file, maps columns to model features, and returns
    structured JSON to pre-fill the frontend form.
    
    Args:
        file: Uploaded file (CSV or Excel format)
        
    Returns:
        DiabetesUploadResponse with parsed patient data and completeness metrics
    """
    try:
        # Read file bytes
        file_bytes = await file.read()
        
        # Validate file is not empty
        if not file_bytes or len(file_bytes) == 0:
            raise ValueError("Uploaded file is empty.")
        
        # Parse file based on extension
        filename = file.filename or ""
        if filename.endswith('.csv'):
            df = pd.read_csv(pd.io.common.BytesIO(file_bytes))
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(pd.io.common.BytesIO(file_bytes))
        else:
            raise ValueError("Unsupported file format. Please upload CSV or Excel file.")
        
        # Convert first row to dict (assuming single patient per file)
        parsed_data = df.iloc[0].to_dict()
        
        # Apply default values for expected fields that might be missing from CSV
        defaults = {
            'age': 0,
            'prior_admissions': 0,
            'number_inpatient': 0,
            'number_emergency': 0,
            'number_outpatient': 0,
            'comorbidity_count': 0,
            'medication_count': 0,
            'time_in_hospital': 0,
            'number_diagnoses': 0,
            'num_lab_procedures': 0,
            'num_procedures': 0,
            'admission_type_id': 1,
            'discharge_disposition_id': 1,
            'admission_source_id': 1,
            'diabetes_diag_count': 0,
            'metformin_encoded': 0,
            'insulin_encoded': 0,
            'on_insulin': 0,
        }
        
        # Merge with defaults - user data takes precedence
        patient_data = {**defaults, **parsed_data}
        
        # Convert all numpy/pandas types to native Python types for JSON serialization
        def convert_to_native(obj):
            """Recursively convert numpy/pandas types to native Python types."""
            import json
            if isinstance(obj, dict):
                return {key: convert_to_native(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_native(item) for item in obj]
            elif hasattr(obj, 'item'):  # numpy scalar types
                return obj.item()
            elif pd.isna(obj):  # pandas NaN
                return None
            else:
                return obj
        
        patient_data = convert_to_native(patient_data)
        
        # Calculate data completeness
        key_features = ['prior_admissions', 'comorbidity_count', 'age', 'medication_count', 
                       'time_in_hospital', 'number_diagnoses']
        provided_count = sum(1 for f in key_features if patient_data.get(f) is not None and patient_data.get(f) != 0)
        data_completeness_pct = (provided_count / len(key_features)) * 100 if key_features else 0
        
        return DiabetesUploadResponse(
            success=True,
            message=f"Successfully parsed {filename}",
            patient_data=patient_data,
            data_completeness_pct=data_completeness_pct,
            error=None
        )
        
    except ValueError as e:
        # Return a valid response with defaults even on error
        default_patient_data = {
            'age': 0,
            'prior_admissions': 0,
            'number_inpatient': 0,
            'number_emergency': 0,
            'number_outpatient': 0,
            'comorbidity_count': 0,
            'medication_count': 0,
            'time_in_hospital': 0,
            'number_diagnoses': 0,
            'num_lab_procedures': 0,
            'num_procedures': 0,
            'admission_type_id': 1,
            'discharge_disposition_id': 1,
            'admission_source_id': 1,
            'diabetes_diag_count': 0,
            'metformin_encoded': 0,
            'insulin_encoded': 0,
            'on_insulin': 0,
        }
        return DiabetesUploadResponse(
            success=False,
            message="Failed to parse file",
            patient_data=default_patient_data,
            data_completeness_pct=0,
            error=str(e)
        )
    except Exception as e:
        # Return a valid response with defaults even on unexpected error
        default_patient_data = {
            'age': 0,
            'prior_admissions': 0,
            'number_inpatient': 0,
            'number_emergency': 0,
            'number_outpatient': 0,
            'comorbidity_count': 0,
            'medication_count': 0,
            'time_in_hospital': 0,
            'number_diagnoses': 0,
            'num_lab_procedures': 0,
            'num_procedures': 0,
            'admission_type_id': 1,
            'discharge_disposition_id': 1,
            'admission_source_id': 1,
            'diabetes_diag_count': 0,
            'metformin_encoded': 0,
            'insulin_encoded': 0,
            'on_insulin': 0,
        }
        return DiabetesUploadResponse(
            success=False,
            message="Unexpected error during file processing",
            patient_data=default_patient_data,
            data_completeness_pct=0,
            error=str(e)
        )


# =============================================================================
# MODEL INFO ENDPOINT
# =============================================================================

@router.get("/model-info", response_model=DiabetesModelInfoResponse)
async def get_model_information():
    """
    Get model metadata, performance metrics, and theoretical ceiling citations.
    
    Returns information about the trained model including:
    - Model type and feature count
    - ROC-AUC and recall metrics
    - Optimal threshold for 80%+ recall
    - Dataset benchmark citations
    
    This endpoint allows the frontend to display model transparency information.
    
    Returns:
        DiabetesModelInfoResponse with metrics and citations
    """
    try:
        ml_service = get_diabetes_ml_service()
        info = ml_service.get_model_info()
        
        return DiabetesModelInfoResponse(
            model_type=info['model_type'],
            feature_count=info['feature_count'],
            roc_auc=info.get('roc_auc'),
            recall=info.get('recall'),
            optimal_threshold=info.get('optimal_threshold'),
            theoretical_ceiling=info.get('theoretical_ceiling'),
            training_samples=info.get('training_samples'),
            test_samples=info.get('test_samples')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve model info: {str(e)}")
