"""
Care Navigator Service Module
Triage Care Guidance and Dynamic Google Maps Link Generator for Healthcare Navigation.
"""

from urllib.parse import quote_plus
from typing import Dict, Any, Optional, List
from .client import genai_client
from .context_builder import UnifiedPatientContext, build_unified_context, format_conversation_history
import re


def build_google_maps_url(subsidy_tier: Optional[str], facility_type: str = "Polyclinic") -> str:
    """
    Constructs dynamic Google Maps search URLs matching the pattern:
    https://www.google.com/maps/search/?api=1&query={Subsidy_Tier}+{Facility_Type}+near+me
    Omits subsidy tier if unprovided or not specified.
    """
    tier_str = (subsidy_tier or "").strip()
    if not tier_str or tier_str.lower() in ("not provided", "unprovided", "none", "n/a", "not_provided"):
        query_str = f"{facility_type} near me"
    else:
        query_str = f"{tier_str} {facility_type} near me"
    encoded_query = quote_plus(query_str)
    return f"https://www.google.com/maps/search/?api=1&query={encoded_query}"

class CareNavigatorService:
    """
    Care navigator assistant for patient triage, post-discharge navigation,
    and Singapore healthcare scheme routing (CHAS, Healthier SG, Polyclinics).
    """

    def generate_navigation_advice(
        self,
        context: UnifiedPatientContext,
        user_query: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generates care triage advice with dynamic CLINIC_MAP_LINK or TRIAGE_CHECKLIST widget.
        """
        query_str = user_query or "Where should I seek medical care given my current symptoms and subsidy tier?"
        history_str = format_conversation_history(history)

        subsidy = context.demographics.subsidy_tier or "CHAS Green"
        urgency = context.ml_scores.readmission_risk_level or "Routine Monitoring"
        symptoms = context.form_metrics.active_symptoms

        facility_type = "Hospital Emergency Department" if urgency == "Immediate Intervention" else "Polyclinic"
        maps_url = build_google_maps_url(subsidy, facility_type)

        system_prompt = f"""
You are the Care Navigator & Triage Assistant for Singapore healthcare patients.
Your role is to evaluate the patient's symptoms, clinical severity scores, and subsidy tier to guide them to the right healthcare facility.

GLOBAL SYSTEM PERSONA & RESPONSE TONE RULES:
1. CONCISENESS: strictly UNDER 150 WORDS using clean Markdown bullet points.
2. DIRECT SECOND-PERSON TONE: Always address the patient directly using "you" / "your". NEVER use third-person clinical jargon.
3. MEDICAL DISCLAIMER: Avoid diagnostic statements. Focus strictly on decision support and triage.

INSTRUCTION: If you mention a scheme (e.g. "Visit a CHAS clinic"), you MUST format it as "Visit a [CHAS](https://www.chas.sg) clinic". Do not output raw URLs.

DYNAMIC CONTEXT:
- Maps URL: {maps_url}
- Patient Subsidy Tier: {subsidy}
- Urgency: {urgency}
- Symptoms: {', '.join(symptoms) if symptoms else 'None'}

REQUIRED JSON SCHEMA:
{{
  "message": "<Care triage narrative. MUST include markdown links from Knowledge Base if schemes are mentioned.>",
  "widget": {{
    "type": "CLINIC_MAP_LINK" | "TRIAGE_CHECKLIST",
    "data": {{ ... }}
  }}
}}

WIDGET SPECIFICATIONS:
- If type is "CLINIC_MAP_LINK":
  data: {{
    "facility_type": "{facility_type}",
    "subsidy_tier": "{subsidy}",
    "url": "{maps_url}",
    "label": "Find Nearby {subsidy} {facility_type}s"
  }}
- If type is "TRIAGE_CHECKLIST":
  data: {{
    "title": "Post-Discharge Care Navigation Checklist",
    "urgency": "{urgency}",
    "tasks": [
      {{"id": "1", "task": "Book follow-up appointment at nearest Polyclinic / CHAS GP", "completed": false}},
      {{"id": "2", "task": "Bring current discharge medication list to consultation", "completed": false}}
    ]
  }}
"""

        prompt = f"""
PATIENT CONTEXT:
{context.to_prompt_summary()}

CONVERSATION HISTORY SUMMARY:
{history_str}

PATIENT QUERY:
{query_str}

Please generate the JSON response now.
"""

        fallback_widget = {
            "type": "CLINIC_MAP_LINK",
            "data": {
                "facility_type": facility_type,
                "subsidy_tier": subsidy,
                "url": maps_url,
                "label": f"Find Nearby {subsidy} {facility_type}s on Google Maps"
            }
        }

        fallback_payload = {
            "message": (
                f"**Care Navigation Assessment ({urgency})**:\n\n"
                f"Based on your clinical severity score ({context.ml_scores.readmission_severity_score or '30'}/100) and reported symptoms, "
                f"we recommend seeking consultation at a subsidized healthcare facility matching your **{subsidy}** status.\n\n"
                f"**Recommended Action**:\n"
                f"- If experiencing acute chest pain or severe shortness of breath, go immediately to the nearest A&E or call 995.\n"
                f"- For routine or moderate follow-up, book an appointment at your enrolled Healthier SG GP or local Polyclinic."
            ),
            "widget": fallback_widget
        }

        return genai_client.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
            fallback_data=fallback_payload
        )


def get_care_navigator_service() -> CareNavigatorService:
    return CareNavigatorService()
