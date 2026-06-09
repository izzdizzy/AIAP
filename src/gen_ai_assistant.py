"""
Gen AI Care Navigation Assistant for Chronic Condition Patients
================================================================
Singapore Healthcare Context

This module provides an LLM-powered care navigation assistant that translates
ML-predicted readmission risk scores into actionable healthcare guidance
aligned with Singapore's healthcare system.

Features:
- System prompt with Singapore healthcare knowledge base
- Structured risk score injection
- Triage recommendations based on risk levels
- Plain English output for patients and caregivers
- Integration with CHAS tiers, Healthier SG, and MAF schemes

Author: AIAP Team
Date: 2024
"""

import os
import json
from typing import Dict, Optional, Any
from pathlib import Path


try:
    from google import genai
    from google.genai import types
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False


class SingaporeHealthcareKnowledgeBase:
    """
    Knowledge base containing Singapore healthcare system information.
    
    Includes:
    - CHAS (Community Health Assist Scheme) tiers and subsidies
    - Healthier SG enrolment process
    - Care provider routing rules (GP vs Polyclinic vs Specialist)
    - MediSave/MediShield Life/MediFund (MAF) basics
    - Emergency and hotline contacts
    """
    
    def __init__(self, knowledge_file: Optional[str] = None):
        """
        Initialize the knowledge base.
        
        Args:
            knowledge_file: Path to JSON file with custom knowledge base.
                           If None, uses built-in knowledge.
        """
        self.knowledge_file = knowledge_file
        self.knowledge = self._load_knowledge()
    
    def _load_knowledge(self) -> Dict[str, Any]:
        """Load knowledge base from file or use built-in defaults."""
        if self.knowledge_file and os.path.exists(self.knowledge_file):
            with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return self._get_builtin_knowledge()
    
    def _get_builtin_knowledge(self) -> Dict[str, Any]:
        """Return built-in Singapore healthcare knowledge base."""
        return {
            "chas_tiers": {
                "CHAS Blue": {
                    "description": "Highest subsidy tier for lower-income households",
                    "subsidies": {
                        "acute_conditions": "Up to SGD $21.50 per visit",
                        "chronic_conditions": "Up to SGD $72.50 per visit",
                        "dental_care": "Up to SGD $262.50 per year"
                    },
                    "eligibility": "Household monthly income per person ≤ SGD $1,300"
                },
                "CHAS Orange": {
                    "description": "Medium subsidy tier",
                    "subsidies": {
                        "acute_conditions": "Up to SGD $16.50 per visit",
                        "chronic_conditions": "Up to SGD $52.50 per visit",
                        "dental_care": "Up to SGD $192.50 per year"
                    },
                    "eligibility": "Household monthly income per person SGD $1,301 - $2,000"
                },
                "CHAS Green": {
                    "description": "Basic subsidy tier for middle-income",
                    "subsidies": {
                        "acute_conditions": "Up to SGD $11.50 per visit",
                        "chronic_conditions": "Up to SGD $32.50 per visit"
                    },
                    "eligibility": "Household monthly income per person SGD $2,001 - $3,000 OR all Singaporeans with annual value of home ≤ SGD $21,000"
                },
                "Merdeka Generation": {
                    "description": "Special tier for those born 1950-1959",
                    "subsidies": {
                        "chronic_conditions": "Additional SGD $20 per visit on top of CHAS",
                        "medi_save_top_up": "SGD $200 annually",
                        "specialist_outpatient": "50% subsidy at polyclinics"
                    },
                    "eligibility": "Singaporeans born between 1950-1959"
                },
                "Pioneer Generation": {
                    "description": "Highest priority tier for seniors born before 1950",
                    "subsidies": {
                        "chronic_conditions": "Additional SGD $25 per visit on top of CHAS",
                        "medi_save_top_up": "SGD $250 annually",
                        "specialist_outpatient": "50% subsidy at polyclinics",
                        "home_care": "Subsidies for home nursing and day rehab"
                    },
                    "eligibility": "Singaporeans born on or before 31 Dec 1949"
                }
            },
            "healthier_sg": {
                "description": "National initiative for preventive care and chronic disease management",
                "enrolment_process": [
                    "Choose a Healthier SG GP clinic near you",
                    "Attend first appointment for health review",
                    "Develop personalized health plan with GP",
                    "Receive regular follow-ups and screenings"
                ],
                "benefits": [
                    "Free initial health review",
                    "Subsidized chronic disease medications",
                    "Healthier SG screening tests",
                    "Continuity of care with same GP"
                ],
                "eligibility": "All Singaporeans and Permanent Residents aged 40+",
                "website": "https://www.healthier.sg"
            },
            "care_routing_rules": {
                "low_risk_followup": {
                    "condition": "Readmission risk < 0.3, stable condition",
                    "recommendation": "Schedule follow-up with GP or CHAS clinic within 2-4 weeks",
                    "rationale": "Primary care sufficient for routine monitoring"
                },
                "medium_risk_followup": {
                    "condition": "Readmission risk 0.3-0.6, multiple chronic conditions",
                    "recommendation": "Refer to polyclinic chronic disease program within 1-2 weeks",
                    "rationale": "Polyclinics offer multidisciplinary care for complex cases"
                },
                "high_risk_followup": {
                    "condition": "Readmission risk > 0.6, recent hospitalization",
                    "recommendation": "Urgent specialist review within 1 week + consider transitional care program",
                    "rationale": "High risk requires intensive monitoring and specialist input"
                },
                "emergency_referral": {
                    "condition": "Risk > 0.8 OR acute symptoms present",
                    "recommendation": "Immediate A&E assessment or call 995",
                    "rationale": "Patient safety priority - rule out acute complications"
                },
                "chas_routing": {
                    "Blue/Orange": "Encourage CHAS GP enrollment for subsidized care",
                    "Green": "Consider polyclinic for higher subsidies on chronic meds",
                    "Merdeka/Pioneer": "Maximize generation-specific benefits at any provider"
                }
            },
            "maf_schemes": {
                "MediSave": {
                    "description": "National medical savings scheme using CPF contributions",
                    "usage": "Can be used for hospitalization, day surgery, certain outpatient treatments",
                    "withdrawal_limits": "Varies by procedure; chronic disease management up to SGD $600/year",
                    "eligibility": "All working Singaporeans and PRs"
                },
                "MediShield Life": {
                    "description": "Compulsory basic health insurance for all Singaporeans/PRs",
                    "coverage": "Large hospital bills, selected expensive outpatient treatments",
                    "claims": "Automatic claims at public hospitals; submit manually for private",
                    "eligibility": "All Singapore citizens and PRs (mandatory)"
                },
                "MediFund": {
                    "description": "Safety net for needy Singaporeans unable to pay medical bills",
                    "coverage": "Outstanding bills after MediSave and MediShield Life",
                    "application": "Apply through Medical Social Worker at hospital",
                    "eligibility": "Singaporeans with financial need; assessed case-by-case"
                }
            },
            "emergency_contacts": {
                "ambulance": "995",
                "police": "999",
                "healthhub_hotline": "1800-2255-533 (Mon-Fri 8am-6pm)",
                "ncis_24hr": "6222 3322 (National Cancer Centre)",
                "sgfh_24hr": "6385 5888 (Singapore General Hospital)",
                "nuh_24hr": "6772 2255 (National University Hospital)",
                "ttsh_24hr": "6357 7000 (Tan Tock Seng Hospital)",
                "mental_health_helpline": "1800-531 4767 (Institute of Mental Health)",
                "silver_line": "1800-350 6530 (Elderly support hotline)"
            },
            "polyclinics": {
                "description": "Government primary care clinics offering subsidized services",
                "services": [
                    "Chronic disease management",
                    "Health screenings",
                    "Vaccinations",
                    "Minor procedures",
                    "Referrals to specialists"
                ],
                "locations": [
                    "Ang Mo Kio", "Bedok", "Bukit Batok", "Bukit Merah",
                    "Choa Chu Kang", "Geylang", "Hougang", "Jurong",
                    "Kallang", "Pasir Ris", "Queenstown", "Sengkang",
                    "Toa Payoh", "Woodlands", "Yishun"
                ]
            }
        }
    
    def get_knowledge_summary(self) -> str:
        """Return a formatted summary of key knowledge for system prompt."""
        kb = self.knowledge
        
        summary = """SINGAPORE HEALTHCARE KNOWLEDGE BASE:

CHAS SUBSIDY TIERS:
- CHAS Blue: Highest subsidies (≤$1,300/month per person)
- CHAS Orange: Medium subsidies ($1,301-$2,000/month)
- CHAS Green: Basic subsidies ($2,001-$3,000/month)
- Merdeka Generation: Born 1950-1959, extra $20/visit + $200 MediSave/year
- Pioneer Generation: Born ≤1949, extra $25/visit + $250 MediSave/year

HEALTHIER SG:
- Enrol with a GP for preventive care and chronic disease management
- Free initial health review, subsidized medications, regular follow-ups
- All Singaporeans/PRs aged 40+ eligible

CARE ROUTING RULES:
- Low risk (<0.3): GP follow-up in 2-4 weeks
- Medium risk (0.3-0.6): Polyclinic chronic disease program in 1-2 weeks
- High risk (>0.6): Specialist review within 1 week + transitional care
- Very high risk (>0.8) or acute symptoms: A&E immediately or call 995

FINANCIAL ASSISTANCE (MAF):
- MediSave: Use CPF savings for medical expenses
- MediShield Life: Insurance for large hospital bills (mandatory)
- MediFund: Safety net for needy patients (apply via Medical Social Worker)

EMERGENCY CONTACTS:
- Ambulance: 995
- HealthHub Hotline: 1800-2255-533
- Silver Line (Elderly): 1800-350 6530
"""
        return summary


class CareNavigationAssistant:
    """
    LLM-powered Care Navigation Assistant for chronic condition patients.
    
    This assistant takes ML-generated risk scores and patient profiles,
    then generates personalized care navigation recommendations using
    Singapore healthcare knowledge.
    """
    
    def __init__(
        self,
        knowledge_base: Optional[SingaporeHealthcareKnowledgeBase] = None,
        llm_api_key: Optional[str] = None,
        model_name: str = "gemini-2.0-flash"
    ):
        """
        Initialize the Care Navigation Assistant.
        
        Args:
            knowledge_base: SingaporeHealthcareKnowledgeBase instance
            llm_api_key: Google AI API key (or set GOOGLE_API_KEY env var)
            model_name: LLM model to use (default: gemini-2.0-flash)
        """
        self.knowledge_base = knowledge_base or SingaporeHealthcareKnowledgeBase()
        self.model_name = model_name
        self.api_key = llm_api_key or os.environ.get("GOOGLE_API_KEY")
        
        # Check if API key is available
        self._api_available = self.api_key is not None and len(self.api_key) > 10
        
        # Initialize Google AI client if available
        if GOOGLE_AI_AVAILABLE and self._api_available:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt with Singapore healthcare knowledge."""
        kb_summary = self.knowledge_base.get_knowledge_summary()
        
        system_prompt = f"""You are a Care Navigation Assistant for chronic condition patients in Singapore.

YOUR ROLE:
- Translate ML-predicted readmission risk scores into actionable healthcare guidance
- Provide clear, empathetic recommendations in plain English (max 200 words)
- Align recommendations with Singapore's healthcare system (CHAS, Healthier SG, MAF)
- Prioritize patient safety while avoiding unnecessary alarm

KNOWLEDGE BASE:
{kb_summary}

OUTPUT FORMAT:
Structure your response as:
1. RISK LEVEL: [Low/Medium/High/Urgent]
2. RECOMMENDED ACTION: [Specific next step with timeframe]
3. CARE PROVIDER: [GP/Polyclinic/Specialist/A&E based on risk and CHAS tier]
4. FINANCIAL GUIDANCE: [Relevant subsidies/schemes if applicable]
5. CONTACT INFO: [Relevant hotline or facility]

IMPORTANT GUIDELINES:
- For risk > 0.8 or mention of acute symptoms: Recommend immediate medical attention
- Always mention specific timeframes (e.g., "within 1 week", "within 24 hours")
- Consider patient's CHAS tier when recommending providers
- Use encouraging but realistic tone
- Never diagnose - only provide navigation guidance
- If uncertain, recommend consulting a healthcare professional
"""
        return system_prompt
    
    def _build_user_prompt(
        self,
        readmission_score: float,
        diabetes_risk: Optional[float] = None,
        hypertension_score: Optional[float] = None,
        health_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build the user prompt with patient-specific information.
        
        Args:
            readmission_score: ML-predicted probability of 30-day readmission (0-1)
            diabetes_risk: Optional diabetes-specific risk score (0-1)
            hypertension_score: Optional hypertension risk score (0-1)
            health_profile: Dict with patient demographics and preferences
            
        Returns:
            Formatted user prompt string
        """
        # Determine risk level
        if readmission_score >= 0.8:
            risk_level = "VERY HIGH"
        elif readmission_score >= 0.6:
            risk_level = "HIGH"
        elif readmission_score >= 0.3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Extract profile info
        profile = health_profile or {}
        age = profile.get("age", "Not specified")
        chas_tier = profile.get("chas_tier", "Not specified")
        has_diabetes = profile.get("has_diabetes", False)
        has_hypertension = profile.get("has_hypertension", False)
        preferred_provider = profile.get("preferred_provider", "Any")
        
        user_prompt = f"""PATIENT INFORMATION:

Readmission Risk Score: {readmission_score:.2f} ({risk_level} RISK)
"""
        
        if diabetes_risk is not None:
            user_prompt += f"Diabetes Risk Score: {diabetes_risk:.2f}\n"
        
        if hypertension_score is not None:
            user_prompt += f"Hypertension Risk Score: {hypertension_score:.2f}\n"
        
        user_prompt += f"""
Patient Profile:
- Age: {age}
- CHAS Tier: {chas_tier}
- Has Diabetes: {'Yes' if has_diabetes else 'No'}
- Has Hypertension: {'Yes' if has_hypertension else 'No'}
- Preferred Provider: {preferred_provider}

TASK:
Based on the risk scores and patient profile above, provide a personalized care navigation recommendation following the output format in the system instructions.

Consider:
1. The urgency based on readmission risk level
2. Appropriate care provider based on CHAS tier and complexity
3. Relevant financial assistance schemes
4. Specific actionable next steps with timeframes
"""
        
        return user_prompt
    
    def generate_recommendation(
        self,
        readmission_score: float,
        diabetes_risk: Optional[float] = None,
        hypertension_score: Optional[float] = None,
        health_profile: Optional[Dict[str, Any]] = None,
        max_tokens: int = 300
    ) -> Dict[str, Any]:
        """
        Generate a care navigation recommendation.
        
        Args:
            readmission_score: ML-predicted probability of 30-day readmission (0-1)
            diabetes_risk: Optional diabetes-specific risk score (0-1)
            hypertension_score: Optional hypertension risk score (0-1)
            health_profile: Dict with patient demographics and preferences
            max_tokens: Maximum tokens in response
            
        Returns:
            Dict with keys: 'recommendation' (str), 'risk_level' (str), 
                          'success' (bool), 'error' (optional str)
        """
        # Validate inputs
        if not 0 <= readmission_score <= 1:
            return {
                "recommendation": "",
                "risk_level": "INVALID",
                "success": False,
                "error": f"Invalid readmission_score: {readmission_score}. Must be between 0 and 1."
            }
        
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            readmission_score,
            diabetes_risk,
            hypertension_score,
            health_profile
        )
        
        # Determine risk level for response
        if readmission_score >= 0.8:
            risk_level = "URGENT"
        elif readmission_score >= 0.6:
            risk_level = "HIGH"
        elif readmission_score >= 0.3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # If API not available, use rule-based fallback
        if not self._api_available:
            recommendation = self._rule_based_recommendation(
                readmission_score,
                health_profile
            )
            return {
                "recommendation": recommendation,
                "risk_level": risk_level,
                "success": True,
                "note": "Generated using rule-based system (LLM API not configured)"
            }
        
        # Use Google AI API if client is initialized
        if self.client is not None:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=f"{system_prompt}\n\n{user_prompt}",
                    config=types.GenerateContentConfig(
                        max_output_tokens=max_tokens,
                        temperature=0.7
                    )
                )
                
                recommendation = response.text.strip()
                
                return {
                    "recommendation": recommendation,
                    "risk_level": risk_level,
                    "success": True,
                    "model_used": self.model_name
                }
                
            except Exception as e:
                # Fallback to rule-based if API call fails
                print(f"Google AI API call failed: {e}. Using rule-based fallback.")
                recommendation = self._rule_based_recommendation(
                    readmission_score,
                    health_profile
                )
                return {
                    "recommendation": recommendation,
                    "risk_level": risk_level,
                    "success": True,
                    "note": f"Generated using rule-based system (API error: {str(e)})"
                }
        else:
            # Use rule-based system when no API key
            recommendation = self._rule_based_recommendation(
                readmission_score,
                health_profile
            )
            return {
                "recommendation": recommendation,
                "risk_level": risk_level,
                "success": True,
                "note": "Generated using rule-based system (LLM API not configured)"
            }
    
    def _rule_based_recommendation(
        self,
        readmission_score: float,
        health_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate recommendation using rule-based logic (fallback when LLM unavailable).
        
        Args:
            readmission_score: ML-predicted probability of 30-day readmission (0-1)
            health_profile: Dict with patient demographics
            
        Returns:
            Formatted recommendation string
        """
        profile = health_profile or {}
        chas_tier = profile.get("chas_tier", "Not specified")
        age = profile.get("age", "Not specified")
        
        # Determine recommendation based on risk level
        if readmission_score >= 0.8:
            recommendation = f"""RISK LEVEL: URGENT

RECOMMENDED ACTION: Seek immediate medical attention. Go to nearest A&E or call 995 if experiencing severe symptoms.

CARE PROVIDER: Accident & Emergency Department

FINANCIAL GUIDANCE: Emergency care is prioritized over cost concerns. MediShield Life will cover eligible expenses. Apply for MediFund assistance if needed via hospital Medical Social Worker.

CONTACT INFO: 
- Ambulance: 995
- Nearest A&E: Call 1800-2255-533 for directions

Note: Your high risk score indicates need for urgent clinical assessment. Do not delay seeking care."""

        elif readmission_score >= 0.6:
            provider = "Polyclinic Chronic Disease Program" if chas_tier in ["CHAS Green", "Not specified"] else "CHAS GP Clinic"
            timeframe = "within 1 week"
            
            recommendation = f"""RISK LEVEL: HIGH

RECOMMENDED ACTION: Schedule urgent follow-up appointment {timeframe}. Contact your primary care provider or enroll in a transitional care program.

CARE PROVIDER: {provider}

FINANCIAL GUIDANCE: 
- CHAS subsidies apply for GP visits
- Polyclinic consultations subsidized for all Singaporeans
- Consider Healthier SG enrolment for ongoing care coordination
- MediSave can be used for certain outpatient treatments

CONTACT INFO:
- HealthHub Hotline: 1800-2255-533 (find nearest clinic)
- Silver Line (if age 60+): 1800-350 6530

Note: Early intervention can prevent readmission. Bring all medication lists to your appointment."""

        elif readmission_score >= 0.3:
            provider = "Polyclinic" if chas_tier == "CHAS Green" else "CHAS GP"
            timeframe = "within 1-2 weeks"
            
            recommendation = f"""RISK LEVEL: MEDIUM

RECOMMENDED ACTION: Schedule follow-up appointment {timeframe} for medication review and care plan optimization.

CARE PROVIDER: {provider}

FINANCIAL GUIDANCE:
- CHAS {chas_tier if chas_tier != "Not specified" else "subsidies"} available
- Healthier SG enrolment recommended for coordinated care
- Regular medications may be subsidized under chronic disease programs

CONTACT INFO:
- Find CHAS clinic: https://www.chas.com.sg
- Healthier SG: https://www.healthier.sg

Note: Consistent follow-up and medication adherence are key to preventing readmission."""

        else:
            timeframe = "within 2-4 weeks"
            
            recommendation = f"""RISK LEVEL: LOW

RECOMMENDED ACTION: Schedule routine follow-up {timeframe}. Continue current medications and healthy lifestyle practices.

CARE PROVIDER: Primary Care GP or Polyclinic

FINANCIAL GUIDANCE:
- Standard CHAS subsidies apply
- Consider Healthier SG enrolment for preventive care benefits
- Annual health screening recommended

CONTACT INFO:
- HealthHub: 1800-2255-533
- Healthier SG portal: https://www.healthier.sg

Note: Maintain good glycemic control, regular exercise, and attend scheduled appointments to keep risk low."""

        return recommendation


def generate_care_navigation(
    readmission_score: float,
    diabetes_risk: Optional[float] = None,
    hypertension_score: Optional[float] = None,
    health_profile: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None
) -> str:
    """
    Convenience function to generate care navigation recommendation.
    
    Args:
        readmission_score: ML-predicted probability of 30-day readmission (0-1)
        diabetes_risk: Optional diabetes-specific risk score (0-1)
        hypertension_score: Optional hypertension risk score (0-1)
        health_profile: Dict with patient demographics and preferences
        api_key: Optional OpenAI API key
        
    Returns:
        Care navigation recommendation string
    """
    assistant = CareNavigationAssistant(llm_api_key=api_key)
    result = assistant.generate_recommendation(
        readmission_score=readmission_score,
        diabetes_risk=diabetes_risk,
        hypertension_score=hypertension_score,
        health_profile=health_profile
    )
    
    return result["recommendation"]


if __name__ == "__main__":
    # Test the Care Navigation Assistant
    print("="*80)
    print("CARE NAVIGATION ASSISTANT - TEST DEMO")
    print("="*80)
    
    # Test Case 1: High-risk elderly patient
    print("\n" + "="*80)
    print("TEST CASE 1: High-Risk Elderly Patient (Pioneer Generation)")
    print("="*80)
    
    test_profile_1 = {
        "age": 78,
        "chas_tier": "Pioneer Generation",
        "has_diabetes": True,
        "has_hypertension": True,
        "preferred_provider": "Polyclinic"
    }
    
    result_1 = generate_care_navigation(
        readmission_score=0.75,
        diabetes_risk=0.82,
        hypertension_score=0.68,
        health_profile=test_profile_1
    )
    
    print(result_1)
    
    # Test Case 2: Medium-risk middle-aged patient
    print("\n" + "="*80)
    print("TEST CASE 2: Medium-Risk Middle-Aged Patient (CHAS Blue)")
    print("="*80)
    
    test_profile_2 = {
        "age": 52,
        "chas_tier": "CHAS Blue",
        "has_diabetes": True,
        "has_hypertension": False,
        "preferred_provider": "GP"
    }
    
    result_2 = generate_care_navigation(
        readmission_score=0.45,
        diabetes_risk=0.55,
        hypertension_score=0.30,
        health_profile=test_profile_2
    )
    
    print(result_2)
    
    # Test Case 3: Low-risk patient
    print("\n" + "="*80)
    print("TEST CASE 3: Low-Risk Patient (CHAS Green)")
    print("="*80)
    
    test_profile_3 = {
        "age": 45,
        "chas_tier": "CHAS Green",
        "has_diabetes": True,
        "has_hypertension": True,
        "preferred_provider": "Any"
    }
    
    result_3 = generate_care_navigation(
        readmission_score=0.18,
        diabetes_risk=0.25,
        hypertension_score=0.22,
        health_profile=test_profile_3
    )
    
    print(result_3)
    
    # Test Case 4: Urgent risk patient
    print("\n" + "="*80)
    print("TEST CASE 4: Urgent Risk Patient (Requires Immediate Attention)")
    print("="*80)
    
    test_profile_4 = {
        "age": 68,
        "chas_tier": "Merdeka Generation",
        "has_diabetes": True,
        "has_hypertension": True,
        "preferred_provider": "Any"
    }
    
    result_4 = generate_care_navigation(
        readmission_score=0.89,
        diabetes_risk=0.91,
        hypertension_score=0.85,
        health_profile=test_profile_4
    )
    
    print(result_4)
    
    print("\n" + "="*80)
    print("DEMO COMPLETE")
    print("="*80)
    print("\nNote: Recommendations generated using rule-based system.")
    print("To use LLM-powered recommendations, set GOOGLE_API_KEY environment variable.")
    print("Install the Google AI SDK: pip install google-genai")
