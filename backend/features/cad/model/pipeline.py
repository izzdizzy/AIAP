from .formatter import format_prediction
from .predict import predict_from_preprocessed
from .preprocess import preprocess
from .response import build_lifestyle_advice, build_medical_disclaimer, get_risk_level


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
