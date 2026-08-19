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
    age: Optional[Any] = None
    gender: Optional[str] = None
    subsidy_tier: str = "CHAS Green"  # e.g. CHAS Blue, CHAS Orange, CHAS Green, Pioneer Generation


class CADFormMetrics(BaseModel):
    blood_pressure: Optional[str] = None
    cholesterol: Optional[Any] = None
    chest_pain_type: Optional[str] = None
    fasting_blood_sugar: Optional[str] = None
    resting_ecg: Optional[str] = None
    max_heart_rate: Optional[Any] = None
    exercise_angina: Optional[str] = None
    st_depression: Optional[Any] = None
    st_slope: Optional[str] = None
    major_vessels: Optional[Any] = None
    thalassemia: Optional[str] = None


class DiabetesFormMetrics(BaseModel):
    general_health: Optional[str] = None
    bmi: Optional[Any] = None
    high_bp: Optional[str] = None
    high_chol: Optional[str] = None
    phys_activity: Optional[str] = None
    diff_walk: Optional[str] = None
    smoker: Optional[str] = None
    heart_disease: Optional[str] = None
    fruits: Optional[str] = None
    veggies: Optional[str] = None
    glucose: Optional[Any] = None


class ReadmissionFormMetrics(BaseModel):
    active_symptoms: List[str] = Field(default_factory=list)
    prior_admissions: Optional[Any] = None
    num_medications: Optional[Any] = None
    comorbidity_count: int = 0
    time_in_hospital: Optional[Any] = None
    num_lab_procedures: Optional[Any] = None


class RawFormMetrics(BaseModel):
    blood_pressure: Optional[str] = None
    cholesterol: Optional[Any] = None
    bmi: Optional[Any] = None
    glucose: Optional[Any] = None
    comorbidity_count: int = 0
    active_symptoms: List[str] = Field(default_factory=list)
    cad: CADFormMetrics = Field(default_factory=CADFormMetrics)
    diabetes: DiabetesFormMetrics = Field(default_factory=DiabetesFormMetrics)
    readmission: ReadmissionFormMetrics = Field(default_factory=ReadmissionFormMetrics)
    raw_fields: Dict[str, Any] = Field(default_factory=dict)


class MLScores(BaseModel):
    cad_risk_level: Optional[str] = None
    cad_probability: Optional[str] = None
    diabetes_risk_level: Optional[str] = None
    diabetes_probability: Optional[Any] = None
    readmission_risk_level: Optional[str] = None
    readmission_probability: Optional[Any] = None
    readmission_severity_score: Optional[Any] = None


class UnifiedPatientContext(BaseModel):
    demographics: PatientDemographics = Field(default_factory=PatientDemographics)
    form_metrics: RawFormMetrics = Field(default_factory=RawFormMetrics)
    ml_scores: MLScores = Field(default_factory=MLScores)
    shap_factors: List[SHAPFactor] = Field(default_factory=list)

    def to_prompt_summary(self) -> str:
        """Helper to format the context into a clear Markdown string for LLM system prompts."""
        lines = ["=== UNIFIED PATIENT CLINICAL CONTEXT ==="]
        lines.append(f"Demographics: Age {self.demographics.age or 'N/A'}, Gender {self.demographics.gender or 'N/A'}, Subsidy Tier: {self.demographics.subsidy_tier}")

        # CAD Section
        cad = self.form_metrics.cad
        if self.ml_scores.cad_risk_level or cad.chest_pain_type or cad.blood_pressure or cad.cholesterol or cad.max_heart_rate or cad.st_depression:
            lines.append("\n🫀 CAD (Cardiovascular) Assessment Metrics:")
            if self.ml_scores.cad_risk_level:
                lines.append(f"- CAD Risk Level: {self.ml_scores.cad_risk_level} (Probability/Percent: {self.ml_scores.cad_probability or 'N/A'})")
            if cad.blood_pressure or self.form_metrics.blood_pressure:
                lines.append(f"- Resting Blood Pressure: {cad.blood_pressure or self.form_metrics.blood_pressure}")
            if cad.cholesterol is not None or self.form_metrics.cholesterol is not None:
                lines.append(f"- Serum Cholesterol: {cad.cholesterol or self.form_metrics.cholesterol}")
            if cad.chest_pain_type:
                lines.append(f"- Chest Pain Type: {cad.chest_pain_type}")
            if cad.fasting_blood_sugar:
                lines.append(f"- Fasting Blood Sugar: {cad.fasting_blood_sugar}")
            if cad.max_heart_rate is not None:
                lines.append(f"- Max Heart Rate: {cad.max_heart_rate} bpm")
            if cad.exercise_angina:
                lines.append(f"- Exercise-Induced Angina: {cad.exercise_angina}")
            if cad.st_depression is not None:
                lines.append(f"- ST Depression (Oldpeak): {cad.st_depression}")
            if cad.st_slope:
                lines.append(f"- ST Slope: {cad.st_slope}")
            if cad.resting_ecg:
                lines.append(f"- Resting ECG: {cad.resting_ecg}")
            if cad.major_vessels is not None:
                lines.append(f"- Major Vessels Count: {cad.major_vessels}")
            if cad.thalassemia:
                lines.append(f"- Thalassemia: {cad.thalassemia}")

        # Diabetes Section
        dia = self.form_metrics.diabetes
        if self.ml_scores.diabetes_risk_level or dia.general_health or dia.bmi or dia.high_bp or dia.high_chol:
            lines.append("\n🥗 Diabetes Risk Classifier Metrics:")
            if self.ml_scores.diabetes_risk_level:
                lines.append(f"- Diabetes Risk Band: {self.ml_scores.diabetes_risk_level} (Prob: {self.ml_scores.diabetes_probability or 'N/A'})")
            if dia.general_health:
                lines.append(f"- General Health Self-Rating: {dia.general_health}")
            if dia.bmi or self.form_metrics.bmi:
                lines.append(f"- BMI: {dia.bmi or self.form_metrics.bmi}")
            if dia.glucose or self.form_metrics.glucose:
                lines.append(f"- Glucose Level: {dia.glucose or self.form_metrics.glucose}")
            if dia.high_bp:
                lines.append(f"- High Blood Pressure Flag: {dia.high_bp}")
            if dia.high_chol:
                lines.append(f"- High Cholesterol Flag: {dia.high_chol}")
            if dia.phys_activity:
                lines.append(f"- Physical Activity (30 Days): {dia.phys_activity}")
            if dia.diff_walk:
                lines.append(f"- Difficulty Walking/Stairs: {dia.diff_walk}")
            if dia.smoker:
                lines.append(f"- Smoker History: {dia.smoker}")
            if dia.heart_disease:
                lines.append(f"- Heart Disease/Attack History: {dia.heart_disease}")
            if dia.fruits:
                lines.append(f"- Daily Fruit Intake: {dia.fruits}")
            if dia.veggies:
                lines.append(f"- Daily Veggie Intake: {dia.veggies}")

        # Readmission Section
        readm = self.form_metrics.readmission
        if self.ml_scores.readmission_risk_level or readm.active_symptoms or readm.prior_admissions or self.form_metrics.active_symptoms:
            lines.append("\n🏥 Hospital Readmission Triage Metrics:")
            if self.ml_scores.readmission_risk_level:
                lines.append(f"- Readmission Urgency: {self.ml_scores.readmission_risk_level} (Clinical Severity Score: {self.ml_scores.readmission_severity_score or 'N/A'}/100, Raw Prob: {self.ml_scores.readmission_probability or 'N/A'})")
            symptoms_list = readm.active_symptoms or self.form_metrics.active_symptoms
            if symptoms_list:
                lines.append(f"- Active Symptoms: {', '.join(symptoms_list)}")
            if readm.prior_admissions is not None:
                lines.append(f"- Prior Hospital Admissions: {readm.prior_admissions}")
            if readm.num_medications is not None:
                lines.append(f"- Prescribed Medications Count: {readm.num_medications}")
            if readm.comorbidity_count or self.form_metrics.comorbidity_count:
                lines.append(f"- Comorbidity Count: {readm.comorbidity_count or self.form_metrics.comorbidity_count}")
            if readm.time_in_hospital is not None:
                lines.append(f"- Hospital Stay Duration: {readm.time_in_hospital} days")
            if readm.num_lab_procedures is not None:
                lines.append(f"- Lab Procedures Count: {readm.num_lab_procedures}")

        # Fallback if no specific module sections triggered
        if not (self.ml_scores.cad_risk_level or self.ml_scores.diabetes_risk_level or self.ml_scores.readmission_risk_level):
            lines.append("\nForm Metrics Summary:")
            if self.form_metrics.blood_pressure:
                lines.append(f"- Blood Pressure: {self.form_metrics.blood_pressure}")
            if self.form_metrics.cholesterol is not None:
                lines.append(f"- Cholesterol: {self.form_metrics.cholesterol}")
            if self.form_metrics.bmi is not None:
                lines.append(f"- BMI: {self.form_metrics.bmi}")
            if self.form_metrics.glucose is not None:
                lines.append(f"- Glucose: {self.form_metrics.glucose}")

        if self.shap_factors:
            lines.append("\n📊 Top SHAP Risk Factor Drivers Across Assessments:")
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


CP_MAP = {0: "Typical Angina (0)", 1: "Atypical Angina (1)", 2: "Non-anginal Pain (2)", 3: "Asymptomatic (3)"}
FBS_MAP = {1: "Elevated (>120 mg/dL)", 0: "Normal (<=120 mg/dL)"}
RESTECG_MAP = {0: "Normal (0)", 1: "ST-T Wave Abnormality (1)", 2: "Left Ventricular Hypertrophy (2)"}
EXANG_MAP = {1: "Yes (1)", 0: "No (0)"}
SLOPE_MAP = {0: "Upsloping (0)", 1: "Flat (1)", 2: "Downsloping (2)"}
THAL_MAP = {1: "Normal (1)", 2: "Fixed Defect (2)", 3: "Reversible Defect (3)"}

GENHLTH_MAP = {1: "Excellent (1)", 2: "Very Good (2)", 3: "Good (3)", 4: "Fair (4)", 5: "Poor (5)"}
YES_NO_MAP = {1: "Yes (1)", 0: "No (0)", "1": "Yes (1)", "0": "No (0)"}


def _to_int_safe(val: Any) -> Optional[int]:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def build_unified_context(data: Dict[str, Any]) -> UnifiedPatientContext:
    """
    Constructs a UnifiedPatientContext from arbitrary dictionary inputs across
    CAD, Diabetes, Readmission or combined payloads.
    """
    demographics_data = data.get("demographics") or {}
    metrics_data = data.get("form_metrics") or data.get("assessment") or data.get("profile") or {}
    scores_data = data.get("ml_scores") or data.get("prediction") or {}
    raw_shap_list = data.get("shap_factors") or data.get("top_factors") or data.get("shap_values") or []

    cad_raw = metrics_data.get("cad_form") or data.get("cad_form") or metrics_data
    diabetes_raw = metrics_data.get("diabetes_form") or data.get("diabetes_form") or metrics_data
    readm_raw = metrics_data.get("readmission_form") or data.get("readmission_form") or metrics_data

    # Extract demographics
    age = demographics_data.get("age") or cad_raw.get("age") or diabetes_raw.get("Age") or readm_raw.get("age")
    gender = (
        demographics_data.get("gender")
        or cad_raw.get("gender")
        or (f"Male ({cad_raw.get('sex')})" if cad_raw.get("sex") in (1, "1") else (f"Female ({cad_raw.get('sex')})" if cad_raw.get("sex") in (0, "0") else None))
        or (f"Male ({diabetes_raw.get('Sex')})" if diabetes_raw.get("Sex") in (1, "1") else (f"Female ({diabetes_raw.get('Sex')})" if diabetes_raw.get("Sex") in (0, "0") else None))
        or readm_raw.get("gender")
    )
    subsidy_tier = (
        demographics_data.get("subsidy_tier")
        or data.get("chas_tier")
        or metrics_data.get("chas_tier")
        or readm_raw.get("chas_tier")
        or "CHAS Green"
    )

    # Extract high-level metrics
    bp = metrics_data.get("blood_pressure") or metrics_data.get("bp") or (
        f"{cad_raw.get('trestbps')} mmHg" if cad_raw.get("trestbps") else None
    )
    chol = metrics_data.get("cholesterol") or metrics_data.get("chol") or cad_raw.get("chol")
    chol_str = f"{chol} mg/dL" if chol is not None else None
    bmi = metrics_data.get("bmi") or diabetes_raw.get("BMI") or cad_raw.get("bmi")
    glucose = metrics_data.get("glucose") or diabetes_raw.get("glucose") or cad_raw.get("glucose") or (
        "Elevated (>120 mg/dL)" if cad_raw.get("fbs") in (1, "1") else None
    )
    symptoms = metrics_data.get("active_symptoms") or readm_raw.get("symptoms") or readm_raw.get("active_symptoms") or data.get("symptoms") or []
    if isinstance(symptoms, str):
        symptoms = [s.strip() for s in symptoms.split(",") if s.strip()]

    comorb_count = metrics_data.get("comorbidity_count") or readm_raw.get("comorbidity_count") or readm_raw.get("comorbidities") or 0
    if not comorb_count and isinstance(metrics_data, dict):
        keys = ["num_conditions", "number_diagnoses", "diabetes", "hypertension"]
        comorb_count = sum(1 for k in keys if metrics_data.get(k))

    # Parse CAD metrics
    cp_val = _to_int_safe(cad_raw.get("cp"))
    fbs_val = _to_int_safe(cad_raw.get("fbs"))
    restecg_val = _to_int_safe(cad_raw.get("restecg"))
    exang_val = _to_int_safe(cad_raw.get("exang"))
    slope_val = _to_int_safe(cad_raw.get("slope"))
    thal_val = _to_int_safe(cad_raw.get("thal"))

    cad_metrics = CADFormMetrics(
        blood_pressure=bp,
        cholesterol=chol_str,
        chest_pain_type=CP_MAP.get(cp_val) if cp_val in CP_MAP else (str(cad_raw.get("cp")) if cad_raw.get("cp") is not None else None),
        fasting_blood_sugar=FBS_MAP.get(fbs_val) if fbs_val in FBS_MAP else None,
        resting_ecg=RESTECG_MAP.get(restecg_val) if restecg_val in RESTECG_MAP else None,
        max_heart_rate=_to_int_safe(cad_raw.get("thalach")),
        exercise_angina=EXANG_MAP.get(exang_val) if exang_val in EXANG_MAP else None,
        st_depression=cad_raw.get("oldpeak"),
        st_slope=SLOPE_MAP.get(slope_val) if slope_val in SLOPE_MAP else None,
        major_vessels=_to_int_safe(cad_raw.get("ca")),
        thalassemia=THAL_MAP.get(thal_val) if thal_val in THAL_MAP else None,
    )

    # Parse Diabetes metrics
    gen_hlth_val = _to_int_safe(diabetes_raw.get("GenHlth"))
    high_bp_val = _to_int_safe(diabetes_raw.get("HighBP"))
    high_chol_val = _to_int_safe(diabetes_raw.get("HighChol"))
    phys_act_val = _to_int_safe(diabetes_raw.get("PhysActivity"))
    diff_walk_val = _to_int_safe(diabetes_raw.get("DiffWalk"))
    smoker_val = _to_int_safe(diabetes_raw.get("Smoker"))
    heart_dis_val = _to_int_safe(diabetes_raw.get("HeartDiseaseorAttack"))
    fruits_val = _to_int_safe(diabetes_raw.get("Fruits"))
    veggies_val = _to_int_safe(diabetes_raw.get("Veggies"))

    diabetes_metrics = DiabetesFormMetrics(
        general_health=GENHLTH_MAP.get(gen_hlth_val) if gen_hlth_val in GENHLTH_MAP else None,
        bmi=bmi,
        high_bp=YES_NO_MAP.get(high_bp_val) if high_bp_val in YES_NO_MAP else None,
        high_chol=YES_NO_MAP.get(high_chol_val) if high_chol_val in YES_NO_MAP else None,
        phys_activity=YES_NO_MAP.get(phys_act_val) if phys_act_val in YES_NO_MAP else None,
        diff_walk=YES_NO_MAP.get(diff_walk_val) if diff_walk_val in YES_NO_MAP else None,
        smoker=YES_NO_MAP.get(smoker_val) if smoker_val in YES_NO_MAP else None,
        heart_disease=YES_NO_MAP.get(heart_dis_val) if heart_dis_val in YES_NO_MAP else None,
        fruits=YES_NO_MAP.get(fruits_val) if fruits_val in YES_NO_MAP else None,
        veggies=YES_NO_MAP.get(veggies_val) if veggies_val in YES_NO_MAP else None,
        glucose=glucose,
    )

    # Parse Readmission metrics
    readm_metrics = ReadmissionFormMetrics(
        active_symptoms=symptoms,
        prior_admissions=_to_int_safe(readm_raw.get("prior_admissions")),
        num_medications=_to_int_safe(readm_raw.get("num_medications")),
        comorbidity_count=int(comorb_count),
        time_in_hospital=_to_int_safe(readm_raw.get("time_in_hospital")),
        num_lab_procedures=_to_int_safe(readm_raw.get("num_lab_procedures")),
    )

    # Extract ML scores
    cad_risk = scores_data.get("cad_risk_level") or scores_data.get("risk_level") or scores_data.get("riskLevel")
    cad_prob = scores_data.get("cad_probability") or scores_data.get("probability") or scores_data.get("riskPercent") or scores_data.get("riskProbability")
    
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
                fval = item.get("value") if item.get("value") is not None else item.get("feature_value")
                fimpact_raw = item.get("raw_impact") or item.get("impact") or item.get("shap_value") or item.get("importance") or 0.0
                
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
            gender=str(gender) if gender is not None else None,
            subsidy_tier=str(subsidy_tier)
        ),
        form_metrics=RawFormMetrics(
            blood_pressure=bp,
            cholesterol=chol_str,
            bmi=bmi,
            glucose=glucose,
            comorbidity_count=int(comorb_count),
            active_symptoms=symptoms,
            cad=cad_metrics,
            diabetes=diabetes_metrics,
            readmission=readm_metrics,
            raw_fields=metrics_data if isinstance(metrics_data, dict) else {}
        ),
        ml_scores=MLScores(
            cad_risk_level=str(cad_risk) if cad_risk else None,
            cad_probability=str(cad_prob) if cad_prob else None,
            diabetes_risk_level=str(dia_risk) if dia_risk else None,
            diabetes_probability=dia_prob,
            readmission_risk_level=str(readm_risk) if readm_risk else None,
            readmission_probability=readm_prob,
            readmission_severity_score=readm_score
        ),
        shap_factors=shap_factors
    )
