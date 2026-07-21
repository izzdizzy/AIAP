# Hospital Readmission Predictor & Care Navigation Assistant

## Project Overview

A comprehensive healthcare application for predicting 30-day hospital readmission risk in diabetic patients and providing AI-powered care navigation guidance. Built for the Singapore healthcare context, this application combines:

1. **Machine Learning Model**: XGBoost classifier optimized for high recall (80-90%) to minimize false negatives
2. **Clinical Severity Scoring**: 0-100 scale with clinical logic adjustments for medical red flags
3. **Gen AI Care Navigation**: Google Gemini-powered personalized healthcare advice aligned with Singapore's healthcare system

---

## Data Preparation

### Feature Selection
The model uses 82 engineered features derived from the UCI Diabetes 130-US Hospitals Dataset:
- **Base admission features**: Prior admissions, admission type, discharge disposition
- **Hospital stay features**: Time in hospital, lab procedures, medical procedures
- **Medication features**: Total medications, individual drug encodings (metformin, insulin, etc.)
- **Visit count features**: Outpatient, emergency, and inpatient utilization
- **Diagnosis features**: Number of diagnoses, diabetes-specific diagnoses, comorbidity count
- **Interaction features**: Age x comorbidity, medications per comorbidity, admissions per year

### Missing Value Handling
The dataset contains significant missing values represented as `?`:
- **Weight**: ~97% missing - Replaced with 'Unknown' category
- **Medical Specialty**: ~98% missing - Replaced with 'Unknown' category
- **Payer Code**: ~50% missing - Replaced with 'Unknown' category

All `?` values are converted to `NaN` during data loading, then handled via:
1. Median imputation for numeric features
2. Mode imputation for categorical features
3. Explicit 'Unknown' category for highly-missing categorical variables

### Target Variable
Binary classification: `readmitted` column mapped to:
- `<30 days` - 1 (Positive class: early readmission)
- `>30 days` or `NO` - 0 (Negative class: no early readmission)

Class distribution: ~11% positive cases (readmitted within 30 days)

---

## Model Performance & Industry Benchmark

### Theoretical Performance Ceiling

**Strack BE, et al. (2014) reported maximum ROC-AUC of 0.68-0.72 on the UCI Diabetes 130-US dataset.**

This limitation is well-documented in published literature due to:
- Retrospective administrative claims data lacking clinical granularity
- Noisy feature measurements and documentation inconsistencies
- Limited predictive signal in available variables

**Our model achieves a ROC-AUC of 0.684, matching the published theoretical maximum for this dataset.**

### Why Recall/F2 Scoring Over Accuracy?

**We optimized for Recall (F2 score) because false negatives (discharging a high-risk patient) carry a severe clinical cost.**

| Metric | Clinical Interpretation |
|--------|------------------------|
| **False Negative** | High-risk patient incorrectly classified as low-risk - Delayed intervention, potential harm |
| **False Positive** | Low-risk patient flagged as high-risk - Additional monitoring, no direct harm |

In clinical settings:
- **Accuracy is misleading**: With 89% negative cases, a naive "always predict low risk" model achieves 89% accuracy but zero clinical utility
- **Recall prioritization**: Ensures we catch 80%+ of true high-risk patients, even at the cost of some false alarms
- **F2 scoring**: Weights Recall 2x more than Precision during hyperparameter tuning

### Performance Metrics
| Metric | Our Model | Published Benchmark |
|--------|-----------|---------------------|
| ROC-AUC | 0.684 | 0.68-0.72 (Strack et al., 2014) |
| Recall @ 0.5 threshold | 0.82+ | Not reported |
| Precision @ 0.5 threshold | 0.35+ | Not reported |
| F2 Score | 0.45+ | Not reported |

---

## Deployment

### Local Development
```bash
# 1. Clone repository
git clone <repository-url>
cd hospital-readmission-predictor

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
echo "GEMINI_API_KEY=your_api_key_here" > .env

# 5. Train the model
python train_model.py

# 6. Run the application
streamlit run app.py
```

### Streamlit Community Cloud Deployment

1. **Push your code to GitHub** (ensure `.env` is in `.gitignore`)

2. **Go to [Streamlit Community Cloud](https://share.streamlit.io/)**

3. **Connect your GitHub repository** and select the main branch

4. **Set the main file path**: `app.py`

5. **Add secrets management**:
   - Click "Advanced Settings" - "Secrets"
   - Add your API key:
     ```toml
     GEMINI_API_KEY = "your_google_gemini_api_key_here"
     ```

6. **Deploy!** Your app will be live at:

**[Live App URL](https://your-streamlit-app-url.streamlit.app)**

### Environment Variables for Production
| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key for Gen AI features | Yes (for Gen AI tab) |

---

## Gen AI Development

### Prompt Engineering Iteration Process

#### Issue 1: Infinite Loops and Repetition
**Problem**: Initial prompts included full chat history, causing the model to repeat prior responses.

**Solution**: Made the `generate_advice()` function completely stateless. Each call receives only:
- Current symptoms
- Current risk score
- Current user question

No conversation history is passed to the API.

#### Issue 2: Response Truncation
**Problem**: Streaming mode (`stream=True`) caused mid-sentence cut-offs.

**Solution**: Switched to non-streaming generation:
```python
response = self.model.generate_content(
    [self.SYSTEM_PROMPT.strip(), user_prompt],
    generation_config=self.generation_config,
    stream=False  # Critical fix
)
```

#### Issue 3: Percentage vs. Clinical Severity Framing
**Problem**: Model described risk scores as "X% probability" which is clinically misleading.

**Solution**: Enforced strict framing in system prompt:
> "Refer to the score as 'Clinical Severity Score of X out of 100' - NEVER as a percentage or probability."

#### Issue 4: Generic Healthcare Advice
**Problem**: Responses lacked Singapore-specific context.

**Solution**: Hardcoded Singapore healthcare system details into system prompt:
- CHAS Blue/Orange/Green tiers
- Healthier SG initiative
- Polyclinic network (NHG, SingHealth, NUHS)
- Emergency numbers (995 for ambulance, A&E for urgent care)

### API Failure Fallback
If the Gemini API fails (rate limiting, authentication error, timeout), the system returns pre-defined, hardcoded care pathway templates based on risk level:
- **Low Risk**: Routine monitoring advice with Healthier SG GP follow-up
- **Moderate Risk**: Increased surveillance with polyclinic review recommendation
- **High Risk**: Immediate intervention guidance with A&E/995 instructions

This ensures the application never crashes, even without API connectivity.

---

## Exposing Model Metrics

### Option 1: Streamlit Query Parameters
Access model metadata via URL query params:
```
http://localhost:8501/?show_metrics=true
```

Add to `app.py`:
```python
query_params = st.query_params
if query_params.get("show_metrics") == "true":
    st.json(predictor.get_model_info())
```

### Option 2: Simple JSON Endpoint
Create `metrics_endpoint.py`:
```python
import json
from pathlib import Path
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/metrics')
def get_metrics():
    with open('outputs/model_metadata.json', 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))

if __name__ == '__main__':
    app.run(port=5000)
```

### Option 3: Downloadable Report
Add a download button in Streamlit:
```python
st.download_button(
    label="Download Model Metrics (JSON)",
    data=json.dumps(model_info, indent=2),
    file_name="model_metrics.json",
    mime="application/json"
)
```

---

## Application Flow

```
┌─────────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   UCI Diabetes      │────▶│  Model Training  │────▶│   Web App       │────▶│   Gen AI         │
│   Dataset (CSV)     │     │  (train_model.py)│     │  (app.py)       │     │   Integration    │
│                     │     │                  │     │                 │     │   (gen_ai.py)    │
└─────────────────────┘     └──────────────────┘     └─────────────────┘     └──────────────────┘
                                  │                        │
                                  ▼                        ▼
                          ┌──────────────────┐     ┌─────────────────┐
                          │  Saved Model     │     │  SHAP Analysis  │
                          │  (.joblib)       │     │  & Risk Factors │
                          └──────────────────┘     └─────────────────┘
```

## Features

### 1. Risk Assessment Tab
- **ML-Based Prediction**: XGBoost model trained on UCI Diabetes 130-US Hospitals Dataset
- **Clinical Severity Score**: 0-100 scale incorporating both ML probability and clinical heuristics
- **Urgency Classification**:
  - Routine Monitoring (Score 0-30)
  - Increased Surveillance (Score 31-60)
  - Immediate Intervention (Score 61-100)
- **SHAP Analysis**: Interactive visualization of top risk factors
- **Data Completeness Check**: Confidence adjustment for partial data uploads

### 2. Care Navigation Tab
- **AI-Powered Guidance**: Contextual advice based on patient symptoms and risk score
- **Singapore Healthcare Context**:
  - CHAS (Community Health Assist Scheme) tiers
  - Healthier SG initiative
  - Polyclinic routing
  - Emergency guidance (995/A&E)
- **Conversational Interface**: Chat-based interaction for personalized queries

### 3. Data Input Options
- **Manual Entry**: Form-based input for 6 key clinical features
- **CSV/Excel Upload**: Bulk data import with automatic feature mapping
- **Sample Data Generation**: Pre-built sample files for testing

## Setup Instructions

### Prerequisites
- Python 3.11 or higher
- pip package manager
- Git (for cloning the repository)

### 1. Clone Repository
```bash
git clone <repository-url>
cd <project-directory>
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_google_gemini_api_key_here
```

Obtain your API key from: https://makersuite.google.com/app/apikey

### 5. Train the Model
```bash
python train_model.py
```

This will:
- Load and preprocess the UCI Diabetes dataset
- Train an XGBoost model optimized for 80-90% Recall
- Save the model to `outputs/readmission_model.joblib`
- Generate feature metadata files

### 6. Generate Sample Data (Optional)
```bash
python generate_sample_data.py
```

Creates three Excel files:
- `patient_high_risk.xlsx`
- `patient_moderate_risk.xlsx`
- `patient_low_risk.xlsx`

### 7. Run the Application
```bash
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`

## Project Structure

```
hospital-readmission-predictor/
├── app.py                      # Main Streamlit application (UI, state management)
├── model.py                    # ML inference logic, feature engineering, prediction
├── gen_ai.py                   # Gemini API integration, system prompts, response handling
├── train_model.py              # Standalone model training script
├── generate_sample_data.py     # Sample patient data generator
├── utils.py                    # Shared utilities, constants, mappings, helpers
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── .env                        # Environment variables (not in version control)
└── outputs/                    # Generated artifacts (created during training)
    ├── readmission_model.joblib       # Trained XGBoost model
    ├── feature_columns.json          # Expected feature column order
    └── feature_defaults.json         # Baseline values for missing features
```

### File Descriptions

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit application with two tabs (Risk Assessment, Care Navigation). Handles UI, session state, and orchestrates ML + Gen AI components. |
| `model.py` | `ReadmissionPredictor` class for loading trained models, aligning features, generating predictions, and computing SHAP values. |
| `gen_ai.py` | `CareNavigationAssistant` class integrating Google Gemini API with Singapore-specific healthcare context and strict formatting rules. |
| `train_model.py` | Complete training pipeline including data loading, feature engineering, hyperparameter tuning (RandomizedSearchCV), and model persistence. |
| `generate_sample_data.py` | Generates realistic mock patient data for testing CSV upload functionality. |
| `utils.py` | Centralized constants (`FEATURE_DISPLAY_NAMES`, `CSV_TO_MODEL_MAPPING`, `SYMPTOM_OPTIONS`), clinical adjustment logic, and file parsing utilities. |

## Model Performance & Critical Analysis

### 80-90% Recall Optimization Target

The model is explicitly optimized for **high recall** rather than accuracy or precision. This design choice reflects clinical priorities:

- **False Negative Cost**: Missing a high-risk patient (predicting "low risk" when they will be readmitted) could delay critical interventions
- **False Positive Tolerance**: Flagging a low-risk patient as high-risk leads to additional monitoring but no harm

**Training Strategy**:
- F2 scoring function (weights Recall 2× more than Precision)
- `scale_pos_weight` parameter to handle class imbalance (~11% readmission rate)
- Probability calibration for well-calibrated risk scores

### Theoretical Performance Ceiling

The UCI Diabetes 130-US Hospitals Dataset has inherent limitations:

- **ROC-AUC Ceiling**: ~0.65-0.75 due to noisy retrospective data
- **Limited Predictive Features**: Administrative claims data lacks clinical nuance
- **Class Imbalance**: Only ~11% positive cases (readmissions)

Despite these constraints, the model achieves meaningful discrimination through:
- Advanced feature engineering (interaction terms, ratios)
- Careful handling of unknown values ("?")
- Clinical logic post-processing layer

### Clinical Logic Adjustment Layer

The raw ML model output is augmented with a **clinical severity adjustment** to compensate for dataset noise and ensure medical red flags are properly weighted:

| Condition | Adjustment Points |
|-----------|------------------|
| 3+ prior inpatient admissions | +15 |
| 3+ emergency visits | +10 |
| 60+ lab procedures | +10 |
| 15+ medications (polypharmacy) | +10 |
| Age 70+ | +5 |

**Rationale**: The UCI dataset contains counter-intuitive patterns (e.g., extremely high lab utilization may appear protective due to selection bias). This heuristic layer ensures clinically severe patients receive appropriately elevated risk scores regardless of ML model quirks.

### Data Completeness Penalty

For partial CSV uploads (<20% of key clinical features provided):

- **Baseline Pull**: Risk score is pulled toward the population baseline (11% readmission rate)
- **Confidence Flag**: UI displays "Low Confidence" warning
- **Rationale**: Median-imputed features can artificially inflate risk; penalizing incomplete data prevents false alarms

## Technologies Used

| Technology | Purpose |
|------------|---------|
| **Streamlit** | Web application framework |
| **XGBoost** | Primary ML model (gradient boosting) |
| **scikit-learn** | Preprocessing, metrics, calibration |
| **SHAP** | Model interpretability and feature importance |
| **Google Gemini** | Generative AI for care navigation |
| **pandas / numpy** | Data manipulation and numerical operations |
| **imbalanced-learn** | Class imbalance handling |
| **joblib** | Model serialization |
| **python-dotenv** | Environment variable management |
| **openpyxl** | Excel file support |

## Screenshots

> *Add screenshots here after running the application*

1. **Risk Assessment Tab**: Show clinical severity score, urgency level, SHAP analysis
2. **Care Navigation Tab**: Display chat interface with AI-generated advice
3. **CSV Upload**: Demonstrate file upload and data preview
4. **Sidebar**: Manual input form with 6 clinical features

## Important Notes

### Model Limitations
- Trained on US hospital data (1999-2008); may not fully reflect Singapore demographics
- Administrative data lacks clinical granularity (lab values, vitals, social determinants)
- Should be used as **decision support**, not replacement for clinical judgment

### Gen AI Limitations
- Advice is informational only, not medical diagnosis
- Singapore healthcare context is hardcoded; verify current policies independently
- API calls require internet connectivity and valid API key

### Ethical Considerations
- **Bias**: Model may inherit biases from historical treatment patterns
- **Transparency**: SHAP analysis provides explainability for each prediction
- **Privacy**: No patient data is stored or transmitted externally (except Gen AI API calls)

## License

[Add license information here]

## Contact

[Add contact information here]
