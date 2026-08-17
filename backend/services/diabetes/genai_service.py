"""
Gen AI layer: the Personalised Risk Explainer.

Takes the model's risk output plus the person's profile and asks an LLM to
explain it in plain, supportive language. This is the Gen AI capability for
the project, its use case is clearly scoped: turn a numeric risk score and its
drivers into guidance a non-technical person can act on.

Design choices worth knowing for the code review:
- The LLM only EXPLAINS the model's output. It does not decide the risk itself.
  The number comes from the trained classifier; the LLM just translates it.
  This keeps the medical decision with the validated model, not the language model.
- The API key is read from an environment variable, never hard-coded, so the
  key is not exposed in the submitted source.
- If no key is set, we fall back to a template so the backend still runs and
  can be demoed without a paid API.
"""

import os

# Load a local .env file if present (so you can keep the key in one place
# instead of retyping it each session). The .env file must NOT be committed
# to Git or included in your submission - it holds the secret key.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional; env vars still work without it

# Read configuration from environment variables.
# LLM_API_KEY holds the Google Gemini API key. It is never hard-coded in this
# file, so the key does not end up in the submitted source or in Git history.
LLM_API_KEY = os.getenv("DIABETES_GEMINI_KEY") or os.getenv("GEMINI_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash")


def _build_prompt(profile: dict, prediction: dict) -> str:
    """Assemble the instruction sent to the LLM. We give it the risk result and
    the person's key values, and tell it exactly how to respond."""
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
    """Used when no LLM key is configured, so the app still returns something."""
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
    """Main entry point: return a plain-language explanation of the risk."""
    # No key configured -> safe fallback so the demo still works.
    if not LLM_API_KEY:
        return _template_fallback(profile, prediction)

    prompt = _build_prompt(profile, prediction)

    # Call Google Gemini. If the call fails (bad key, no network, quota),
    # fall back to the template rather than crashing the request.
    try:
        import google.generativeai as genai
        genai.configure(api_key=LLM_API_KEY)
        model = genai.GenerativeModel(LLM_MODEL)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return _template_fallback(profile, prediction) + f"\n\n[Note: live AI unavailable: {e}]"
