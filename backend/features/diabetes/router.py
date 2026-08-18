from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List

from sqlalchemy.orm import Session

from .schemas import (
    HealthProfile,
    PredictionResponse,
    ExplainRequest,
    ExplainResponse,
)
from .model_service import DiabetesModel
from .genai_service import generate_explanation
from .history_models import DiabetesAssessment
from .history_schemas import DiabetesHistoryCreate, DiabetesHistoryOut
from ...core.db import get_db
from ...core.security import get_current_user
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


# =============================================================================
# ASSESSMENT HISTORY (account-scoped)
# =============================================================================

def _row_to_history_out(row: DiabetesAssessment) -> DiabetesHistoryOut:
    return DiabetesHistoryOut(
        id=row.id,
        created_at=row.created_at,
        risk_label=row.risk_label,
        risk_probability=row.risk_probability,
        risk_band=row.risk_band,
        top_factors=row.top_factors or [],
        profile=row.input_profile or {}
    )


@router.post("/history", response_model=DiabetesHistoryOut, status_code=201)
def save_history(
    payload: DiabetesHistoryCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        model = get_diabetes_model()
        profile_dict = payload.profile.model_dump()
        # Recompute server-side; never trust a client-supplied prediction.
        prediction = PredictionResponse.model_validate(model.predict(profile_dict)).model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    row = DiabetesAssessment(
        user_id=current_user.id,
        input_profile=profile_dict,
        risk_label=prediction["risk_label"],
        risk_probability=prediction["risk_probability"],
        risk_band=prediction["risk_band"],
        top_factors=prediction["top_factors"]
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _row_to_history_out(row)


@router.get("/history", response_model=List[DiabetesHistoryOut])
def list_history(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rows = (
        db.query(DiabetesAssessment)
        .filter(DiabetesAssessment.user_id == current_user.id)
        .order_by(DiabetesAssessment.created_at.desc())
        .all()
    )
    return [_row_to_history_out(r) for r in rows]


@router.delete("/history/{assessment_id}", status_code=204)
def delete_history(
    assessment_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    row = (
        db.query(DiabetesAssessment)
        .filter(
            DiabetesAssessment.id == assessment_id,
            DiabetesAssessment.user_id == current_user.id
        )
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    db.delete(row)
    db.commit()
