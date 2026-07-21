# Workflow and Dataset Explanation

## 1. Current Workflow

### Is the flow strictly Dataset -> ML Training -> Gen AI Integration -> Webapp Deployment?

**Yes, but with important clarifications.** The workflow has two distinct phases:

#### Phase A: Development/Training Pipeline (One-time or Periodic)
```
UCI Diabetes Dataset (data/raw/diabetic_data.csv)
        ↓
Data Preprocessing & Feature Engineering (train_model.py)
        ↓
Processed Dataset (data/processed/final_dataset.csv)
        ↓
ML Model Training (train_model.py)
        ↓
Trained Model (outputs/readmission_model.joblib)
Feature Schema (outputs/feature_columns.json)
Model Metadata (outputs/model_metadata.json)
```

#### Phase B: Runtime/Inference Pipeline (User Interaction)
```
User opens Streamlit app (app.py)
        ↓
User inputs clinical features via sidebar:
  - Prior admissions, comorbidity count, age group
  - Medication count, discharge diagnosis, high risk flag
        ↓
App calculates interaction features:
  - age_comorbidity_interaction
  - medication_comorbidity_interaction
  - admissions_comorbidity_interaction
  - age_medication_interaction
        ↓
ML Model (model.py) processes input
        ↓
Risk score + SHAP values generated
        ↓
[Optional] User switches to Care Navigation tab
        ↓
Gen AI Assistant (gen_ai.py) receives:
  - Patient symptoms (from multiselect)
  - ML risk score
  - Risk category
        ↓
Gemini API generates personalized advice
        ↓
Advice displayed in chat interface
```

### Exact Data Flow When User Interacts with App

1. **User loads app.py**: Environment variables loaded via `load_dotenv()`, model and assistant cached
2. **User enters clinical data in sidebar**: 6 clinical features + symptom selection
3. **User clicks "Calculate Risk Score" in Tab 1**:
   - Input dictionary created with 10 features (6 base + 4 interactions)
   - `ReadmissionPredictor.predict()` called
   - Features aligned to training schema
   - XGBoost model generates probability
   - SHAP values computed for interpretability
   - Results stored in session state
4. **User switches to Tab 2 and asks questions**:
   - Chat input captured
   - `CareNavigationAssistant.generate_advice()` called with:
     - Symptoms list from sidebar
     - Risk score from Tab 1 calculation
     - Risk category derived from score
   - Gemini API returns contextualized advice
   - Response displayed in chat

---

## 2. Dataset Contents

### UCI Diabetes 130-US Hospitals Dataset

**Source**: UCI Machine Learning Repository  
**Description**: Hospital readmission records for diabetic patients from 1999-2008 across 130 US hospitals  
**Target Variable**: `readmitted` (binary: whether patient was readmitted within 30 days)

#### Raw Dataset Columns (diabetic_data.csv)
The raw dataset contains ~50 columns including:
- **Identifiers**: encounter_id, patient_nbr
- **Demographics**: race, gender, age
- **Admission Details**: admission_type_id, discharge_disposition_id, admission_source_id
- **Hospital Stay**: time_in_hospital
- **Insurance**: payer_code
- **Medical Care**: medical_specialty, num_lab_procedures, num_procedures
- **Medications**: num_medications, various medication change indicators
- **Visit History**: number_outpatient, number_emergency, number_inpatient
- **Diagnoses**: diag_1, diag_2, diag_3 (ICD-9 codes)
- **Lab Results**: max_glu_serum, A1Cresult
- **Medication Changes**: metformin, repaglinide, nateglinide, chlorpropamide, glimepiride, acetohexamide, etc.
- **Outcome**: readmitted (YES/NO/<30/>30)

#### Processed Dataset (final_dataset.csv)
After feature engineering, the processed dataset contains **11 columns**:

| Column | Type | Description |
|--------|------|-------------|
| `prior_admissions` | Integer | Total previous hospital admissions |
| `comorbidity_count` | Integer | Number of co-existing conditions |
| `age` | Integer | Encoded age group (0-100 in decades) |
| `medication_count` | Integer | Number of prescribed medications |
| `discharge_diagnosis` | Float | Primary ICD diagnosis code |
| `age_comorbidity_interaction` | Integer | age × comorbidity_count |
| `medication_comorbidity_interaction` | Integer | medication_count × comorbidity_count |
| `admissions_comorbidity_interaction` | Integer | prior_admissions × comorbidity_count |
| `age_medication_interaction` | Integer | age × medication_count |
| `high_risk_flag` | Binary | Derived high-risk indicator |
| `readmission_target` | Binary | Target variable (1 if readmitted <30 days) |

### Features Currently Fed into ML Model for Inference

When a user interacts with the app, **exactly 10 features** are passed to the model:

1. **prior_admissions** - from sidebar number_input
2. **comorbidity_count** - from sidebar number_input
3. **age** - encoded from age_group dropdown (0, 10, 20, ... 90)
4. **medication_count** - from sidebar number_input
5. **discharge_diagnosis** - converted from text input to float
6. **age_comorbidity_interaction** - calculated: age_encoded × comorbidity_count
7. **medication_comorbidity_interaction** - calculated: medication_count × comorbidity_count
8. **admissions_comorbidity_interaction** - calculated: prior_admissions × comorbidity_count
9. **age_medication_interaction** - calculated: age_encoded × medication_count
10. **high_risk_flag** - from selectbox (0 for "No", 1 for "Yes")

**Note**: Symptoms are NOT fed into the ML model. They are only used by the Gen AI assistant for contextual advice generation.

---

## 3. Real-World Scenario Validation

### Intended Use Case
> A patient is discharged from the hospital and downloads the app. The app uses the hospital-known baseline data (from the dataset structure) to establish a readmission risk score. The patient monitors their symptoms, and the app provides actionable self-care steps. The patient can ask the Gen AI any questions about their symptoms, and the AI responds using the patient's inputted symptoms, the ML risk score, and general hospital/dataset context.

### Evaluation: PARTIAL MATCH with Gaps

#### What Matches ✅

1. **Risk Score Generation**: The app correctly uses clinical features similar to what would be known at hospital discharge (prior admissions, comorbidities, medications, diagnosis) to generate a readmission risk score.

2. **Symptom Monitoring**: The sidebar allows patients to select from 18 common diabetes-related symptoms they're currently experiencing.

3. **Gen AI Integration**: The Care Navigation tab passes both symptoms AND ML risk score to the Gemini-powered assistant, which generates contextualized advice.

4. **Singapore Healthcare Context**: The Gen AI assistant includes specific guidance about CHAS tiers, Healthier SG, polyclinic routing, and emergency procedures (call 995).

5. **Actionable Guidance**: The AI response includes:
   - Risk score interpretation
   - Symptom assessment
   - Recommended next steps
   - Lifestyle recommendations
   - When to seek immediate care

#### Critical Gaps ❌

##### Gap 1: No Baseline Data Import Mechanism
**Problem**: The scenario states "the app uses the hospital-known baseline data." Currently, users must **manually enter** all clinical features. There's no mechanism to:
- Import discharge summary data
- Connect to hospital EHR systems
- Load pre-populated patient profiles

**Impact**: Patients would need to know their exact comorbidity count, medication count, and ICD diagnosis code—information typically found in discharge documents.

**Fix Required**: Add one of the following to `app.py`:
```python
# Option A: File upload for discharge summary
uploaded_file = st.file_uploader("Upload Discharge Summary (CSV/JSON)", type=['csv', 'json'])
if uploaded_file:
    # Parse and auto-populate clinical features
    
# Option B: QR code scanning from discharge papers
# Option C: API integration placeholder for hospital EHR
```

##### Gap 2: No Longitudinal Symptom Tracking
**Problem**: The scenario mentions "the patient monitors their symptoms." Currently, symptoms are entered once per session with no:
- Historical tracking
- Trend visualization
- Alert thresholds for worsening symptoms

**Fix Required**: Add to `app.py`:
```python
# Session-based symptom history
if 'symptom_history' not in st.session_state:
    st.session_state.symptom_history = []
    
# Track symptoms over time with timestamps
st.session_state.symptom_history.append({
    'timestamp': datetime.now(),
    'symptoms': selected_symptoms,
    'risk_score': current_risk_score
})
```

##### Gap 3: Gen AI Lacks Hospital/Dataset Context
**Problem**: The scenario states AI should respond using "general hospital/dataset context." Currently:
- The Gen AI prompt includes Singapore healthcare system context
- But it does NOT include information about which hospital the patient was discharged from
- It does NOT reference population-level statistics from the UCI dataset
- It does NOT have access to hospital-specific care pathways

**Fix Required**: Update `gen_ai.py` to accept additional context:
```python
def generate_advice(
    self,
    patient_symptoms: List[str],
    ml_risk_score: float,
    risk_category: str,
    hospital_context: Optional[Dict] = None,  # NEW
    population_stats: Optional[Dict] = None   # NEW
):
    # Include in prompt:
    # "This patient was discharged from [Hospital Name] which has 
    #  [X]% 30-day readmission rate for diabetic patients..."
```

##### Gap 4: Missing Self-Care Step Tracking
**Problem**: The scenario mentions "actionable self-care steps" but there's no mechanism to:
- Record which recommendations were followed
- Track adherence over time
- Adjust risk based on adherence

**Fix Required**: Add checklist functionality in Tab 2:
```python
st.subheader("Your Action Plan")
st.checkbox("Schedule follow-up appointment")
st.checkbox("Review medication schedule")
st.checkbox("Monitor blood glucose daily")
```

### Summary Table

| Requirement | Status | Location | Fix Needed |
|-------------|--------|----------|------------|
| Hospital baseline data | ❌ Gap | app.py | Add file upload or EHR integration |
| Risk score from clinical features | ✅ Works | app.py, model.py | None |
| Symptom monitoring | ⚠️ Partial | app.py | Add longitudinal tracking |
| Actionable self-care steps | ⚠️ Partial | gen_ai.py | Add action plan checklist |
| Gen AI uses symptoms + risk score | ✅ Works | gen_ai.py, app.py | None |
| Gen AI has hospital context | ❌ Gap | gen_ai.py | Add hospital/population context parameters |
| Singapore healthcare guidance | ✅ Works | gen_ai.py | None |

### Recommended Code Changes

#### For app.py (Baseline Data Import)
Add after sidebar symptom section:
```python
st.markdown("---")
st.subheader("Import Discharge Data")
st.caption("Optional: Upload discharge summary to auto-populate fields")

uploaded_file = st.file_uploader(
    "Upload CSV/JSON discharge summary",
    type=['csv', 'json'],
    help="If available, upload your hospital discharge summary"
)

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            discharge_data = pd.read_csv(uploaded_file)
        else:
            discharge_data = pd.read_json(uploaded_file)
        
        # Auto-populate fields based on column mapping
        # This would require defining expected column names
        st.success("Discharge data loaded successfully!")
    except Exception as e:
        st.error(f"Failed to parse file: {e}")
```

#### For gen_ai.py (Enhanced Context)
Modify `generate_advice` method signature:
```python
def generate_advice(
    self,
    patient_symptoms: List[str],
    ml_risk_score: float,
    risk_category: str,
    additional_info: Optional[Dict[str, Any]] = None,
    hospital_context: Optional[Dict[str, Any]] = None,  # NEW PARAMETER
    max_retries: int = 3,
    retry_delay: float = 2.0
) -> str:
```

Update `_format_patient_context` to include hospital info:
```python
if hospital_context:
    prompt_parts.append("\\nHospital Context:")
    prompt_parts.append(f"- Discharged from: {hospital_context.get('hospital_name', 'Unknown')}")
    prompt_parts.append(f"- Hospital readmission rate: {hospital_context.get('readmission_rate', 'N/A')}%")
    prompt_parts.append(f"- Follow-up clinic: {hospital_context.get('follow_up_clinic', 'Not specified')}")
```

---

## Conclusion

The current implementation provides a **functional foundation** that matches the core concept: ML risk assessment + Gen AI-guided care navigation. However, to fully realize the intended real-world scenario where a discharged patient uses the app with hospital-provided baseline data, the following must be added:

1. **Data import mechanism** for discharge summaries (high priority)
2. **Longitudinal symptom tracking** across sessions (medium priority)
3. **Hospital-specific context** in Gen AI prompts (medium priority)
4. **Action plan tracking** for self-care adherence (low priority)

Without these additions, the app requires manual data entry and lacks continuity of care features essential for post-discharge monitoring.
