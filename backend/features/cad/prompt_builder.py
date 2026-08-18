from pathlib import Path
from .model.translations import *

SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent / "documents" / "system_prompt.txt"


def load_system_prompt() -> str:
    """
    Loads the system prompt from disk.
    """
    if SYSTEM_PROMPT_PATH.exists():
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    return "You are an expert AI lifestyle coaching assistant specializing in cardiovascular health."


SYSTEM_PROMPT = load_system_prompt()


def format_assessment(assessment: dict) -> str:
    return f"""
Age:
{int(assessment["age"])} years

Sex:
{SEX.get(int(assessment["sex"]), "Unknown")}

Chest Pain Type:
{CHEST_PAIN.get(int(assessment["cp"]), "Unknown")}

Resting Blood Pressure:
{assessment["trestbps"]} mmHg

Serum Cholesterol:
{assessment["chol"]} mg/dL

Fasting Blood Sugar:
{FASTING_BLOOD_SUGAR.get(int(assessment["fbs"]), "Unknown")}

Resting ECG:
{REST_ECG.get(int(assessment["restecg"]), "Unknown")}

Maximum Heart Rate:
{assessment["thalach"]} bpm

Exercise-induced Angina:
{EXERCISE_ANGINA.get(int(assessment["exang"]), "Unknown")}

ST Depression (Oldpeak):
{assessment["oldpeak"]}

Slope of Peak Exercise ST Segment:
{SLOPE.get(int(assessment["slope"]), "Unknown")}

Major Vessels Colored by Fluoroscopy:
{int(assessment["ca"])}

Thalassemia:
{THAL.get(int(assessment["thal"]), "Unknown")}
""".strip()


def format_factors(top_factors: list[dict]) -> str:
    lines = []
    for factor in top_factors:
        lines.append(
            f"- {factor['feature']}: "
            f"{factor['impact']} "
            f"({factor['direction']} risk)"
        )

    return "\n".join(lines)


def format_prediction(prediction: dict) -> str:
    factors_str = format_factors(
        prediction.get("top_factors", [])
    )

    return f"""
Risk Level:
{prediction["risk_level"]}

Risk Percentage:
{prediction["risk_percent"]}%

Key Contributing Factors:
{factors_str}
""".strip()


def format_conversation(messages: list[dict]) -> str:
    lines = []
    for msg in messages:
        role = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"{role}: {msg['content']}")

    return "\n\n".join(lines)


def build_prompt(
    assessment: dict,
    prediction: dict,
    knowledge: str,
    messages: list[dict]
) -> str:
    formatted_assessment = format_assessment(assessment)
    formatted_prediction = format_prediction(prediction)
    conversation = format_conversation(messages)

    return f"""
SYSTEM INSTRUCTIONS:
{SYSTEM_PROMPT}

USER ASSESSMENT:
{formatted_assessment}

USER PREDICTION:
{formatted_prediction}

REFERENCE KNOWLEDGE:
{knowledge}

CONVERSATION HISTORY:
{conversation}

Assistant:
""".strip()
