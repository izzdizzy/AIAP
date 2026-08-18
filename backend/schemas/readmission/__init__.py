"""
Pydantic Schemas for Hospital Readmission Prediction Module
============================================================

This module defines request/response models for the Hospital Readmission API.
Separated from CAD schemas to avoid conflicts.
"""

from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, field_validator


# =============================================================================
# PREDICTION ENDPOINT MODELS
# =============================================================================

class PatientData(BaseModel):
    """
    Request model for patient data input.
    Accepts any subset of features - missing features will be filled with defaults.
    
    This schema is specific to the Hospital Readmission model and uses
    feature names from the dataset.
    """
    # Core clinical features (commonly provided)
    prior_admissions: Optional[Union[int, str]] = Field(None, description="Number of prior hospital admissions")
    comorbidity_count: Optional[Union[int, str]] = Field(None, description="Number of comorbidities")
    age: Optional[Union[int, str]] = Field(None, description="Patient age in years or bracket e.g. 50-60")
    medication_count: Optional[Union[int, str]] = Field(None, description="Total number of medications")
    num_medications: Optional[Union[int, str]] = Field(None, description="Alias for medication_count")

    @field_validator("age", "prior_admissions", "comorbidity_count", "medication_count", "num_medications", mode="before")
    @classmethod
    def parse_numeric_or_range(cls, v: Any) -> Optional[int]:
        if v is None or v == "":
            return None
        if isinstance(v, (int, float)):
            return int(v)
        if isinstance(v, str):
            v_str = v.strip()
            if "-" in v_str:
                parts = v_str.split("-")
                try:
                    # Take average or midpoint of range like "50-60" -> 55
                    nums = [int(p.strip()) for p in parts if p.strip().isdigit()]
                    if nums:
                        return int(sum(nums) / len(nums))
                except Exception:
                    pass
            try:
                return int(float(v_str))
            except Exception:
                return None
        return None

    def model_post_init(self, __context: Any) -> None:
        if self.medication_count is None and self.num_medications is not None:
            self.medication_count = self.num_medications
    
    # Administrative features
    admission_type_id: Optional[int] = None
    discharge_disposition_id: Optional[int] = None
    admission_source_id: Optional[int] = None
    
    # Hospital stay features
    time_in_hospital: Optional[int] = None
    num_lab_procedures: Optional[int] = None
    num_procedures: Optional[int] = None
    
    # Visit counts
    number_outpatient: Optional[int] = None
    number_emergency: Optional[int] = None
    number_inpatient: Optional[int] = None
    
    # Diagnosis features
    number_diagnoses: Optional[int] = None
    diabetes_diag_count: Optional[int] = None
    
    # Medication features (boolean flags)
    metformin_encoded: Optional[int] = None
    insulin_encoded: Optional[int] = None
    on_insulin: Optional[int] = None
    
    # External risk scores from other modules (0-100 percentage values)
    diabetes_risk_score: Optional[float] = Field(None, description="Diabetes risk score from Diabetes Risk Classifier module (0-100)")
    cad_risk_score: Optional[float] = Field(None, description="Coronary Artery Disease risk score from CAD Risk Assessment module (0-100)")
    
    # Allow additional fields for flexibility
    class Config:
        extra = "allow"


class SHAPValue(BaseModel):
    """Model for individual SHAP value in hospital readmission prediction."""
    feature: str
    importance: float
    shap_value: float


class PredictionResponse(BaseModel):
    """
    Response model for hospital readmission ML prediction endpoint.
    Contains raw probability, severity score, urgency level, and SHAP analysis.
    """
    # Raw model output
    raw_probability: float = Field(..., description="Raw probability from model (0.0-1.0)")
    
    # Clinical Severity Score (0-100 scale with adjustments)
    clinical_severity_score: int = Field(..., description="Clinical Severity Score (0-100)")
    
    # Urgency classification
    urgency_level: str = Field(..., description="Urgency level: Routine Monitoring, Increased Surveillance, or Immediate Intervention")
    risk_category: str = Field(..., description="Risk category: Low, Moderate, or High")
    
    # Binary prediction using optimal threshold
    prediction: int = Field(..., description="Binary prediction (0=Not Readmitted, 1=Readmitted)")
    prediction_label: str = Field(..., description="Human-readable prediction label")
    
    # Clinical adjustment applied
    clinical_adjustment_applied: int = Field(..., description="Points added due to clinical severity rules")
    
    # SHAP analysis
    shap_values: Optional[List[SHAPValue]] = Field(None, description="Top contributing features from SHAP analysis")
    top_positive_features: Optional[List[Dict[str, Any]]] = Field(None, description="Features increasing risk")
    top_negative_features: Optional[List[Dict[str, Any]]] = Field(None, description="Features decreasing risk")
    
    # Model metadata
    threshold_used: float = Field(..., description="Optimal threshold used for binary prediction")


# =============================================================================
# CHAT ENDPOINT MODELS
# =============================================================================

class ChatRequest(BaseModel):
    """
    Request model for Gen AI chat endpoint.
    Includes patient context and user query.
    All fields are Optional with defaults to prevent validation errors from frontend.
    """
    clinical_severity_score: Optional[int] = Field(0, description="Clinical Severity Score (0-100)")
    symptoms: Optional[List[str]] = Field(default_factory=list, description="List of patient-reported symptoms")
    chas_tier: Optional[str] = Field(None, description="CHAS tier: Blue, Orange, Green, or None")
    user_query: Optional[str] = Field("", description="User's question or message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "clinical_severity_score": 75,
                "symptoms": ["fatigue", "frequent urination"],
                "chas_tier": "Blue",
                "user_query": "What should I do about my symptoms?"
            }
        }


class ChatResponse(BaseModel):
    """
    Response model for Gen AI chat endpoint.
    Contains AI-generated advice with safety guardrails.
    """
    response: str = Field(..., description="AI-generated healthcare advice")
    is_fallback: bool = Field(default=False, description="Whether fallback response was used")
    safety_warning: Optional[str] = Field(None, description="Safety warning if dangerous content detected")


# =============================================================================
# FILE UPLOAD ENDPOINT MODELS
# =============================================================================

class UploadResponse(BaseModel):
    """
    Response model for file upload endpoint.
    Returns parsed patient data ready to pre-fill the form.
    """
    success: bool = Field(..., description="Whether upload was successful")
    message: str = Field(..., description="Status message")
    patient_data: Optional[Dict[str, Any]] = Field(None, description="Parsed patient data")
    data_completeness_pct: Optional[float] = Field(None, description="Percentage of key features provided")
    error: Optional[str] = Field(None, description="Error message if upload failed")


# =============================================================================
# MODEL INFO ENDPOINT MODELS
# =============================================================================

class ModelInfoResponse(BaseModel):
    """
    Response model for model info endpoint.
    Contains model metrics and theoretical ceiling citations.
    """
    model_type: str = Field(..., description="Type of ML model")
    feature_count: int = Field(..., description="Number of features used")
    
    # Performance metrics
    roc_auc: Optional[float] = Field(None, description="ROC-AUC score on test set")
    recall: Optional[float] = Field(None, description="Recall at optimal threshold")
    optimal_threshold: Optional[float] = Field(None, description="Optimal threshold for 80%+ recall")
    
    # Theoretical ceiling citations
    theoretical_ceiling: Optional[Dict[str, str]] = Field(
        None, 
        description="Citations for dataset benchmark and theoretical performance limits"
    )
    
    # Training metadata
    training_samples: Optional[int] = Field(None, description="Number of training samples")
    test_samples: Optional[int] = Field(None, description="Number of test samples")
