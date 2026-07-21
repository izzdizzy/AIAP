"""
Gen AI Care Navigation Assistant for Hospital Readmission Predictor
====================================================================

This module implements a Care Navigation Assistant using Google Gemini API
to provide personalized healthcare advice for diabetic patients in Singapore.

The assistant integrates ML model predictions with patient symptoms to generate
contextual, actionable guidance aligned with Singapore's healthcare system:
- CHAS (Community Health Assist Scheme) tiers
- Healthier SG initiative
- Polyclinic routing and primary care recommendations

Usage:
    from gen_ai import CareNavigationAssistant
    
    assistant = CareNavigationAssistant()
    advice = assistant.generate_advice(
        patient_symptoms=["fatigue", "frequent urination", "blurred vision"],
        ml_risk_score=0.75,
        risk_category="High"
    )
    print(advice)

Environment Variables:
    GEMINI_API_KEY: Required. Your Google Gemini API key.
                   Obtain from https://makersuite.google.com/app/apikey
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Try importing the google-generativeai library
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai library not available. Install with: pip install google-generativeai")


def _load_env_file():
    """Load .env file robustly for macOS compatibility."""
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent / '.env'
        load_dotenv(dotenv_path=env_path)
    except Exception:
        pass  # Silently fail if dotenv not available


# Load environment variables on module import
_load_env_file()


class CareNavigationAssistant:
    """
    AI-powered Care Navigation Assistant for Singapore healthcare context.
    
    This class uses Google Gemini to generate personalized healthcare advice
    based on ML model predictions and patient-reported symptoms.
    
    Attributes:
        api_key (str): Google Gemini API key
        model (genai.GenerativeModel): Configured Gemini model instance
        system_prompt (str): System prompt enforcing Singapore healthcare context
    """
    
    # System prompt that enforces Singapore healthcare context with strict formatting rules
    # Updated to use Clinical Severity framing instead of probability/percentage
    SYSTEM_PROMPT = """
You are a conversational care navigator for diabetic patients in Singapore. Your role is to provide 
personalized, actionable healthcare advice based on clinical severity scores and patient symptoms.

CRITICAL CONTEXT - SINGAPORE HEALTHCARE SYSTEM:
1. CHAS (Community Health Assist Scheme):
   - CHAS Blue: For lower-income households (monthly income per person <= $1,200 or annual household income <= $4,800)
   - CHAS Orange: For middle-income households (monthly income per person <= $2,000 or annual household income <= $8,000)
   - CHAS Green: For higher-income households (all Singaporeans not covered by Blue/Orange)
   - Subsidies apply at participating GP clinics for chronic disease management

2. Healthier SG:
   - National preventive care initiative launched in 2023
   - Patients enroll with a dedicated family physician (GP)
   - Focus on long-term health management and preventive screenings
   - Free Healthier SG screenings available at enrolled clinics

3. Polyclinic Network:
   - Government-subsidized primary care centers operated by NHG, SingHealth, and NUHS
   - Lower costs than private GPs for chronic disease management
   - Can refer to specialists if needed
   - Operating hours typically Mon-Fri 8am-5pm, Sat 8am-12pm

4. Emergency Guidance:
   - Call 995 for life-threatening emergencies
   - Go to A&E for urgent but non-life-threatening conditions
   - Visit GP or polyclinic for routine care and medication refills

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

CLINICAL SEVERITY INTERPRETATION - TAILORED ADVICE BY URGENCY LEVEL:
- Routine Monitoring (Low Urgency, Score < 33): Patient shows low clinical severity relative to population. Advise standard Healthier SG GP follow-ups, continue current management plan, maintain regular appointments with healthcare provider, adhere to prescribed medications. No immediate action required.

- Increased Surveillance (Moderate Urgency, Score 33-66): Patient shows moderate clinical severity. Recommend scheduling an earlier follow-up appointment to review care plan and medication adherence. Pay close attention to any changes in symptoms. Consider contacting polyclinic for enhanced monitoring.

- Immediate Intervention (High Urgency, Score > 66): Patient shows high clinical severity requiring urgent attention. STRONGLY advise seeking immediate medical attention at polyclinic or A&E. Do not delay. This requires prompt consultation with healthcare provider to assess potential complications and adjust treatment plan.
"""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-3.5-flash"):
        """
        Initialize the Care Navigation Assistant.
        
        Args:
            api_key: Google Gemini API key. If None, will attempt to read from 
                    GEMINI_API_KEY environment variable.
            model_name: Name of the Gemini model to use. Default is "gemini-2.0-flash"
                       for faster response times.
        
        Raises:
            ValueError: If API key is not provided and not found in environment
            ImportError: If google-generativeai library is not installed
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai library is required. "
                "Install with: pip install google-generativeai"
            )
        
        # Get API key from parameter or environment variable
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Gemini API key is required. Provide it as a parameter or set the "
                "GEMINI_API_KEY environment variable. "
                "Obtain a key from https://makersuite.google.com/app/apikey"
            )
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        
        # Initialize the model - system instruction is passed separately in generate_content
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name=model_name)
        
        # Generation configuration for non-streaming, complete responses
        # CRITICAL FIX FOR TRUNCATION BUG: Using non-streaming generation with explicit max_output_tokens
        # This ensures we get the full response without cutting off mid-sentence
        self.generation_config = {
            "temperature": 0.2,      # Low temperature for deterministic, focused outputs
            "top_p": 0.8,            # Nucleus sampling threshold
            "top_k": 40,             # Top-k sampling limit
            "max_output_tokens": 2048,  # Increased to prevent premature truncation (was 1024)
        }
        
        print(f"CareNavigationAssistant initialized with model: {model_name}")
    
    def _format_patient_context(
        self,
        patient_symptoms: List[str],
        ml_risk_score: float,
        risk_category: str,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format patient information into a structured prompt for the AI model.
        
        Args:
            patient_symptoms: List of patient-reported symptoms
            ml_risk_score: Float value between 0 and 1 representing clinical severity
            risk_category: String category ("Low", "Moderate", "High") - maps to urgency levels
            additional_info: Optional dictionary with additional patient context
                           (e.g., age, comorbidities, current medications)
        
        Returns:
            str: Formatted prompt string
        """
        # Build the user prompt
        prompt_parts = []
        
        # Patient symptoms section
        if patient_symptoms:
            symptoms_str = ", ".join(patient_symptoms) if isinstance(patient_symptoms, list) else str(patient_symptoms)
            prompt_parts.append(f"Current Symptoms: {symptoms_str}")
        else:
            prompt_parts.append("Current Symptoms: No specific symptoms reported")
        
        # Clinical Severity Score section - reframed from probability to relative severity (0-100 scale)
        # Convert 0-1 score to 0-100 severity score
        severity_score = int(ml_risk_score * 100)
        
        # Map internal categories to clinical urgency levels for the AI
        urgency_mapping = {
            "Low": "Routine Monitoring",
            "Moderate": "Increased Surveillance",
            "High": "Immediate Intervention"
        }
        urgency_level = urgency_mapping.get(risk_category, risk_category)
        
        prompt_parts.append(f"Clinical Severity Score: {severity_score} out of 100")
        prompt_parts.append(f"Urgency Level: {urgency_level}")
        
        # Additional context if provided
        if additional_info:
            prompt_parts.append("\nAdditional Patient Information:")
            for key, value in additional_info.items():
                prompt_parts.append(f"- {key.replace('_', ' ').title()}: {value}")
        
        # Generate the request - updated to reflect clinical severity framing
        prompt_parts.append(
            "\nBased on this information, please provide personalized care navigation advice "
            "including:\n"
            "1. Interpretation of the clinical severity score (as X out of 100, NOT as percentage)\n"
            "2. Symptom assessment and potential concerns\n"
            "3. Recommended next steps based on urgency level (care pathway in Singapore)\n"
            "4. Lifestyle and medication management tips\n"
            "5. When to seek immediate medical attention vs routine follow-up\n"
            "6. Relevant Singapore healthcare resources (CHAS, Healthier SG, polyclinics)"
        )

        return "\n".join(prompt_parts)

    def _classify_risk(self, risk_score: float) -> str:
        """
        Classify risk score into categories.

        Updated thresholds for UCI Diabetes dataset (baseline ~11% readmission rate).
        A severity score of 50+ is considered high in this context.

        Args:
            risk_score: Float value between 0 and 1

        Returns:
            str: Risk category ("Low", "Moderate", or "High")
        """
        if risk_score < 0.20:
            return "Low"
        elif risk_score < 0.40:
            return "Moderate"
        else:
            return "High"

    
    def generate_advice(
        self,
        patient_symptoms: List[str],
        ml_risk_score: float,
        risk_category: Optional[str] = None,
        user_question: str = "Please provide care navigation advice based on my current health status.",
        max_retries: int = 3,
        retry_delay: float = 2.0
    ) -> str:
        """
        Generate personalized care navigation advice using Gemini AI.
        
        CRITICAL: This function is completely stateless. It does NOT receive or use
        any chat history. Each call is independent with only the current context.
        
        Args:
            patient_symptoms: List of patient-reported symptoms
            ml_risk_score: Float value between 0 and 1 representing readmission risk
            risk_category: Optional string category. If None, will be derived from risk_score
            user_question: The user's current question (default provides general advice)
            max_retries: Maximum number of retry attempts for API calls (default: 3)
            retry_delay: Delay in seconds between retries (default: 2.0)
        
        Returns:
            str: Generated healthcare advice text
        
        Raises:
            ValueError: If risk score is outside valid range [0, 1]
            RuntimeError: If API call fails after all retries
        """
        # Validate inputs
        if not isinstance(ml_risk_score, (int, float)):
            raise TypeError("ml_risk_score must be a numeric value")
        
        if ml_risk_score < 0 or ml_risk_score > 1:
            raise ValueError("ml_risk_score must be between 0 and 1")
        
        # Auto-classify risk if not provided
        if risk_category is None:
            risk_category = self._classify_risk(ml_risk_score)
        
        # Validate risk category
        valid_categories = ["Low", "Medium", "High"]
        if risk_category not in valid_categories:
            raise ValueError(f"risk_category must be one of: {valid_categories}")
        
        # Build a minimal, focused prompt with ONLY current context
        # DO NOT include any chat history - this causes repetition loops
        prompt_parts = []
        
        # Current symptoms
        if patient_symptoms:
            symptoms_str = ", ".join(patient_symptoms) if isinstance(patient_symptoms, list) else str(patient_symptoms)
            prompt_parts.append(f"Patient Symptoms: {symptoms_str}")
        else:
            prompt_parts.append("Patient Symptoms: None reported")
        
        # Clinical Severity Score - reframed from probability to relative severity (0-100 scale)
        # Convert 0-1 score to 0-100 severity score
        severity_score = int(ml_risk_score * 100)
        
        # Map internal categories to clinical urgency levels for the AI
        urgency_mapping = {
            "Low": "Routine Monitoring",
            "Moderate": "Increased Surveillance",
            "High": "Immediate Intervention"
        }
        urgency_level = urgency_mapping.get(risk_category, risk_category)
        
        prompt_parts.append(f"Clinical Severity Score: {severity_score} out of 100")
        prompt_parts.append(f"Urgency Level: {urgency_level}")
        
        # User's current question
        prompt_parts.append(f"\nPatient Question: {user_question}")
        
        # Clear instruction to answer the specific question with clinical severity framing
        prompt_parts.append(
            "\nProvide a concise, direct answer to the patient's question above. "
            "Refer to the score as 'Clinical Severity Score of X out of 100' - NEVER as a percentage or probability. "
            "Tailor advice based on the urgency level (Routine Monitoring = standard GP follow-ups, "
            "Increased Surveillance = earlier appointment/polyclinic check-in, "
            "Immediate Intervention = seek immediate medical attention at polyclinic or A&E). "
            "Do NOT repeat disclaimers or metadata - those are handled by the UI. "
            "Do NOT reference previous conversations."
        )
        
        user_prompt = "\n".join(prompt_parts)
        
        # CRITICAL FIX FOR TRUNCATION BUG: Using non-streaming generation with stream=False
        # This ensures we receive the complete response without cutting off mid-sentence.
        # The exact pattern required by the task specification is used below.
        
        # Attempt API call with retry logic
        last_exception = None
        for attempt in range(max_retries):
            try:
                # Generate response using non-streaming mode (stream=False)
                # This is the critical fix - streaming was causing truncation issues
                response = self.model.generate_content(
                    [self.SYSTEM_PROMPT.strip(), user_prompt],
                    generation_config=self.generation_config,
                    stream=False  # CRITICAL: Must be False to prevent truncation
                )
                
                # Extract and validate response
                if response and response.text:
                    advice_text = response.text.strip()
                    
                    # VALIDATION CHECK: Ensure response is not too short (truncation indicator)
                    # If response is less than 10 characters, it's likely truncated or invalid
                    if len(advice_text) < 10:
                        print(f"Warning: Response too short ({len(advice_text)} chars), triggering retry...")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        else:
                            # Return safe fallback message after all retries
                            return "I apologize, but I'm having trouble generating a response right now. Please try again or consult your healthcare provider directly."
                    
                    # Return raw advice text - UI handles disclaimers separately
                    return advice_text
                else:
                    raise RuntimeError("Empty response received from API")
            
            except Exception as e:
                last_exception = e
                error_type = type(e).__name__
                
                # Handle specific error types
                if "rate limit" in str(e).lower() or "quota" in str(e).lower():
                    # Exponential backoff for rate limiting
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"Rate limit hit. Waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                elif "api key" in str(e).lower() or "authentication" in str(e).lower():
                    # Don't retry authentication errors
                    raise ValueError(
                        f"API authentication failed. Check your GEMINI_API_KEY. Error: {str(e)}"
                    )
                else:
                    # Generic retry with delay
                    if attempt < max_retries - 1:
                        print(f"API call failed (attempt {attempt + 1}/{max_retries}): {error_type}. Retrying...")
                        time.sleep(retry_delay)
        
        # All retries exhausted
        raise RuntimeError(
            f"Failed to generate advice after {max_retries} attempts. "
            f"Last error: {type(last_exception).__name__}: {str(last_exception)}"
        )
    
    def _add_disclaimer_and_metadata(
        self,
        advice: str,
        risk_score: float,
        risk_category: str
    ) -> str:
        """
        Add metadata header and medical disclaimer to the generated advice.
        
        Args:
            advice: The AI-generated advice text
            risk_score: The ML risk score used
            risk_category: The risk category
        
        Returns:
            str: Complete response with metadata and disclaimer
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        header = (
            "=" * 60 + "\n"
            "CARE NAVIGATION ADVICE - GENERATED BY AI ASSISTANT\n"
            "=" * 60 + "\n"
            f"Generated: {timestamp}\n"
            f"Risk Score: {risk_score:.2f} ({risk_category} Risk)\n"
            "=" * 60 + "\n\n"
        )
        
        disclaimer = (
            "\n" + "=" * 60 + "\n"
            "IMPORTANT MEDICAL DISCLAIMER\n"
            "=" * 60 + "\n"
            "This advice is generated by an AI assistant and is for informational\n"
            "purposes only. It does NOT constitute medical advice, diagnosis, or\n"
            "treatment.\n\n"
            "ALWAYS consult with a qualified healthcare professional for:\n"
            "- Medical decisions and treatment plans\n"
            "- Medication changes or adjustments\n"
            "- Interpretation of symptoms and test results\n\n"
            "IN CASE OF EMERGENCY:\n"
            "- Call 995 immediately for life-threatening conditions\n"
            "- Go to the nearest Accident & Emergency (A&E) department\n"
            "- Do not rely on AI-generated advice for emergencies\n\n"
            "For non-urgent care in Singapore:\n"
            "- Visit your enrolled Healthier SG GP clinic\n"
            "- Check CHAS subsidy eligibility at www.chas.sg\n"
            "- Locate nearest polyclinic at www.moh.gov.sg\n"
            "=" * 60
        )
        
        return header + advice + disclaimer
    
    def get_quick_recommendation(
        self,
        risk_score: float,
        symptom_count: int = 0
    ) -> str:
        """
        Provide a quick, templated recommendation without API call.
        Useful for fallback when API is unavailable or for initial screening.
        
        Args:
            risk_score: Float value between 0 and 1
            symptom_count: Number of reported symptoms
        
        Returns:
            str: Quick recommendation text
        """
        risk_category = self._classify_risk(risk_score)
        
        if risk_category == "High":
            urgency = "URGENT"
            action = (
                "Schedule an appointment with your doctor within 24-48 hours. "
                "Review your medication adherence and blood sugar monitoring. "
                "If symptoms worsen, visit a polyclinic or GP immediately."
            )
        elif risk_category == "Medium":
            urgency = "MODERATE"
            action = (
                "Schedule a follow-up with your healthcare provider within 1-2 weeks. "
                "Monitor your symptoms closely and maintain regular medication. "
                "Consider reviewing your diet and activity levels."
            )
        else:
            urgency = "ROUTINE"
            action = (
                "Continue your current diabetes management plan. "
                "Attend scheduled follow-ups and maintain healthy lifestyle habits. "
                "Report any new or worsening symptoms to your doctor."
            )
        
        symptom_note = ""
        if symptom_count > 0:
            symptom_note = f" You have reported {symptom_count} symptom(s), which should be discussed with your doctor."
        
        return (
            f"Risk Level: {risk_category} ({urgency})\n"
            f"Recommended Action: {action}{symptom_note}\n\n"
            "Singapore Healthcare Resources:\n"
            "- Healthier SG: Enroll with a family physician for continuous care\n"
            "- CHAS Clinics: Check subsidy eligibility at www.chas.sg\n"
            "- Polyclinics: Affordable primary care with specialist referral capability\n"
            "- Emergency: Call 995 for life-threatening conditions"
        )


# Convenience function for direct usage
def generate_care_advice(
    symptoms: List[str],
    risk_score: float,
    api_key: Optional[str] = None,
    **kwargs
) -> str:
    """
    Convenience function to generate care advice without instantiating the class.
    
    Args:
        symptoms: List of patient symptoms
        risk_score: ML risk score (0-1)
        api_key: Optional Gemini API key (uses GEMINI_API_KEY env var if not provided)
        **kwargs: Additional arguments passed to generate_advice()
    
    Returns:
        str: Generated healthcare advice
    """
    assistant = CareNavigationAssistant(api_key=api_key)
    return assistant.generate_advice(
        patient_symptoms=symptoms,
        ml_risk_score=risk_score,
        **kwargs
    )


if __name__ == "__main__":
    # Example usage and testing
    print("Testing CareNavigationAssistant...")
    
    # Check if API key is available
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("\nNo GEMINI_API_KEY found in environment.")
        print("Set the environment variable to test the full functionality:")
        print("  export GEMINI_API_KEY='your-key-here'")
        print("\nDemonstrating fallback quick recommendation...\n")
        
        # Demo quick recommendation
        assistant = CareNavigationAssistant.__new__(CareNavigationAssistant)
        print(assistant.get_quick_recommendation(risk_score=0.75, symptom_count=3))
    else:
        print("\nGEMINI_API_KEY found. Running full test...\n")
        try:
            assistant = CareNavigationAssistant()
            advice = assistant.generate_advice(
                patient_symptoms=["fatigue", "frequent urination", "blurred vision"],
                ml_risk_score=0.75,
                risk_category="High"
            )
            print(advice)
        except Exception as e:
            print(f"Error during test: {type(e).__name__}: {str(e)}")
