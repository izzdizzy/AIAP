from fastapi import APIRouter

from ..model.schemas import AssessmentRequest, PredictionResponse
from ..services.prediction_service import predict_cad_risk

router = APIRouter()


@router.post('/predict', response_model=PredictionResponse)
def predict(payload: AssessmentRequest) -> PredictionResponse:
    return predict_cad_risk(payload.model_dump())
