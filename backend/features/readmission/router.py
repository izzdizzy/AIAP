"""
Readmission Router for Hospital Readmission Prediction API
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Optional
import os
from pathlib import Path
import pandas as pd

from .schemas import (
    PatientData,
    PredictionResponse,
    SHAPValue,
    ChatRequest,
    ChatResponse,
    UploadResponse,
    ModelInfoResponse,
)
from .ml_service import get_ml_service, MLService
from .genai_service import get_genai_service, GenAIService
from .utils import parse_uploaded_file_bytes

router = APIRouter(tags=["Hospital Readmission"])


@router.get("/health")
async def health_check():
    return {"status": "healthy"}


@router.post("/api/predict", response_model=PredictionResponse)
async def predict_readmission(patient_data: PatientData):
    try:
        ml_service = get_ml_service()
        patient_dict = patient_data.model_dump(exclude_unset=True)
        result = ml_service.predict(patient_dict, return_shap=True)

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
        raise HTTPException(
            status_code=503,
            detail=f"ML Model unavailable: {str(e)}. Please run model training first."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


@router.post("/api/chat", response_model=ChatResponse)
async def chat_readmission(request: ChatRequest):
    try:
        genai_service = get_genai_service()
        result = genai_service.generate_response(
            clinical_severity_score=request.clinical_severity_score or 0,
            symptoms=request.symptoms or [],
            chas_tier=request.chas_tier,
            user_query=request.user_query or ""
        )

        return ChatResponse(
            response=result['response'],
            is_fallback=result.get('is_fallback', False),
            safety_warning=result.get('safety_warning')
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat generation failed: {str(e)}"
        )


@router.post("/api/upload", response_model=UploadResponse)
async def upload_patient_file(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        extracted_data = parse_uploaded_file_bytes(file_bytes, file.filename or "uploaded.csv")

        completeness_pct = extracted_data.get('data_completeness_pct', 0.0)
        warning_msg = ""
        if extracted_data.get('is_low_completeness', False):
            warning_msg = " Warning: Low data completeness (< 20%). Missing features will be filled with defaults."

        return UploadResponse(
            success=True,
            message=f"Successfully processed {file.filename}.{warning_msg}",
            patient_data=extracted_data,
            data_completeness_pct=completeness_pct,
            error=None
        )

    except ValueError as e:
        return UploadResponse(
            success=False,
            message=f"Failed to process file: {str(e)}",
            patient_data=None,
            data_completeness_pct=None,
            error=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File upload processing failed: {str(e)}"
        )


@router.get("/api/model-info", response_model=ModelInfoResponse)
async def get_model_info():
    try:
        ml_service = get_ml_service()
        info = ml_service.get_model_info()

        return ModelInfoResponse(
            model_type=info.get('model_type', 'XGBClassifier'),
            feature_count=info.get('feature_count', 82),
            roc_auc=info.get('roc_auc'),
            recall=info.get('recall'),
            optimal_threshold=info.get('optimal_threshold')
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve model info: {str(e)}"
        )
