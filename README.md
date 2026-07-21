# Hospital Readmission Predictor & Care Navigation Assistant

## Project Overview

A comprehensive healthcare application for predicting 30-day hospital readmission risk in diabetic patients and providing AI-powered care navigation guidance. Built for the Singapore healthcare context, this application combines:

1. **Machine Learning Model**: XGBoost classifier optimized for high recall (80-90%) to minimize false negatives
2. **Clinical Severity Scoring**: 0-100 scale with clinical logic adjustments for medical red flags
3. **Gen AI Care Navigation**: Google Gemini-powered personalized healthcare advice aligned with Singapore's healthcare system

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
