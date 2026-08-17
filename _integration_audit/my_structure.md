# My Structure Analysis

**Source:** Workspace root (excluding aiappprj_test-main/)  
**Status:** Can be modified for integration

---

## Directory Tree

```
/workspace/
├── backend/
│   ├── Dockerfile
│   ├── main.py               # Standalone FastAPI application
│   ├── ml_service.py         # ML inference service (XGBoost)
│   ├── models.py             # Pydantic request/response models
│   ├── genai_service.py      # Google Gemini integration
│   ├── utils.py              # Utility functions
│   ├── requirements.txt      # Python dependencies
│   └── scripts/              # Training scripts
│       ├── train.py          # Main training script
│       ├── train_L.py        # LightGBM training
│       └── train_XG.py       # XGBoost training
│
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf            # Nginx configuration for production
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   ├── dist/                 # Production build output
│   │   ├── index.html
│   │   └── assets/
│   │       ├── index-BLs6Y64X.js
│   │       └── index-CepYFi2A.css
│   └── src/
│       ├── main.jsx          # React entry point
│       ├── App.jsx           # Main app (tab-based navigation)
│       ├── index.css         # Tailwind CSS styles
│       ├── components/
│       │   ├── ChatInterface.jsx     # Chat UI component
│       │   ├── PatientDataManager.jsx # Data management UI
│       │   ├── PatientForm.jsx       # Patient input form
│       │   └── RiskDashboard.jsx     # Results visualization
│       └── services/
│           └── api.js        # API client (axios-based)
│
├── data/                     # Dataset directory
│   ├── raw/
│   │   └── diabetic_data.csv     # Raw diabetes dataset
│   └── processed/
│       └── final_dataset.csv     # Processed/cleaned data
│
├── outputs/                  # Model artifacts and visualizations
│   ├── readmission_model.joblib    # Trained XGBoost model
│   ├── feature_columns.json        # Feature column order
│   ├── feature_defaults.json       # Baseline feature values
│   ├── model_metadata.json         # Model performance metrics
│   ├── threshold.json              # Optimal classification threshold
│   ├── correlation_heatmap.png
│   ├── feature_distributions.png
│   ├── feature_vs_target.png
│   ├── model_comparison_bar.png
│   ├── model_comparison_metrics.png
│   ├── pr_curves.png
│   ├── roc_curves.png
│   ├── shap_beeswarm.png
│   ├── shap_dependence.png
│   ├── shap_force.png
│   ├── shap_importance.png
│   └── target_distribution.png
│
├── Samples/                  # Sample patient data for testing
│   ├── generate_sample_data.py
│   ├── patient_high_risk.csv
│   ├── patient_high_risk.xlsx
│   ├── patient_high_risk_full.xlsx
│   ├── patient_low_risk.csv
│   ├── patient_low_risk.xlsx
│   ├── patient_low_risk_full.xlsx
│   ├── patient_moderate_risk.csv
│   ├── patient_moderate_risk.xlsx
│   └── patient_moderate_risk_full.xlsx
│
├── .env                      # Environment variables (empty)
├── .dockerignore
├── .gitignore
├── README.md                 # Project documentation
├── docker-compose.yml        # Docker orchestration
├── requirements.txt          # Root Python dependencies
└── notebook.ipynb            # Jupyter notebook (analysis/training)
```

---

## Architecture Overview

### Backend Architecture (My)

```
main.py (standalone FastAPI app)
    ↓
Endpoints defined inline:
    ├── POST /api/predict → ml_service.predict()
    ├── POST /api/chat → genai_service.generate_response()
    ├── POST /api/upload → file parsing utility
    └── GET /api/model-info → model metadata
    ↓
Services:
    ├── ml_service.py (MLService class)
    │   ├── Loads model from artifacts/ or outputs/
    │   ├── Feature alignment with baseline defaults
    │   ├── SHAP value computation
    │   └── Clinical severity scoring
    └── genai_service.py (GenAIService class)
        └── Google Gemini API integration
    ↓
Utils:
    └── utils.py
        └── parse_uploaded_file_bytes()
        └── calculate_clinical_adjustment()
```

**Key Characteristics:**
- Monolithic FastAPI app (all routes in main.py)
- Service classes for ML and GenAI
- Robust path resolution (relative to file location)
- Fallback paths for model artifacts
- Clinical adjustment rules for risk scoring
- File upload parsing for CSV/Excel

### Frontend Architecture (My)

```
main.jsx
    ↓
App.jsx (tab-based navigation)
    ↓
Tabs:
    ├── Risk Assessment
    │   ├── PatientForm (input)
    │   └── RiskDashboard (results)
    └── Care Navigation
        └── ChatInterface (chat UI)
    ↓
Services:
    └── api.js (axios client)
        ├── predictPatient()
        ├── uploadPatientFile()
        └── sendChatMessage()
    ↓
Styling: Tailwind CSS via index.css
```

**Key Characteristics:**
- Single-page tab navigation (no routing)
- All logic in App.jsx
- Tailwind CSS for styling
- Axios for API calls
- Built-in file upload support
- Loading states and error handling

---

## Key Files Detail

### Backend Entry Point
**File:** `backend/main.py`
- Full FastAPI application (400+ lines)
- Endpoints: `/health`, `/api/predict`, `/api/chat`, `/api/upload`, `/api/model-info`
- CORS configured for localhost:3000, localhost:5173
- Startup event initializes services
- Comprehensive error handling with fallback responses

### ML Service
**File:** `backend/ml_service.py`
- `MLService` class with singleton pattern via `get_ml_service()`
- Loads XGBoost model from `artifacts/` (primary) or `outputs/` (fallback)
- Feature alignment using baseline defaults (not zeros)
- Clinical Severity Score calculation (0-100)
- Urgency levels: Routine Monitoring, Increased Surveillance, Immediate Intervention
- SHAP value computation for interpretability

### Frontend App
**File:** `frontend/src/App.jsx`
- Tab state: `activeTab` ('assessment' or 'navigation')
- Patient data state: `{ form: null, prediction: null }`
- Handles file upload and form submission
- Chat context builder with severity score and symptoms

### API Service
**File:** `frontend/src/services/api.js`
- Axios instance configured
- Functions: `predictPatient()`, `uploadPatientFile()`, `sendChatMessage()`
- Error handling with response detail extraction

---

## Dependencies (My)

### Python (requirements.txt)
```
# Core Data Processing
pandas>=2.0.0
numpy>=1.24.0

# Machine Learning
scikit-learn>=1.3.0
imbalanced-learn>=0.11.0
joblib>=1.3.0
xgboost>=1.7.0
lightgbm>=4.0.0
catboost>=1.2.0

# Interpretability & Visualization
shap>=0.42.0
matplotlib>=3.7.0
seaborn>=0.12.0

# Web Application
streamlit>=1.28.0

# Gen AI
google-generativeai>=0.3.0

# Environment
python-dotenv>=1.0.0
```

### Node.js (frontend/package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "recharts": "^2.10.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@vitejs/plugin-react": "^4.2.1",
    "vite": "^5.0.8",
    "tailwindcss": "^3.4.0"
  }
}
```

---

## Docker Configuration

### docker-compose.yml
```yaml
services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    env_file: .env
    restart: always

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: always
```

### Backend Dockerfile
- Uses Python base image
- Installs requirements
- Copies backend code

### Frontend Dockerfile
- Uses Node for build
- Uses Nginx for serving
- Copies built assets from dist/

---

## Environment Variables

**File:** `.env` (currently empty)

Expected variables based on code:
- `GEMINI_KEY` - Google Gemini API key (used by genai_service.py)

---

## Model Artifacts

Located in `outputs/`:
- `readmission_model.joblib` - Trained XGBoost model
- `feature_columns.json` - Expected feature columns in order
- `feature_defaults.json` - Baseline values for missing features
- `model_metadata.json` - Performance metrics (ROC-AUC, recall, etc.)
- `threshold.json` - Optimal threshold for 80% recall target

---

## Training Scripts

Located in `backend/scripts/`:
- `train.py` - Main training pipeline
- `train_L.py` - LightGBM variant
- `train_XG.py` - XGBoost variant

These scripts produce artifacts in `outputs/` directory.

---

## Sample Data

Located in `Samples/`:
- CSV and XLSX formats
- Three risk levels: low, moderate, high
- `_full` variants contain complete feature sets
- `generate_sample_data.py` - Script to generate more samples

---

## Notes

1. **Complete Docker setup** - Has Dockerfiles and docker-compose.yml
2. **Full training pipeline** - Includes training scripts and notebooks
3. **Rich artifacts** - Model files, visualizations, metrics all present
4. **Clinical scoring** - Implements clinical adjustment rules
5. **File upload** - Supports CSV/Excel file parsing
6. **Tailwind CSS** - Uses Tailwind for styling (different from teammate's CSS)
7. **Tab navigation** - Single-page design vs teammate's hash routing
8. **No RAG documents** - Missing knowledge base files for GenAI
9. **No session management** - No conversation tracking like teammate's session_service
