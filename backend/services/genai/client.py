"""
Singleton LLM Client Helper with Fallback and Retry Logic
"""

import os
import json
import time
import re
from typing import Dict, Any, Optional
from ...config import settings


class GenAIClient:
    """
    Singleton LLM client helper with retry and fallback logic.
    Supports both google.genai and google.generativeai SDKs.
    Guarantees structured JSON return payloads.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GenAIClient, cls).__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        self.api_key = (
            getattr(settings, "GEMINI_KEY", None)
            or getattr(settings, "DIABETES_GEMINI_KEY", None)
            or os.environ.get("GEMINI_KEY")
            or os.environ.get("GEMINI_API_KEY")
            or ""
        )
        self.model_name = os.environ.get("LLM_MODEL", "gemini-3.5-flash")
        self.genai_sdk = None
        self.is_available = False

        if not self.api_key:
            print("[GenAIClient] Warning: No GEMINI_KEY configured. Operating in fallback mode.")
            return

        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.genai_sdk = "google-genai"
            self.is_available = True
            print(f"[GenAIClient] Initialized google.genai client with model {self.model_name}")
        except Exception as e1:
            try:
                import google.generativeai as genai_legacy
                genai_legacy.configure(api_key=self.api_key)
                self.legacy_model = genai_legacy.GenerativeModel(self.model_name)
                self.genai_sdk = "google-generativeai"
                self.is_available = True
                print(f"[GenAIClient] Initialized google.generativeai client with model {self.model_name}")
            except Exception as e2:
                print(f"[GenAIClient] Failed to initialize Gemini SDKs: {e1} / {e2}")
                self.is_available = False

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        fallback_data: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> Dict[str, Any]:
        """
        Generates content from LLM and guarantees a valid JSON dict matching response schema.
        Falls back gracefully if LLM is unavailable or fails after max_retries.
        """
        if not self.is_available:
            return fallback_data or {
                "message": "AI service is currently operating in offline protocol mode.",
                "widget": None
            }

        full_prompt = prompt
        if system_prompt:
            full_prompt = (
                f"SYSTEM INSTRUCTIONS:\n{system_prompt}\n\n"
                f"USER PROMPT:\n{prompt}\n\n"
                f"CRITICAL REQUIREMENT: Return ONLY a valid JSON object. Do not include markdown code block backticks unless strictly JSON, and do not include any leading or trailing conversational text outside the JSON object."
            )

        for attempt in range(1, max_retries + 1):
            try:
                raw_text = ""
                if self.genai_sdk == "google-genai":
                    from google.genai import types
                    config = types.GenerateContentConfig(
                        temperature=0.3,
                        max_output_tokens=2048,
                        system_instruction=system_prompt
                    )
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=full_prompt,
                        config=config
                    )
                    raw_text = response.text or ""
                elif self.genai_sdk == "google-generativeai":
                    response = self.legacy_model.generate_content(full_prompt)
                    raw_text = response.text or ""

                parsed_json = self._clean_and_parse_json(raw_text)
                if parsed_json and isinstance(parsed_json, dict) and "message" in parsed_json:
                    return parsed_json
            except Exception as e:
                print(f"[GenAIClient] Attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    time.sleep(retry_delay * attempt)

        return fallback_data or {
            "message": "AI service encountered a temporary connection issue. Showing clinical fallback summary.",
            "widget": None
        }

    def _clean_and_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        text = text.strip()

        # Strip ```json or ``` markdown wrapper if present
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            return json.loads(text)
        except Exception:
            # Try finding first '{' and last '}'
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
        return None


genai_client = GenAIClient()
