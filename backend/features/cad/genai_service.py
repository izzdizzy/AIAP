from google import genai
from google.genai import types

from ...config import settings

client = genai.Client(
    api_key=settings.GEMINI_KEY
)

MODEL_ID = "gemini-3.5-flash"

GENERATION_CONFIG = types.GenerateContentConfig(
    temperature=0.4,
    max_output_tokens=2048,
    thinking_config=types.ThinkingConfig(
        thinking_budget=512
    )
)


def generate_response(prompt: str) -> str:
    """
    Sends a completed prompt to Gemini and returns the text response.
    """
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=GENERATION_CONFIG,
    )

    return response.text.strip()
