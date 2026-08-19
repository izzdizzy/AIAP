"""
Unified Context Builder and Patient Context Pydantic Models
Aggregates Form Data + ML Assessment Results across CAD, Diabetes, and Readmission modules.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SHAPFactor(BaseModel):
    name: str
    value: Optional[Any] = None
    impact: str  # e.g., "+0.597" or "-0.207"
    raw_impact: float = 0.0
    type: str = "risk_driver"  # "risk_driver" or "protective_factor"


class PatientDemographics(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    subsidy_tier: str = "CHAS Green"  # e.g. CHAS Blue, CHAS Orange, CHAS Green, Pioneer Generation


class RawFormMetrics(BaseModel):
    blood_pressure: Optional[str] = None
    cholesterol: Optional[float] = None
    bmi: Optional[float] = None
    glucose: Optional[float] = None
    comorbidity_count: int = 0
    active_symptoms: List[str] = Field(default_factory=list)
    raw_fields: Dict[str, Any] = Field(default_factory=dict)


class MLScores(BaseModel):
    cad_risk_level: Optional[str] = None
    cad_probability: Optional[float] = None
    diabetes_risk_level: Optional[str] = None
    diabetes_probability: Optional[float] = None
    readmission_risk_level: Optional[str] = None
    readmission_probability: Optional[float] = None
    readmission_severity_score: Optional[int] = None


class UnifiedPatientContext(BaseModel):
    demographics: PatientDemographics = Field(default_factory=PatientDemographics)
    form_metrics: RawFormMetrics = Field(default_factory=RawFormMetrics)
    ml_scores: MLScores = Field(default_factory=MLScores)
    shap_factors: List[SHAPFactor] = Field(default_factory=list)

    def to_prompt_summary(self) -> str:
        """Helper to format the context into a clear Markdown string for LLM system prompts."""
        lines = ["=== UNIFIED PATIENT CLINICAL CONTEXT ==="]
        lines.append(f"Demographics: Age {self.demographics.age or 'N/A'}, Gender {self.demographics.gender or 'N/A'}, Subsidy Tier: {self.demographics.subsidy_tier}")
        
        lines.append("\nRaw Form Metrics:")
        if self.form_metrics.blood_pressure:
            lines.append(f"- Blood Pressure: {self.form_metrics.blood_pressure}")
        if self.form_metrics.cholesterol is not None:
            lines.append(f"- Cholesterol: {self.form_metrics.cholesterol} mg/dL")
        if self.form_metrics.bmi is not None:
            lines.append(f"- BMI: {self.form_metrics.bmi}")
        if self.form_metrics.glucose is not None:
            lines.append(f"- Glucose: {self.form_metrics.glucose} mg/dL")
        lines.append(f"- Comorbidity Count: {self.form_metrics.comorbidity_count}")
        if self.form_metrics.active_symptoms:
            lines.append(f"- Active Symptoms: {', '.join(self.form_metrics.active_symptoms)}")

        lines.append("\nML Scores & Risk Levels:")
        if self.ml_scores.cad_risk_level:
            lines.append(f"- CAD Risk Level: {self.ml_scores.cad_risk_level} (Prob: {self.ml_scores.cad_probability or 'N/A'})")
        if self.ml_scores.diabetes_risk_level:
            lines.append(f"- Diabetes Risk Band: {self.ml_scores.diabetes_risk_level} (Prob: {self.ml_scores.diabetes_probability or 'N/A'})")
        if self.ml_scores.readmission_risk_level:
            lines.append(f"- Readmission Urgency: {self.ml_scores.readmission_risk_level} (Score: {self.ml_scores.readmission_severity_score or 'N/A'}/100, Prob: {self.ml_scores.readmission_probability or 'N/A'})")

        if self.shap_factors:
            lines.append("\nTop SHAP Factor Array:")
            for factor in self.shap_factors:
                val_str = f" = {factor.value}" if factor.value is not None else ""
                lines.append(f"- {factor.name}{val_str}: Impact {factor.impact} ({factor.type})")

        return "\n".join(lines)


def format_shap_impact(impact: float) -> str:
    """Formats a float impact into string like +0.597 or -0.210."""
    return f"+{impact:.3f}" if impact >= 0 else f"{impact:.3f}"


def format_conversation_history(history: Optional[List[Dict[str, Any]]]) -> str:
    """
    Formats previous chat messages into a concise summary log for the LLM prompt.
    Includes past user questions and assistant responses while truncating lengthy messages.
    """
    if not history:
        return "No prior conversation history (First message in session)."

    formatted_lines = []
    for msg in history:
        role_raw = msg.get("role") or "user"
        role = "User" if str(role_raw).lower() in ("user", "human") else "Assistant"
        content = (msg.get("content") or msg.get("message") or "").strip()

        if not content or content.startswith("Error:"):
            continue

        # Truncate assistant responses if they are long to keep context window clean
        if role == "Assistant" and len(content) > 250:
            content = content[:250] + "..."

        formatted_lines.append(f"{role}: {content}")

    if not formatted_lines:
        return "No prior conversation history."

    return "\n".join(formatted_lines[-10:])


def build_unified_context(data: Dict[str, Any]) -> UnifiedPatientContext:
    """
    Constructs a UnifiedPatientContext from arbitrary dictionary inputs across
    CAD, Diabetes, Readmission or combined payloads.
    """
    demographics_data = data.get("demographics") or {}
    metrics_data = data.get("form_metrics") or data.get("assessment") or data.get("profile") or {}
    scores_data = data.get("ml_scores") or data.get("prediction") or {}
    raw_shap_list = data.get("shap_factors") or data.get("top_factors") or data.get("shap_values") or []

    # Extract demographics
    age = demographics_data.get("age") or metrics_data.get("age")
    gender = demographics_data.get("gender") or metrics_data.get("gender") or metrics_data.get("sex")
    subsidy_tier = (
        demographics_data.get("subsidy_tier")
        or data.get("chas_tier")
        or metrics_data.get("chas_tier")
        or "CHAS Green"
    )

    # Extract form metrics
    bp = metrics_data.get("blood_pressure") or metrics_data.get("bp") or (
        f"{metrics_data.get('trestbps')}" if metrics_data.get('trestbps') else None
    )
    chol = metrics_data.get("cholesterol") or metrics_data.get("chol")
    bmi = metrics_data.get("bmi")
    glucose = metrics_data.get("glucose") or metrics_data.get("fbs")
    symptoms = metrics_data.get("active_symptoms") or data.get("symptoms") or []
    if isinstance(symptoms, str):
        symptoms = [s.strip() for s in symptoms.split(",") if s.strip()]

    comorb_count = metrics_data.get("comorbidity_count", 0)
    if not comorb_count and isinstance(metrics_data, dict):
        # calculate approximate comorbidities if present
        keys = ["num_conditions", "number_diagnoses", "diabetes", "hypertension"]
        comorb_count = sum(1 for k in keys if metrics_data.get(k))

    # Extract ML scores
    cad_risk = scores_data.get("cad_risk_level") or scores_data.get("risk_level")
    cad_prob = scores_data.get("cad_probability") or scores_data.get("probability")
    
    dia_risk = scores_data.get("diabetes_risk_level") or scores_data.get("risk_band") or scores_data.get("risk_label")
    dia_prob = scores_data.get("diabetes_probability") or scores_data.get("risk_probability")
    
    readm_risk = scores_data.get("readmission_risk_level") or scores_data.get("urgency_level") or scores_data.get("risk_category")
    readm_prob = scores_data.get("readmission_probability") or scores_data.get("raw_probability")
    readm_score = scores_data.get("readmission_severity_score") or scores_data.get("clinical_severity_score")

    # Extract SHAP factor array
    shap_factors: List[SHAPFactor] = []
    if isinstance(raw_shap_list, list):
        for item in raw_shap_list:
            if isinstance(item, dict):
                fname = item.get("name") or item.get("feature") or item.get("feature_name") or "Unknown Factor"
                fval = item.get("value")
                fimpact_raw = item.get("raw_impact") or item.get("impact") or item.get("shap_value") or 0.0
                
                if isinstance(fimpact_raw, str):
                    fimpact_str = fimpact_raw
                    try:
                        fimpact_float = float(fimpact_raw.replace("+", ""))
                    except ValueError:
                        fimpact_float = 0.0
                else:
                    fimpact_float = float(fimpact_raw)
                    fimpact_str = format_shap_impact(fimpact_float)

                ftype = item.get("type") or ("risk_driver" if fimpact_float >= 0 else "protective_factor")

                shap_factors.append(SHAPFactor(
                    name=fname,
                    value=fval,
                    impact=fimpact_str,
                    raw_impact=fimpact_float,
                    type=ftype
                ))

    return UnifiedPatientContext(
        demographics=PatientDemographics(
            age=age,
            gender=gender,
            subsidy_tier=subsidy_tier
        ),
        form_metrics=RawFormMetrics(
            blood_pressure=bp,
            cholesterol=float(chol) if chol is not None else None,
            bmi=float(bmi) if bmi is not None else None,
            glucose=float(glucose) if glucose is not None else None,
            comorbidity_count=int(comorb_count),
            active_symptoms=symptoms,
            raw_fields=metrics_data if isinstance(metrics_data, dict) else {}
        ),
        ml_scores=MLScores(
            cad_risk_level=cad_risk,
            cad_probability=float(cad_prob) if cad_prob is not None else None,
            diabetes_risk_level=dia_risk,
            diabetes_probability=float(dia_prob) if dia_prob is not None else None,
            readmission_risk_level=readm_risk,
            readmission_probability=float(readm_prob) if readm_prob is not None else None,
            readmission_severity_score=int(readm_score) if readm_score is not None else None
        ),
        shap_factors=shap_factors
    )
