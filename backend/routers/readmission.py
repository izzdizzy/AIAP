"""
Readmission Router for Hospital Readmission Prediction API
===========================================================

This module defines the FastAPI router for Hospital Readmission Prediction endpoints.
Ported from my_original/backend/main.py to be included in the main app via include_router.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Optional
import os
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd

# Import Pydantic models from the readmission schemas
from backend.schemas.readmission import (
    PatientData,
    PredictionResponse,
    SHAPValue,
    ChatRequest,
    ChatResponse,
    UploadResponse,
    ModelInfoResponse,
)

# Import services from the new locations
from backend.services.readmission.ml_service import get_ml_service, MLService
from backend.services.readmission.genai_service import get_genai_service, GenAIService
from backend.utils.readmission_utils import parse_uploaded_file_bytes


# =============================================================================
# FASTAPI ROUTER
# =============================================================================

router = APIRouter(tags=["Hospital Readmission"])


# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}


# =============================================================================
# PREDICTION ENDPOINT
# =============================================================================

@router.post("/api/predict", response_model=PredictionResponse)
async def predict_readmission(patient_data: PatientData):
    """
    Predict hospital readmission risk for a patient.
    
    Accepts JSON patient data, runs ML inference, and returns:
    - Raw probability from model
    - Clinical Severity Score (0-100) with adjustments
    - Urgency level classification
    - SHAP values for interpretability
    
    Args:
        patient_data: Patient features (partial data accepted, missing features filled with defaults)
        
    Returns:
        PredictionResponse with severity score, urgency level, and SHAP analysis
    """
    try:
        ml_service = get_ml_service()
        
        # Convert Pydantic model to dict
        patient_dict = patient_data.model_dump(exclude_unset=True)
        
        # Run prediction
        result = ml_service.predict(patient_dict, return_shap=True)
        
        # Format SHAP values for response
        shap_values = []
        if result.get('shap_values'):
            for sv in result['shap_values']:
                shap_values.append(SHAPValue(**sv))
        
        return PredictionResponse(
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

@router.post("/api/chat", response_model=ChatResponse)
async def chat_with_assistant(chat_request: ChatRequest):
    """
    Get AI-powered healthcare advice based on patient context.
    
    Accepts clinical severity score, symptoms, CHAS tier, and user query.
    Returns personalized healthcare advice with Singapore context.
    
    Features:
    - Safety guardrails for dangerous content
    - API failure fallback responses
    - Retry logic with exponential backoff
    
    Args:
        chat_request: ChatRequest with severity score, symptoms, CHAS tier, and query
        
    Returns:
        ChatResponse with AI-generated advice
    """
    try:
        genai_service = get_genai_service()
        
        # Generate response
        result = genai_service.generate_response(
            clinical_severity_score=chat_request.clinical_severity_score,
            symptoms=chat_request.symptoms,
            chas_tier=chat_request.chas_tier,
            user_query=chat_request.user_query
        )
        
        return ChatResponse(
            response=result['response'],
            is_fallback=result['is_fallback'],
            safety_warning=result.get('safety_warning')
        )
        
    except Exception as e:
        # CRITICAL: Catch ALL exceptions to prevent 500 errors
        # Log the exact error and return fallback response instead of crashing
        print(f"CHAT ENDPOINT ERROR: {str(e)}")
        return ChatResponse(
            response="[System Error] Unable to connect to live care navigation. Please follow standard post-discharge protocols. Seek immediate medical attention if symptoms worsen.",
            is_fallback=True,
            safety_warning=None
        )


# =============================================================================
# FILE UPLOAD ENDPOINT
# =============================================================================

@router.post("/api/upload", response_model=UploadResponse)
async def upload_patient_file(file: UploadFile = File(...)):
    """
    Upload and parse patient data from CSV or Excel file.
    
    Accepts CSV or Excel files containing patient data.
    Parses the file, maps columns to model features, and returns
    structured JSON to pre-fill the frontend form.
    
    Args:
        file: Uploaded file (CSV or Excel format)
        
    Returns:
        UploadResponse with parsed patient data and completeness metrics
    """
    try:
        # Read file bytes
        file_bytes = await file.read()
        
        # Validate file is not empty
        if not file_bytes or len(file_bytes) == 0:
            raise ValueError("Uploaded file is empty.")
        
        # Parse file using utility function
        parsed_data = parse_uploaded_file_bytes(file_bytes, file.filename)
        
        # Remove internal fields before returning
        patient_data = {k: v for k, v in parsed_data.items() 
                       if k not in ['data_completeness_pct', 'is_low_completeness', 
                                   'age_group_display', 'high_risk_display', 'symptoms_list']}
        
        # Convert all numpy/pandas types to native Python types for JSON serialization
        # This prevents PydanticSerializationError with numpy.int64, numpy.float64, etc.
        # Also apply default values for missing columns to prevent React crashes
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
        
        # Apply default values for expected fields that might be missing from CSV
        # This ensures the frontend never receives undefined/null for critical fields
        defaults = {
            'age_numeric': 0,
            'total_prior_admissions': 0,
            'number_inpatient': 0,
            'number_emergency': 0,
            'number_outpatient': 0,
            'comorbidity_count': 0,
            'total_medications': 0,
            'num_medications': 0,
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
            'age_group_display': 'Unknown',
            'symptoms_list': []
        }
        
        # Merge with defaults - user data takes precedence
        patient_data = {**defaults, **patient_data}
        
        return UploadResponse(
            success=True,
            message=f"Successfully parsed {file.filename}",
            patient_data=patient_data,
            data_completeness_pct=parsed_data.get('data_completeness_pct'),
            error=None
        )
        
    except ValueError as e:
        # Return a valid response with defaults even on error
        default_patient_data = {
            'age_numeric': 0,
            'total_prior_admissions': 0,
            'number_inpatient': 0,
            'number_emergency': 0,
            'number_outpatient': 0,
            'comorbidity_count': 0,
            'total_medications': 0,
            'num_medications': 0,
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
            'age_group_display': 'Unknown',
            'symptoms_list': []
        }
        return UploadResponse(
            success=False,
            message="Failed to parse file",
            patient_data=default_patient_data,
            data_completeness_pct=0,
            error=str(e)
        )
    except Exception as e:
        # Return a valid response with defaults even on unexpected error
        default_patient_data = {
            'age_numeric': 0,
            'total_prior_admissions': 0,
            'number_inpatient': 0,
            'number_emergency': 0,
            'number_outpatient': 0,
            'comorbidity_count': 0,
            'total_medications': 0,
            'num_medications': 0,
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
            'age_group_display': 'Unknown',
            'symptoms_list': []
        }
        return UploadResponse(
            success=False,
            message="Unexpected error during file processing",
            patient_data=default_patient_data,
            data_completeness_pct=0,
            error=str(e)
        )


# =============================================================================
# MODEL INFO ENDPOINT
# =============================================================================

@router.get("/api/model-info", response_model=ModelInfoResponse)
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
        ModelInfoResponse with metrics and citations
    """
    try:
        ml_service = get_ml_service()
        info = ml_service.get_model_info()
        
        return ModelInfoResponse(
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
