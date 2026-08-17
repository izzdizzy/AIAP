"""
Diabetes Risk Classifier Router for FastAPI Backend
====================================================

This module defines the FastAPI router for Diabetes Risk Classification endpoints.
Ported from AIAP-PR2-main/backend/main.py to be included in the main app via include_router.

Endpoints:
  GET  /health           - quick check that the API and model are up
  POST /predict          - health profile -> diabetes risk (uses the ML model)
  POST /explain          - health profile -> risk + plain-language explanation
                           (uses the ML model, then the Gen AI explainer)
"""

from fastapi import APIRouter, HTTPException
from typing import Dict

# Import Pydantic models from the diabetes schemas
from backend.schemas.diabetes import (
    HealthProfile,
    PredictionResponse,
    ExplainRequest,
    ExplainResponse,
)

# Import services
from backend.services.diabetes.model_service import DiabetesModel
from backend.services.diabetes.genai_service import generate_explanation


# =============================================================================
# FASTAPI ROUTER
# =============================================================================

router = APIRouter(tags=["Diabetes Risk Classifier"])

# A small dict holds resources loaded at startup (the trained model).
_resources: Dict[str, DiabetesModel] = {}


def get_diabetes_model() -> DiabetesModel:
    """Get or create the diabetes model instance (lazy loading)."""
    if "model" not in _resources:
        _resources["model"] = DiabetesModel()
    return _resources["model"]


# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

@router.get("/health")
async def health_check():
    """Confirms the server is running and the model is loaded."""
    # Ensure model is loaded
    try:
        model = get_diabetes_model()
        return {"status": "ok", "model_loaded": True}
    except Exception as e:
        return {"status": "error", "model_loaded": False, "error": str(e)}


# =============================================================================
# PREDICTION ENDPOINT
# =============================================================================

@router.post("/predict", response_model=PredictionResponse)
async def predict(profile: HealthProfile):
    """Run the trained classifier on one health profile and return the risk."""
    try:
        model = get_diabetes_model()
        # profile is already validated by Pydantic. Convert to a plain dict.
        result = model.predict(profile.model_dump())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


# =============================================================================
# EXPLAIN ENDPOINT
# =============================================================================

@router.post("/explain", response_model=ExplainResponse)
async def explain(request: ExplainRequest):
    """Full flow: predict the risk, then have the Gen AI layer explain it.
    This is the endpoint the app's UI would call to show a user their result."""
    try:
        model = get_diabetes_model()
        profile_dict = request.profile.model_dump()

        # Step 1: get the risk from the ML model.
        prediction = model.predict(profile_dict)

        # Step 2: get a plain-language explanation of that risk from the LLM.
        explanation = generate_explanation(profile_dict, prediction)

        return {"prediction": prediction, "explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")
