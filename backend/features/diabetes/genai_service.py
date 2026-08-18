import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

LLM_API_KEY = os.getenv("DIABETES_GEMINI_KEY") or os.getenv("GEMINI_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash")


def _build_prompt(profile: dict, prediction: dict) -> str:
    factors = ", ".join(prediction["top_factors"])
    return (
        "You are a supportive health assistant for a chronic-disease monitoring app "
        "used in Singapore. Explain a diabetes risk result to a non-medical user.\n\n"
        f"Risk result from the model: {prediction['risk_label']} "
        f"(probability {prediction['risk_probability']}, band {prediction['risk_band']}).\n"
        f"The user's most influential health factors: {factors}.\n\n"
        "Write 3 short paragraphs:\n"
        "1. Explain what this risk level means in plain, calm language.\n"
        "2. Point to 2-3 of their specific factors and why they matter.\n"
        "3. Give practical next steps. If risk is Moderate or High, advise seeing "
        "a GP or polyclinic and mention Healthier SG enrolment.\n\n"
        "Be encouraging, not alarming. Do NOT give a diagnosis. Add a one-line "
        "reminder that this is a screening tool, not medical advice."
    )


def _template_fallback(profile: dict, prediction: dict) -> str:
    band = prediction["risk_band"]
    factors = ", ".join(prediction["top_factors"])
    advice = ("Consider booking a check-up at your polyclinic or GP, and look into "
              "Healthier SG enrolment.") if band in ("Moderate", "High") else \
             ("Keep up your current habits and review your health yearly.")
    return (
        f"Your diabetes risk is assessed as {band} "
        f"({prediction['risk_label']}, probability {prediction['risk_probability']}). "
        f"The factors influencing this most are: {factors}. {advice} "
        "Please remember this is a screening tool, not a medical diagnosis."
    )


def generate_explanation(profile: dict, prediction: dict) -> str:
    if not LLM_API_KEY:
        return _template_fallback(profile, prediction)

    prompt = _build_prompt(profile, prediction)

    try:
        import google.generativeai as genai
        genai.configure(api_key=LLM_API_KEY)
        model = genai.GenerativeModel(LLM_MODEL)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return _template_fallback(profile, prediction) + f"\n\n[Note: live AI unavailable: {e}]"
