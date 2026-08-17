"""
Gen AI Service for Hospital Readmission Predictor API
======================================================

This module handles Gen AI chat functionality, migrated from gen_ai.py.
It integrates with Google Gemini API to provide personalized healthcare advice
with safety guardrails and API failure fallback.
"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Resolve .env from the integration workspace root
# File is at: backend/services/readmission/genai_service.py
_CURRENT_FILE = Path(__file__).resolve()
_INTEGRATION_ROOT = _CURRENT_FILE.parent.parent.parent.parent  # Goes up 4 levels to _integration_workspace

_env_path = _INTEGRATION_ROOT / '.env'
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path, override=True)
    print(f"[GenAI Service] Loaded .env from {_env_path}")
else:
    print(f"[GenAI Service] Warning: .env file not found at {_env_path}")

from typing import List, Dict, Any, Optional

# Try importing the google-generativeai library
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("[GenAI] Warning: google-generativeai library not available.")


# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

# System prompt for Singapore healthcare context
SYSTEM_PROMPT = """
You are a conversational care navigator for diabetic patients in Singapore. Your role is to provide 
personalized, actionable healthcare advice based on clinical severity scores and patient symptoms.

CRITICAL CONTEXT - SINGAPORE HEALTHCARE SYSTEM:
1. CHAS (Community Health Assist Scheme):
   - CHAS Blue: For lower-income households (monthly income per person <= $1,200)
   - CHAS Orange: For middle-income households (monthly income per person <= $2,000)
   - CHAS Green: For higher-income households (all Singaporeans not covered by Blue/Orange)
   - Subsidies apply at participating GP clinics for chronic disease management
   - Official link: https://www.chas.sg

2. Healthier SG:
   - National preventive care initiative launched in 2023
   - Patients enroll with a dedicated family physician (GP)
   - Focus on long-term health management and preventive screenings
   - Free Healthier SG screenings available at enrolled clinics
   - Official link: https://www.moh.gov.sg/healthiersg

3. Polyclinic Network:
   - Government-subsidized primary care centers operated by NHG, SingHealth, and NUHS
   - Lower costs than private GPs for chronic disease management
   - Can refer to specialists if needed
   - Care routing info: https://www.moh.gov.sg

4. Medication Assistance Fund (MAF):
   - Subsidises costly medicines for eligible, means-tested patients
   - Apply via the medical social service office at public healthcare institutions
   - Official link: https://www.moh.gov.sg/costs-and-claims/medication-assistance-fund

5. Emergency Guidance:
   - Emergency ambulance: Call 995 for life-threatening emergencies
   - Non-emergency ambulance: Call 1777 for non-urgent transport
   - For non-urgent after-hours care, direct users to a 24-hr GP clinic or telemedicine service, or their polyclinic/CHAS GP by day
   - General MOH info: https://www.moh.gov.sg

CRITICAL CONVERSATIONAL RULES - MUST FOLLOW:
1. You are a conversational care navigator. Answer the user's specific question directly using the provided context.
2. Do NOT just repeat the user's severity score or symptoms back to them unless they specifically ask for a summary.
3. If the user asks what to watch out for, give them actionable steps based on their specific symptoms and urgency level.
4. NEVER include disclaimers, headers, or metadata blocks - these are handled by the UI
5. Each response should directly answer the user's current question only - do not reference prior conversation
6. Provide fresh, unique information in each response - never say "As mentioned before" or "To reiterate"
7. CRITICAL: The score provided is a Clinical Severity Score (0-100), NOT a percentage or probability. Do NOT describe it as "% chance" or "probability".

STRICT FORMATTING RULES - MUST FOLLOW:
1. DO NOT use markdown headers (#, ##, ###) under any circumstances. These create huge fonts in the UI.
2. Use bold text (**text**) for emphasis on key terms instead of headers.
3. Keep the tone conversational, concise, and friendly.
4. Do NOT output any section headers like "=== CARE NAVIGATION ADVICE ===" or timestamps
5. Do NOT include medical disclaimers - they are displayed separately in the UI
6. Do NOT create numbered lists unless absolutely necessary - use bullet points instead.
7. Avoid repetitive language - each sentence should add new information.
8. Keep responses between 150-300 words maximum.
9. Structure your response as a natural conversation, not a formatted report.

LINK EMBEDDING RULES - MUST FOLLOW:
1. When explaining a scheme or service (CHAS, Healthier SG, MAF, emergency services, polyclinics), ALWAYS include the matching official link from the knowledge base.
2. Use markdown link format: [link text](https://url) - this exact syntax with square brackets and parentheses.
3. Example: For CHAS subsidies, write: Visit [CHAS](https://www.chas.sg) to check your eligibility.
4. Only use the URLs provided in this prompt - do NOT invent or guess URLs.
5. Always embed links naturally within sentences, not as standalone URLs.

COLOUR EMPHASIS RULES - MUST FOLLOW SPARSELY:
1. Use {red: critical action} for urgent actions requiring immediate attention (e.g., seeking emergency care).
2. Use {amber: caution point} for monitoring advice or cautionary notes (e.g., watch for symptoms).
3. Use {green: reassurance} for normal/OK status or positive reinforcement.
4. Use colour emphasis very sparingly - only 1-2 instances per response maximum.
5. Never overuse colours; they should highlight key points only.

YOUR RESPONSE GUIDELINES:
1. Always directly answer the user's specific question first
2. When referring to the score, describe it as "Clinical Severity Score of [X] out of 100" - NEVER as a percentage or probability
3. Connect symptoms to potential diabetes management issues when asked
4. Provide specific, actionable next steps relevant to Singapore healthcare
5. Mention appropriate care pathways (CHAS clinics, Healthier SG, polyclinics) when giving care recommendations
6. Include lifestyle recommendations (diet, exercise, medication adherence) when relevant
7. Specify when to seek immediate medical attention vs routine follow-up when discussing symptoms
8. Never diagnose - always recommend consulting a healthcare professional
9. Be concise and avoid repetition - get straight to the point
10. CRITICAL: Each response must be stateless and self-contained - do not reference prior conversation
11. Include relevant official links when mentioning schemes or services so users can tap through for more details
12. Use colour emphasis ({red: }, {amber: }, {green: }) sparingly to highlight critical actions, cautions, or reassurances

CLINICAL SEVERITY INTERPRETATION - TAILORED ADVICE BY URGENCY LEVEL:
- Routine Monitoring (Low Urgency, Score < 33): Patient shows low clinical severity. Advise standard Healthier SG GP follow-ups, continue current management plan, maintain regular appointments with healthcare provider, adhere to prescribed medications. No immediate action required.

- Increased Surveillance (Moderate Urgency, Score 33-66): Patient shows moderate clinical severity. Recommend scheduling an earlier follow-up appointment to review care plan and medication adherence. Pay close attention to any changes in symptoms. Consider contacting polyclinic for enhanced monitoring.

- Immediate Intervention (High Urgency, Score > 66): Patient shows high clinical severity requiring urgent attention. STRONGLY advise seeking immediate medical attention at polyclinic or A&E. Do not delay. This requires prompt consultation with healthcare provider to assess potential complications and adjust treatment plan.
"""


# =============================================================================
# GEN AI SERVICE CLASS
# =============================================================================

class GenAIService:
    """
    AI-powered Care Navigation Assistant for Singapore healthcare context.
    
    This class uses Google Gemini to generate personalized healthcare advice
    based on ML model predictions and patient-reported symptoms.
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-3.5-flash"):
        """
        Initialize the Gen AI service.
        
        Args:
            api_key: Google Gemini API key. If None, will read from GEMINI_API_KEY env var.
            model_name: Name of the Gemini model to use. Default is "gemini-2.0-flash".
        """
          # Check both possible environment variable names
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_KEY")
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model_name = model_name
        self.model = None
        self.is_available = False
        
        # Generation configuration for non-streaming, complete responses
        self.generation_config = {
            "temperature": 0.2,      # Low temperature for deterministic outputs
            "top_p": 0.8,            # Nucleus sampling threshold
            "top_k": 40,             # Top-k sampling limit
            "max_output_tokens": 2048,  # Prevent premature truncation
        }
        
        # Initialize if API key is available
        if self.api_key and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(model_name=model_name)
                self.is_available = True
                print(f"[GenAI] Initialized with model: {model_name}")
            except Exception as e:
                print(f"[GenAI] Warning: Failed to initialize Gemini: {str(e)}")
        else:
            if not GEMINI_AVAILABLE:
                print("[GenAI] google-generativeai library not installed. Using fallback responses only.")
            else:
                print("[GenAI] No API key configured. Using fallback responses only.")
    
    def _check_dangerous_content(self, user_question: str, symptoms: List[str]) -> Optional[str]:
        """
        Check for dangerous phrases that require safety intervention.
        
        Returns:
            Safety warning message if dangerous content detected, None otherwise.
        """
        dangerous_phrases = [
            'stop taking insulin',
            'ignore doctor',
            'don\'t take medication',
            'skip your meds',
            'stop medication',
            'discontinue treatment',
            'ignore medical advice',
            'harm yourself',
            'hurt yourself'
        ]
        
        user_question_lower = user_question.lower()
        for phrase in dangerous_phrases:
            if phrase in user_question_lower:
                return (
                    "**SAFETY WARNING**: I cannot provide advice on stopping or ignoring medical treatment. "
                    "Please consult your healthcare provider immediately for any concerns about your medications. "
                    "For emergencies, call 995 or go to the nearest A&E."
                )
        
        # Also check patient symptoms for dangerous content
        if symptoms:
            symptoms_str = ", ".join(symptoms).lower()
            for phrase in dangerous_phrases:
                if phrase in symptoms_str:
                    return (
                        "**SAFETY WARNING**: I notice concerning content related to stopping medical treatment. "
                        "Please speak with your healthcare provider right away. Your health and safety are important. "
                        "For emergencies, call 995 or go to the nearest A&E."
                    )
        
        return None
    
    def _get_fallback_response(self, severity_score: int, urgency_level: str, symptoms: List[str]) -> str:
        """
        Generate a templated fallback response when API is unavailable.
        
        Args:
            severity_score: Clinical Severity Score (0-100)
            urgency_level: Urgency level string
            symptoms: List of patient symptoms
            
        Returns:
            Fallback advice text with system note about offline mode
        """
        # Add transparent system note for fallback mode
        system_note = "[System Note: Operating on offline clinical protocols due to API unavailability.] "
        
        if urgency_level == "Immediate Intervention":
            return (
                system_note +
                f"**URGENT ATTENTION REQUIRED**\n\n"
                f"Your Clinical Severity Score of {severity_score} out of 100 indicates high risk. "
                f"I strongly recommend seeking immediate medical attention at a polyclinic or A&E. "
                f"Do not delay - please contact your healthcare provider right away.\n\n"
                f"For your reported symptoms ({', '.join(symptoms) if symptoms else 'none specified'}), "
                f"prompt medical evaluation is essential to rule out serious complications."
            )
        elif urgency_level == "Increased Surveillance":
            return (
                system_note +
                f"**MODERATE CONCERN**\n\n"
                f"Your Clinical Severity Score of {severity_score} out of 100 suggests moderate risk. "
                f"I recommend scheduling an appointment with your Healthier SG GP within the next few days "
                f"to review your care plan and medication adherence.\n\n"
                f"Monitor your symptoms ({', '.join(symptoms) if symptoms else 'none specified'}) closely. "
                f"If they worsen, visit a polyclinic or GP immediately. Consider checking your blood sugar levels more frequently."
            )
        else:
            return (
                system_note +
                f"**ROUTINE MONITORING**\n\n"
                f"Your Clinical Severity Score of {severity_score} out of 100 indicates low risk. "
                f"Continue your current diabetes management plan and attend scheduled follow-ups with your GP.\n\n"
                f"Maintain healthy lifestyle habits including proper diet, regular exercise, and medication adherence. "
                f"Report any new or worsening symptoms to your healthcare provider."
            )
    
    def generate_response(
        self,
        clinical_severity_score: int,
        symptoms: List[str],
        chas_tier: Optional[str],
        user_query: str,
        max_retries: int = 3,
        retry_delay: float = 2.0
    ) -> Dict[str, Any]:
        """
        Generate AI response for the chat endpoint.
        
        Args:
            clinical_severity_score: Clinical Severity Score (0-100)
            symptoms: List of patient-reported symptoms
            chas_tier: CHAS tier (Blue, Orange, Green, or None)
            user_query: User's question or message
            max_retries: Maximum number of retry attempts for API calls
            retry_delay: Delay in seconds between retries
            
        Returns:
            Dictionary containing:
            - response: AI-generated advice text
            - is_fallback: Whether fallback response was used
            - safety_warning: Safety warning if dangerous content detected
        """
        try:
            # Validate inputs
            if not isinstance(clinical_severity_score, (int, float)):
                raise TypeError("clinical_severity_score must be numeric")
            
            if clinical_severity_score < 0 or clinical_severity_score > 100:
                raise ValueError("clinical_severity_score must be between 0 and 100")
            
            # Check for dangerous content first
            safety_warning = self._check_dangerous_content(user_query, symptoms)
            if safety_warning:
                return {
                    "response": safety_warning,
                    "is_fallback": False,
                    "safety_warning": safety_warning
                }
            
            # Determine urgency level from severity score
            if clinical_severity_score < 33:
                urgency_level = "Routine Monitoring"
            elif clinical_severity_score < 66:
                urgency_level = "Increased Surveillance"
            else:
                urgency_level = "Immediate Intervention"
            
            # Build the user prompt with explicit patient context format
            prompt_parts = []
            
            # Patient context header for clear prompt structure
            prompt_parts.append("=== PATIENT CONTEXT ===")
            
            # Current symptoms - explicitly include in prompt
            if symptoms:
                symptoms_str = ", ".join(symptoms)
                prompt_parts.append(f"Patient Symptoms: {symptoms_str}")
            else:
                prompt_parts.append("Patient Symptoms: None reported")
            
            # Clinical Severity Score and Urgency Level
            prompt_parts.append(f"Clinical Severity Score: {clinical_severity_score} out of 100")
            prompt_parts.append(f"Urgency Level: {urgency_level}")
            
            # CHAS tier if provided
            if chas_tier:
                prompt_parts.append(f"CHAS Tier: {chas_tier}")
            
            # User's current question
            prompt_parts.append(f"\nPatient Question: {user_query}")
            
            # Clear instruction with explicit context requirement
            prompt_parts.append(
                "\nProvide a concise, direct answer to the patient's question above. "
                "Refer to the score as 'Clinical Severity Score of X out of 100' - NEVER as a percentage or probability. "
                "Tailor advice based on the urgency level and specific symptoms provided. "
                "Do NOT repeat disclaimers or metadata. "
                "Do NOT reference previous conversations."
            )
            
            user_prompt = "\n".join(prompt_parts)
            
            # If API is not available, use fallback
            if not self.is_available or self.model is None:
                print("[GenAI] API not available. Using fallback response.")
                fallback_response = self._get_fallback_response(clinical_severity_score, urgency_level, symptoms)
                return {
                    "response": fallback_response,
                    "is_fallback": True,
                    "safety_warning": None
                }
            
            # Attempt API call with retry logic
            last_exception = None
            for attempt in range(max_retries):
                try:
                    # Generate response using non-streaming mode
                    response = self.model.generate_content(
                        [SYSTEM_PROMPT.strip(), user_prompt],
                        generation_config=self.generation_config,
                        stream=False
                    )
                    
                    # Extract and validate response
                    if response and response.text:
                        advice_text = response.text.strip()
                        
                        # Validation check: Ensure response is not too short
                        if len(advice_text) < 10:
                            print(f"[GenAI] Warning: Response too short ({len(advice_text)} chars), triggering retry...")
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay)
                                continue
                            else:
                                # Return fallback after all retries
                                fallback_response = self._get_fallback_response(clinical_severity_score, urgency_level, symptoms)
                                return {
                                    "response": fallback_response,
                                    "is_fallback": True,
                                    "safety_warning": None
                                }
                        
                        return {
                            "response": advice_text,
                            "is_fallback": False,
                            "safety_warning": None
                        }
                    else:
                        raise RuntimeError("Empty response received from API")
                
                except Exception as e:
                    last_exception = e
                    error_type = type(e).__name__
                    
                    # Handle rate limiting with exponential backoff
                    if "rate limit" in str(e).lower() or "quota" in str(e).lower():
                        wait_time = retry_delay * (2 ** attempt)
                        print(f"[GenAI] Rate limit hit. Waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}")
                        time.sleep(wait_time)
                    elif "api key" in str(e).lower() or "authentication" in str(e).lower():
                        # Don't retry authentication errors - return fallback immediately
                        print(f"Gemini API failed: API key not valid. Using fallback.")
                        fallback_response = self._get_fallback_response(clinical_severity_score, urgency_level, symptoms)
                        return {
                            "response": fallback_response,
                            "is_fallback": True,
                            "safety_warning": None
                        }
                    else:
                        # Generic retry with delay
                        if attempt < max_retries - 1:
                            print(f"[GenAI] API call failed (attempt {attempt + 1}/{max_retries}): {error_type}. Retrying...")
                            time.sleep(retry_delay)
                        else:
                            # Final attempt failed - log and return fallback
                            print(f"Gemini API failed after all retries: {str(e)}. Using fallback.")
            
            # All retries exhausted - use fallback
            print(f"[GenAI] All retries exhausted. Using fallback response.")
            fallback_response = self._get_fallback_response(clinical_severity_score, urgency_level, symptoms)
            return {
                "response": fallback_response,
                "is_fallback": True,
                "safety_warning": None
            }
            
        except Exception as e:
            # CRITICAL: Catch any unexpected exception and return fallback
            print(f"Gemini API failed with unexpected error: {str(e)}. Using fallback.")
            # Determine urgency level for fallback response
            if clinical_severity_score < 33:
                urgency_level = "Routine Monitoring"
            elif clinical_severity_score < 66:
                urgency_level = "Increased Surveillance"
            else:
                urgency_level = "Immediate Intervention"
            fallback_response = self._get_fallback_response(clinical_severity_score, urgency_level, symptoms or [])
            return {
                "response": fallback_response,
                "is_fallback": True,
                "safety_warning": None
            }


# Singleton instance for the FastAPI app
_genai_service_instance: Optional[GenAIService] = None


def get_genai_service() -> GenAIService:
    """Get or create the Gen AI service singleton instance."""
    global _genai_service_instance
    if _genai_service_instance is None:
        _genai_service_instance = GenAIService()
    return _genai_service_instance
