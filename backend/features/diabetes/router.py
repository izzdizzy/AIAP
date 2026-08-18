from fastapi import APIRouter, HTTPException
from typing import Dict

from .schemas import (
    HealthProfile,
    PredictionResponse,
    ExplainRequest,
    ExplainResponse,
)
from .model_service import DiabetesModel
from .genai_service import generate_explanation
from ...services.genai import get_diabetes_explainer_service, build_unified_context

router = APIRouter(tags=["Diabetes Risk Classifier"])

_resources: Dict[str, DiabetesModel] = {}


def get_diabetes_model() -> DiabetesModel:
    if "model" not in _resources:
        _resources["model"] = DiabetesModel()
    return _resources["model"]


@router.get("/health")
async def health_check():
    try:
        get_diabetes_model()
        return {"status": "ok", "model_loaded": True}
    except Exception as e:
        return {"status": "error", "model_loaded": False, "error": str(e)}


@router.post("/predict", response_model=PredictionResponse)
async def predict(profile: HealthProfile):
    try:
        model = get_diabetes_model()
        result = model.predict(profile.model_dump())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/explain", response_model=ExplainResponse)
async def explain(request: ExplainRequest):
    try:
        model = get_diabetes_model()
        profile_dict = request.profile.model_dump()
        prediction = model.predict(profile_dict)
        
        context = build_unified_context({
            "profile": profile_dict,
            "prediction": prediction
        })
        service = get_diabetes_explainer_service()
        genai_res = service.generate_explanation(context=context)
        explanation = genai_res.get("message", "")
        return {"prediction": prediction, "explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")
