"""
CAD Coach Service Module
RAG-backed lifestyle & diet advisor for Coronary Artery Disease (CAD) management.
Injects local knowledge base .txt files into system prompts.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from .client import genai_client
from .context_builder import UnifiedPatientContext, build_unified_context


class CADCoachService:
    """
    RAG-backed CAD lifestyle and dietary coaching assistant.
    Grounds recommendations in local HealthHub/MOH knowledge documents.
    """

    def __init__(self):
        self.knowledge_text = self._load_knowledge_base()

    def _load_knowledge_base(self) -> str:
        """Loads and aggregates all .txt knowledge files from backend/data/knowledge_base/."""
        kb_dir = Path(__file__).parent.parent.parent / "data" / "knowledge_base"
        fallback_dir = Path(__file__).parent.parent / "features" / "cad" / "documents"

        docs: List[str] = []
        target_dirs = [kb_dir, fallback_dir]

        for d in target_dirs:
            if d.exists() and d.is_dir():
                for txt_file in d.glob("*.txt"):
                    if txt_file.name == "system_prompt.txt":
                        continue
                    try:
                        content = txt_file.read_text(encoding="utf-8").strip()
                        if content:
                            docs.append(f"--- DOCUMENT: {txt_file.name} ---\n{content}")
                    except Exception as e:
                        print(f"[CADCoachService] Could not read {txt_file}: {e}")

        if docs:
            return "\n\n".join(docs)
        return "Standard Singapore HealthHub dietary guidelines: reduce saturated fats, lower sodium <2000mg/day, engage in 150 mins exercise weekly."

    def generate_advice(
        self,
        context: UnifiedPatientContext,
        user_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates grounded CAD coaching advice with optional structured widget payload.
        """
        query_str = user_query or "Provide lifestyle, dietary, and exercise recommendations based on my CAD risk metrics."

        system_prompt = f"""
You are the CAD Specialist & Lifestyle Coach, an expert cardiovascular health advisor for Singapore patients.
Your role is to give practical, evidence-backed lifestyle, exercise, and dietary guidance tailored to the patient's specific risk metrics.

GLOBAL SYSTEM PERSONA & RESPONSE TONE RULES:
1. CONCISENESS: For simple or specific queries, provide direct, actionable answers strictly UNDER 150 WORDS using clean Markdown bullet points.
2. DIRECT SECOND-PERSON TONE: Always address the patient directly using "you" / "your". NEVER use third-person clinical jargon such as "the patient presents with..." or "the patient's cholesterol is...".
3. MEDICAL DISCLAIMER: Avoid diagnostic statements. Focus strictly on clinical decision support, health education, and provider triage.

VALIDATED KNOWLEDGE BASE GUIDELINES:
{self.knowledge_text}

CRITICAL FORMATTING RULES:
1. Base your dietary and lifestyle advice directly on the validated knowledge base guidelines above.
2. Address specific patient metrics (e.g., cholesterol, blood pressure, BMI, active symptoms).
3. Always respond with a strictly formatted JSON object matching the schema below:

REQUIRED JSON SCHEMA:
{{
  "message": "<Markdown explanation under 150 words with direct 'you/your' tone and bullet points>",
  "widget": {{
    "type": "COPYABLE_DOCTOR_QUESTIONS" | "SHAP_FACTOR_CARD" | "TRIAGE_CHECKLIST",
    "data": {{ ... }}
  }}
}}

WIDGET SPECIFICATIONS:
- If type is "COPYABLE_DOCTOR_QUESTIONS":
  data format: {{ "title": "Questions for Your Doctor", "questions": ["Question 1?", "Question 2?", "Question 3?"] }}
- If type is "SHAP_FACTOR_CARD":
  data format: {{ "overall_risk": "{context.ml_scores.cad_risk_level or 'Moderate'}", "factors": [ {{"name": "Cholesterol", "value": "{context.form_metrics.cholesterol or 'High'} mg/dL", "impact": "+0.350", "type": "risk_driver"}} ] }}
- If type is "TRIAGE_CHECKLIST":
  data format: {{ "title": "Heart Health Action Checklist", "urgency": "Routine Monitoring", "tasks": [ {{"id": "1", "task": "Swap palm oil/butter for olive oil in daily meals", "completed": false}} ] }}
"""

        prompt = f"""
PATIENT CONTEXT:
{context.to_prompt_summary()}

PATIENT QUESTION:
{query_str}

Please generate the JSON response now.
"""

        fallback_widget = {
            "type": "COPYABLE_DOCTOR_QUESTIONS",
            "data": {
                "title": "Heart Health Questions for Your Doctor",
                "questions": [
                    "How can I safely lower my LDL cholesterol through diet and exercise?",
                    "Is my blood pressure reading within a safe range for my age group?",
                    "Should I undergo additional cardiovascular diagnostic testing?"
                ]
            }
        }

        fallback_payload = {
            "message": (
                f"Based on your CAD assessment metrics (Risk Level: {context.ml_scores.cad_risk_level or 'Assessed'}), "
                f"here are key cardiovascular lifestyle recommendations:\n\n"
                f"**Dietary Adjustments**:\n"
                f"- Reduce saturated and trans fats by choosing healthier unsaturated oils (e.g., olive oil or canola oil).\n"
                f"- Limit daily sodium intake to under 2,000 mg (1 teaspoon of salt) to help manage blood pressure.\n"
                f"- Increase dietary fiber with whole grains, fruits, and vegetables.\n\n"
                f"**Physical Activity**:\n"
                f"- Aim for 150 minutes of moderate-intensity exercise (such as brisk walking) per week, subject to physician clearance."
            ),
            "widget": fallback_widget
        }

        return genai_client.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
            fallback_data=fallback_payload
        )


def get_cad_coach_service() -> CADCoachService:
    return CADCoachService()
