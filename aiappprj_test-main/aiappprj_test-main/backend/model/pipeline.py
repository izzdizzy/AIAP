from pathlib import Path
import sys

from .formatter import format_prediction
from .predict import predict_from_preprocessed
from .preprocess import preprocess
from .response import build_lifestyle_advice, build_medical_disclaimer, get_risk_level

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def run_prediction(patient: dict) -> dict:
    preprocessed = preprocess(patient)
    raw_result = predict_from_preprocessed(preprocessed)
    formatted = format_prediction(raw_result, patient)
    risk_probability = float(formatted['risk_probability'])

    return {
        **formatted,
        'raw_probability': float(raw_result['raw_probability']),
        'risk_level': get_risk_level(risk_probability),
        'lifestyle_advice': build_lifestyle_advice(risk_probability),
        'medical_disclaimer': build_medical_disclaimer()
    }
