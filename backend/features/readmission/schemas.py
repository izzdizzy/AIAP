"""
Pydantic Schemas for Hospital Readmission Prediction Module
"""

from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, field_validator


class PatientData(BaseModel):
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

    admission_type_id: Optional[int] = None
    discharge_disposition_id: Optional[int] = None
    admission_source_id: Optional[int] = None

    time_in_hospital: Optional[int] = None
    num_lab_procedures: Optional[int] = None
    num_procedures: Optional[int] = None

    number_outpatient: Optional[int] = None
    number_emergency: Optional[int] = None
    number_inpatient: Optional[int] = None

    number_diagnoses: Optional[int] = None
    diabetes_diag_count: Optional[int] = None

    metformin_encoded: Optional[int] = None
    insulin_encoded: Optional[int] = None
    on_insulin: Optional[int] = None

    diabetes_risk_score: Optional[float] = Field(None, description="Diabetes risk score (0-100)")
    cad_risk_score: Optional[float] = Field(None, description="CAD risk score (0-100)")

    class Config:
        extra = "allow"


class SHAPValue(BaseModel):
    feature: str
    importance: float
    shap_value: float


class PredictionResponse(BaseModel):
    raw_probability: float = Field(..., description="Raw probability from model (0.0-1.0)")
    clinical_severity_score: int = Field(..., description="Clinical Severity Score (0-100)")
    urgency_level: str = Field(..., description="Urgency level")
    risk_category: str = Field(..., description="Risk category: Low, Moderate, or High")
    prediction: int = Field(..., description="Binary prediction (0 or 1)")
    prediction_label: str = Field(..., description="Human-readable prediction label")
    clinical_adjustment_applied: int = Field(..., description="Points added due to clinical severity rules")
    shap_values: Optional[List[SHAPValue]] = Field(None, description="SHAP analysis")
    top_positive_features: Optional[List[Dict[str, Any]]] = Field(None, description="Features increasing risk")
    top_negative_features: Optional[List[Dict[str, Any]]] = Field(None, description="Features decreasing risk")
    threshold_used: float = Field(..., description="Optimal threshold used")


class ChatRequest(BaseModel):
    clinical_severity_score: Optional[int] = Field(0, description="Clinical Severity Score (0-100)")
    symptoms: Optional[List[str]] = Field(default_factory=list, description="Patient symptoms")
    chas_tier: Optional[str] = Field(None, description="CHAS tier")
    user_query: Optional[str] = Field("", description="User's query")

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
    response: str = Field(..., description="AI-generated healthcare advice")
    is_fallback: bool = Field(default=False, description="Whether fallback response was used")
    safety_warning: Optional[str] = Field(None, description="Safety warning")


class UploadResponse(BaseModel):
    success: bool = Field(..., description="Whether upload was successful")
    message: str = Field(..., description="Status message")
    patient_data: Optional[Dict[str, Any]] = Field(None, description="Parsed patient data")
    data_completeness_pct: Optional[float] = Field(None, description="Percentage of key features provided")
    error: Optional[str] = Field(None, description="Error message if upload failed")


class ModelInfoResponse(BaseModel):
    model_type: str = Field(..., description="Type of ML model")
    feature_count: int = Field(..., description="Number of features used")
    roc_auc: Optional[float] = Field(None, description="ROC-AUC score on test set")
    recall: Optional[float] = Field(None, description="Recall at optimal threshold")
    optimal_threshold: Optional[float] = Field(None, description="Optimal threshold for 80%+ recall")
