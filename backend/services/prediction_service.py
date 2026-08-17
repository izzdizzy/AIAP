from ..model.pipeline import run_prediction
from ..model.schemas import PredictionResponse


def predict_cad_risk(payload: dict) -> PredictionResponse:
    print(payload)
    result = run_prediction(payload)
    return PredictionResponse.model_validate(result)
