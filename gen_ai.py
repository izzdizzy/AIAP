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
from typing import List, Dict, Any, Optional
from datetime import datetime

# Try importing the google-generativeai library
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai library not available. Install with: pip install google-generativeai")


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
    # Updated to explicitly forbid repetition and prevent infinite loops
    SYSTEM_PROMPT = """
You are a Care Navigation Assistant for diabetic patients in Singapore. Your role is to provide 
personalized, actionable healthcare advice based on hospital readmission risk predictions and 
patient symptoms.

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

STRICT ANTI-REPETITION RULES - CRITICAL TO FOLLOW:
1. NEVER repeat content from previous responses - each response must be unique
2. NEVER include disclaimers, headers, or metadata blocks - these are handled by the UI
3. NEVER say things like "As mentioned before" or "To reiterate" - always provide fresh information
4. DO NOT output any section headers like "=== CARE NAVIGATION ADVICE ===" or timestamps
5. DO NOT include medical disclaimers - they are displayed separately in the UI
6. Each response should directly answer the user's current question only

STRICT FORMATTING RULES - MUST FOLLOW:
1. DO NOT use markdown headers (#, ##, ###) under any circumstances. These create huge fonts in the UI.
2. Use bold text (**text**) for section titles instead of headers.
3. Keep the tone conversational, concise, and friendly.
4. Do NOT repeat greetings or introductory phrases like "Hello", "Thank you for sharing", etc.
5. Do NOT create numbered lists unless absolutely necessary - use bullet points instead.
6. Avoid repetitive language - each sentence should add new information.
7. Keep responses between 200-400 words maximum.
8. Structure your response with these bold sections only:
   - **Your Risk Assessment** - Explain the ML risk score simply
   - **Symptom Analysis** - Connect symptoms to diabetes management
   - **Recommended Actions** - Specific next steps in Singapore healthcare context
   - **When to Seek Help** - Clear guidance on emergency vs routine care

YOUR RESPONSE GUIDELINES:
1. Always acknowledge the patient's current situation empathetically but briefly
2. Explain the ML risk score in simple, non-alarming terms
3. Connect symptoms to potential diabetes management issues
4. Provide specific, actionable next steps relevant to Singapore
5. Mention appropriate care pathways (CHAS clinics, Healthier SG, polyclinics)
6. Include lifestyle recommendations (diet, exercise, medication adherence)
7. Specify when to seek immediate medical attention vs routine follow-up
8. Never diagnose - always recommend consulting a healthcare professional
9. Be concise and avoid repetition - get straight to the point
10. CRITICAL: Each response must be stateless and self-contained - do not reference prior conversation

RISK SCORE INTERPRETATION:
- Low Risk (< 0.4): Continue current management, routine follow-ups
- Medium Risk (0.4 - 0.7): Increase monitoring, consider medication review
- High Risk (> 0.7): Urgent follow-up recommended, assess medication adherence, check for complications
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
        
        # Initialize the model with generation config
        self.model_name = model_name
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=self.SYSTEM_PROMPT.strip()
        )
        
        # Generation configuration with low temperature to prevent looping and ensure consistency
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.2,  # Low temperature for deterministic, non-repetitive outputs
            top_p=0.9,
            top_k=40,
            max_output_tokens=1024,  # Increased from 512 to prevent premature truncation
            candidate_count=1
        )
        
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
            ml_risk_score: Float value between 0 and 1 representing readmission risk
            risk_category: String category ("Low", "Medium", "High")
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
        
        # ML risk assessment section
        risk_percentage = ml_risk_score * 100
        prompt_parts.append(f"Hospital Readmission Risk Score: {ml_risk_score:.2f} ({risk_percentage:.1f}%)")
        prompt_parts.append(f"Risk Category: {risk_category}")
        
        # Additional context if provided
        if additional_info:
            prompt_parts.append("\nAdditional Patient Information:")
            for key, value in additional_info.items():
                prompt_parts.append(f"- {key.replace('_', ' ').title()}: {value}")
        
        # Generate the request
        prompt_parts.append(
            "\nBased on this information, please provide personalized care navigation advice "
            "including:\n"
            "1. Interpretation of the risk score\n"
            "2. Symptom assessment and potential concerns\n"
            "3. Recommended next steps (care pathway in Singapore)\n"
            "4. Lifestyle and medication management tips\n"
            "5. When to seek immediate medical attention\n"
            "6. Relevant Singapore healthcare resources (CHAS, Healthier SG, polyclinics)"
        )
        
        return "\n".join(prompt_parts)
    
    def _classify_risk(self, risk_score: float) -> str:
        """
        Classify risk score into categories.
        
        Args:
            risk_score: Float value between 0 and 1
        
        Returns:
            str: Risk category ("Low", "Medium", or "High")
        """
        if risk_score < 0.4:
            return "Low"
        elif risk_score < 0.7:
            return "Medium"
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
        
        # Risk assessment
        prompt_parts.append(f"Readmission Risk Score: {ml_risk_score:.2f} ({ml_risk_score*100:.1f}%)")
        prompt_parts.append(f"Risk Category: {risk_category}")
        
        # User's current question
        prompt_parts.append(f"\nPatient Question: {user_question}")
        
        # Clear instruction to answer the specific question
        prompt_parts.append(
            "\nProvide a concise, direct answer to the patient's question above. "
            "Include relevant guidance about their risk level and symptoms. "
            "Do NOT repeat disclaimers or metadata - those are handled by the UI. "
            "Do NOT reference previous conversations."
        )
        
        user_prompt = "\n".join(prompt_parts)
        
        # Attempt API call with retry logic
        last_exception = None
        for attempt in range(max_retries):
            try:
                # Generate response - completely stateless, no chat history
                response = self.model.generate_content(
                    contents=user_prompt,
                    generation_config=self.generation_config
                )
                
                # Extract and validate response
                if response and response.text:
                    advice_text = response.text.strip()
                    
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
