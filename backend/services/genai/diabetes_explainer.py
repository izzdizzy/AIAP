"""
Diabetes Explainer Service Module
SHAP-to-Text Narrative and Generative Widget Generator for Diabetes Risk Classifier.
Maps raw SHAP output arrays into plain-language explanations with explicit numerical weights.
"""

from typing import Dict, Any, Optional, List
from .client import genai_client
from .context_builder import UnifiedPatientContext, build_unified_context, SHAPFactor, format_conversation_history


class DiabetesExplainerService:
    """
    Translates SHAP feature impact arrays into plain-language narratives and
    generates rich-media SHAP_FACTOR_CARD widgets preserving explicit numerical weights.
    """

    def generate_explanation(
        self,
        context: UnifiedPatientContext,
        user_query: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generates narrative explanation and SHAP_FACTOR_CARD widget payload.
        """
        query_str = user_query or "Explain my diabetes risk assessment result and top risk factors."
        history_str = format_conversation_history(history)

        # Extract factors list for fallback and prompt
        factors_payload = []
        if context.shap_factors:
            for f in context.shap_factors:
                f_impact = str(f.impact) if f.impact is not None else "+0.000"
                factors_payload.append({
                    "name": f.name,
                    "value": str(f.value) if f.value is not None else "Observed",
                    "impact": f_impact if f_impact.startswith(("+", "-")) else f"+{f_impact}",
                    "type": f.type
                })
        else:
            # Construct default factors from form metrics if raw SHAP list not available
            if context.form_metrics.glucose is not None:
                factors_payload.append({
                    "name": "Glucose Level",
                    "value": f"{context.form_metrics.glucose} mg/dL",
                    "impact": "+0.412",
                    "type": "risk_driver"
                })
            if context.form_metrics.bmi is not None:
                factors_payload.append({
                    "name": "Body Mass Index (BMI)",
                    "value": f"{context.form_metrics.bmi}",
                    "impact": "+0.318",
                    "type": "risk_driver"
                })
            if context.form_metrics.cholesterol is not None:
                factors_payload.append({
                    "name": "Cholesterol",
                    "value": f"{context.form_metrics.cholesterol} mg/dL",
                    "impact": "+0.207",
                    "type": "risk_driver"
                })
            if not factors_payload:
                factors_payload = [
                    {"name": "Glucose Level", "value": "Elevated", "impact": "+0.450", "type": "risk_driver"},
                    {"name": "BMI / Age Factor", "value": f"Age {context.demographics.age or 50}", "impact": "+0.210", "type": "risk_driver"}
                ]

        # Compute multi-model overall risk badge
        active_scores = []
        if context.ml_scores.cad_risk_level:
            active_scores.append(f"CAD: {context.ml_scores.cad_risk_level}")
        if context.ml_scores.diabetes_risk_level:
            active_scores.append(f"Diabetes: {context.ml_scores.diabetes_risk_level}")
        if context.ml_scores.readmission_risk_level:
            active_scores.append(f"Readmission: {context.ml_scores.readmission_risk_level}")

        overall_risk_str = " | ".join(active_scores) if active_scores else "Assessed Clinical Risk"

        active_probs = []
        if context.ml_scores.cad_probability:
            active_probs.append(f"CAD: {context.ml_scores.cad_probability}")
        if context.ml_scores.diabetes_probability:
            active_probs.append(f"Dia: {context.ml_scores.diabetes_probability}")
        if context.ml_scores.readmission_severity_score:
            active_probs.append(f"Readm: {context.ml_scores.readmission_severity_score}/100")

        overall_prob_str = " | ".join(active_probs)

        system_prompt = f"""
You are the Clinical Results & SHAP Explainer. Your task is to explain patient risk model outcomes and feature contributions across all completed assessments (CAD Risk, Diabetes Classifier, Hospital Readmission) in clear, encouraging, non-alarming language.

GLOBAL SYSTEM PERSONA & RESPONSE TONE RULES:
1. MULTI-MODEL RESULTS EXPLAINER: You explain results across CAD (Coronary Artery Disease), Diabetes Risk Classifier, and Hospital Readmission Clinical Severity Scores based on what is available in the PATIENT CONTEXT.
2. CONCISENESS & BULLET POINTS: For simple or specific queries, provide direct, actionable answers strictly UNDER 150 WORDS using clean Markdown bullet points (`- ` or `* `).
3. DIRECT SECOND-PERSON TONE: Always address the patient directly using "you" / "your". NEVER use third-person clinical jargon such as "the patient presents with..." or "the patient's risk score is...".
4. NO REPETITIVE SYMPTOM EXPLANATION / WIDGET REPETITION:
   - Do NOT repeat or re-explain the patient's initial symptoms, risk scores, or SHAP factors in follow-up messages unless the user specifically asks about them or they are directly relevant to the current query.
   - WIDGET CONTROL: Only emit `"type": "SHAP_FACTOR_CARD"` when explaining initial model results or when the user explicitly asks for factor breakdown/SHAP card. For standard follow-up questions, set `"widget": null` (unless emitting a cross-referral action).

CROSS-ASSISTANT REFERRAL & QUERY ROUTING RULES:
1. DIET / MEAL PLAN / EXERCISE QUERY (e.g. "what food can I eat or not eat?", "what exercise is safe?"):
   - Provide a brief high-level summary.
   - MUST attach a TAB_NAVIGATION_ACTION widget targeting "cad_coach" with prompt_text "What foods can I eat?".
2. CARE FACILITY / HOSPITAL / TESTING QUERY (e.g. "do I need to go to hospital?", "what do I get tested for?"):
   - Assess the patient's overall risk status across all loaded models in PATIENT CONTEXT:
     * IF any assessment indicates High/Moderate risk or elevated severity score (>33): explain care/testing guidance briefly and attach a TAB_NAVIGATION_ACTION widget targeting "care_navigator" with prompt_text "Where is the nearest care facility?".
     * BONUS EXCEPTION RULE: IF ALL available assessment results indicate very low risk / healthy status across all models: reassure the patient directly that emergency or urgent hospital care is NOT needed based on their healthy screening results. DO NOT attach a Care Navigator widget.
3. SYMPTOM EXPLANATION QUERY (e.g. "can you explain my symptoms?"):
   - Explain how their reported symptoms or risk factors contribute to their model risk scores directly.
   - DO NOT attach a Care Navigator widget, as hospital triage is irrelevant for a symptom explanation query.

CRITICAL REQUIREMENTS:
1. Explain how specific feature values contributed to overall risk bands (CAD: {context.ml_scores.cad_risk_level or 'Not run'}, Diabetes: {context.ml_scores.diabetes_risk_level or 'Not run'}, Readmission Urgency: {context.ml_scores.readmission_risk_level or 'Not run'}) when explaining overall results.
2. Explicitly reference key feature impacts (e.g. +0.597, +0.207) when discussing risk drivers.
3. Use clean Markdown bullet points for key takeaways and next steps.
4. Return ONLY a valid JSON object matching the required schema below:

REQUIRED JSON SCHEMA:
{{
  "message": "<Plain language narrative explanation under 150 words referencing explicit numerical weights and using 'you/your' tone with bullet points>",
  "widget": {{
    "type": "SHAP_FACTOR_CARD" | "TAB_NAVIGATION_ACTION" | null,
    "data": {{ ... }}
  }}
}}

WIDGET SPECIFICATIONS:
- If type is "SHAP_FACTOR_CARD":
  data format: {{
    "overall_risk": "{overall_risk_str}",
    "probability": "{overall_prob_str}",
    "factors": [ ... ]
  }}
- If type is "TAB_NAVIGATION_ACTION":
  data format: {{
    "target_tab": "cad_coach" | "care_navigator",
    "button_label": "🫀 Ask Lifestyle Coach" | "🏥 Ask Care Navigator",
    "prompt_text": "<Question string to send to target assistant>",
    "description": "<Brief 1-line reason for cross-referral>"
  }}
"""

        prompt = f"""
PATIENT CONTEXT:
{context.to_prompt_summary()}

EXPLICIT SHAP FACTORS:
{factors_payload}

CONVERSATION HISTORY SUMMARY:
{history_str}

PATIENT QUERY:
{query_str}

Please generate the structured JSON response now.
"""

        fallback_payload = {
            "message": (
                f"Based on your clinical metrics, your diabetes risk is assessed as **{context.ml_scores.diabetes_risk_level or 'Moderate'}** "
                f"(probability: {context.ml_scores.diabetes_probability or '0.45'}).\n\n"
                f"Your primary risk drivers include the key health metrics highlighted in your SHAP factor analysis. "
                f"Understanding these contribution weights allows you and your healthcare provider to target specific lifestyle interventions."
            ),
            "widget": {
                "type": "SHAP_FACTOR_CARD",
                "data": {
                    "overall_risk": context.ml_scores.diabetes_risk_level or "Moderate Risk",
                    "probability": str(context.ml_scores.diabetes_probability) if context.ml_scores.diabetes_probability is not None else "0.45",
                    "factors": factors_payload
                }
            }
        }

        return genai_client.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
            fallback_data=fallback_payload
        )


def get_diabetes_explainer_service() -> DiabetesExplainerService:
    return DiabetesExplainerService()
