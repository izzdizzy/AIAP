from .model.pipeline import run_prediction
from .schemas import PredictionResponse


def predict_cad_risk(payload: dict) -> PredictionResponse:
    print("Predicting CAD risk payload:", payload)
    result = run_prediction(payload)
    return PredictionResponse.model_validate(result)
