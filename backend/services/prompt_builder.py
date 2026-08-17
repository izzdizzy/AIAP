from pathlib import Path
from ..model.translations import *

BASE_DIR = Path(__file__).resolve().parent.parent
SYSTEM_PROMPT_PATH = BASE_DIR / "genai_documents" / "system_prompt.txt"


def load_system_prompt() -> str:
    """
    Loads the system prompt from disk.

    This is only read once when the server starts.
    """
    return SYSTEM_PROMPT_PATH.read_text(
        encoding="utf-8"
    ).strip()


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

def build_prompt(
    assessment: dict,
    prediction: dict,
    knowledge: str,
    messages: list[dict],
) -> str:
    """
    Builds the complete prompt sent to Gemini.
    """

    print("check", prediction)
    prompt = f"""
{SYSTEM_PROMPT}

# Patient's Assessment
{format_assessment(assessment)}

#Prediction Results

Risk Level:
{prediction["risk_level"]}

Estimated CAD Risk:
{prediction["risk_percent"]:.1f}%

Top Contributing Factors:
{format_top_factors(prediction["top_factors"])}

# Reference Information
=== Knowledge Start ===

{knowledge}

=== Knowledge End ===

# Conversation History (Latest message is current message)

{format_messages(messages)}


Assistant:
"""

    return prompt.strip()


def format_assessment(assessment: dict) -> str:
    """
    Converts assessment JSON into readable text.
    """

    lines = []

    for key, value in assessment.items():
        lines.append(f"{key}: {value}")

    return "\n".join(lines)


def format_top_factors(factors: list) -> str:
    """
    Converts the top factor list into bullet points.
    """

    if not factors:
        return "Not available."

    return "\n".join(
        f"- {factor}"
        for factor in factors
    )


def format_messages(messages: list[dict]) -> str:
    """
    Converts stored messages into a readable conversation.
    """

    if not messages:
        return "No previous conversation."

    conversation = []

    for message in messages:

        role = "User" if message["role"] == "user" else "Assistant"

        conversation.append(
            f"{role}: {message['content']}"
        )

    return "\n\n".join(conversation)