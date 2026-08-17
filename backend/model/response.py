from .constants import LIFESTYLE_ADVICE, MEDICAL_DISCLAIMER, RISK_LEVELS


def get_risk_level(probability: float) -> str:
    for level, upper_bound in RISK_LEVELS:
        if probability < upper_bound:
            return level
    return 'High'


def build_lifestyle_advice(probability: float) -> list[str]:
    return LIFESTYLE_ADVICE[get_risk_level(probability)]


def build_medical_disclaimer() -> str:
    return MEDICAL_DISCLAIMER
