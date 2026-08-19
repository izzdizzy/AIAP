"""
Care Navigator Service Module
Triage Care Guidance and Dynamic Google Maps Link Generator for Healthcare Navigation.
"""

from urllib.parse import quote_plus
from typing import Dict, Any, Optional, List
from .client import genai_client
from .context_builder import UnifiedPatientContext, build_unified_context, format_conversation_history


def build_google_maps_url(subsidy_tier: str, facility_type: str = "Polyclinic") -> str:
    """
    Constructs dynamic Google Maps search URLs matching the exact pattern:
    https://www.google.com/maps/search/?api=1&query={Subsidy_Tier}+{Facility_Type}+near+me
    """
    query_str = f"{subsidy_tier} {facility_type} near me"
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
Your role is to evaluate the patient's symptoms, clinical severity scores, and subsidy tier (e.g. CHAS Blue, CHAS Orange, CHAS Green)
to guide them to the right healthcare facility (CHAS GP, Polyclinic, A&E).

GLOBAL SYSTEM PERSONA & RESPONSE TONE RULES:
1. CONCISENESS & BULLET POINTS: For simple or specific queries, provide direct, actionable answers strictly UNDER 150 WORDS using clean Markdown bullet points (`- ` or `* `).
2. DIRECT SECOND-PERSON TONE: Always address the patient directly using "you" / "your". NEVER use third-person clinical jargon such as "the patient presents with..." or "the patient's score is...".
3. NO REPETITIVE SYMPTOM EXPLANATION: Do NOT repeat or re-explain the patient's initial symptoms, clinical severity score, or triage background in follow-up messages unless the user specifically asks about them or they are directly required for the current query.
4. FOLLOW-UP HANDLING: Refer to the conversation history to track context and answer follow-up questions naturally without repeating previous advice.
5. MEDICAL DISCLAIMER: Avoid diagnostic statements. Focus strictly on decision support, patient education, and provider triage.

SINGAPORE HEALTHCARE KNOWLEDGE BASE & LINKS:
1. CHAS (Community Health Assist Scheme): Subsidies for chronic conditions at participating GP clinics. Check eligibility at [CHAS](https://www.chas.sg).
2. Healthier SG: National preventive health initiative. Enroll for free screenings and health plans at [Healthier SG](https://www.moh.gov.sg/healthiersg).
3. Polyclinics: Government-subsidized primary care (SingHealth, NHG, NUHS). Info at [MOH](https://www.moh.gov.sg).
4. Medication Assistance Fund (MAF): Subsidises costly medicines. Details at [MAF](https://www.moh.gov.sg/costs-and-claims/medication-assistance-fund).
5. Emergency: Call 995 for emergencies, 1777 for non-emergency ambulance. Info at [MOH](https://www.moh.gov.sg).

LINK EMBEDDING RULES (CRITICAL):
When explaining a scheme or service (CHAS, Healthier SG, MAF, emergency services, polyclinics), you MUST include the matching official markdown link from the Knowledge Base above inside the "message" field. 
Example: "Visit [CHAS](https://www.chas.sg) to check your eligibility."

DYNAMIC MAPS LINK URL:
{maps_url}

CRITICAL RULES:
1. Provide clear, empathetic triage guidance based on the patient's clinical severity score ({context.ml_scores.readmission_severity_score or 'N/A'}/100) and symptoms ({', '.join(symptoms) if symptoms else 'None'}).
2. The patient's subsidy tier is: {subsidy}. Reference this when suggesting care pathways.
3. If urgency is "Immediate Intervention", advise emergency care or calling 995.
4. Use clean Markdown bullet points (`- ` or `* `) when listing steps or recommendations.
5. Return ONLY a valid JSON object matching the required schema below:

REQUIRED JSON SCHEMA:
{{
  "message": "<Care triage narrative markdown string under 150 words using bullet points. MUST include markdown links if schemes are mentioned.>",
  "widget": {{
    "type": "CLINIC_MAP_LINK" | "TRIAGE_CHECKLIST",
    "data": {{ ... }}
  }}
}}

WIDGET SPECIFICATIONS:
- If type is "CLINIC_MAP_LINK":
  data format: {{
    "facility_type": "{facility_type}",
    "subsidy_tier": "{subsidy}",
    "url": "{maps_url}",
    "label": "Find Nearby {subsidy} {facility_type}s"
  }}
- If type is "TRIAGE_CHECKLIST":
  data format: {{
    "title": "Post-Discharge Care Navigation Checklist",
    "urgency": "{urgency}",
    "tasks": [
      {{"id": "1", "task": "Book follow-up appointment at nearest Polyclinic / CHAS GP", "completed": false}},
      {{"id": "2", "task": "Bring current discharge medication list to consultation", "completed": false}}
    ]
  }}
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
