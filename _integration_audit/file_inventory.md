# File Inventory Report

**Generated:** Integration Audit for AIAP Project  
**Purpose:** Complete inventory of all files in the workspace to support integration planning

---

## 1. Teammate Files (aiappprj_test-main/aiappprj_test-main/)

### Backend Files (Teammate)
```
backend/
├── __init__.py
├── app.py                    # FastAPI app wrapper
├── config.py                 # Configuration settings
├── main.py                   # Entry point (uvicorn runner)
├── genai_documents/
│   ├── Alcohol and Smoking.txt
│   ├── Cholesterol and Heart Disease.txt
│   ├── Heart Health Basic Dietary Guidelines.txt
│   ├── High Blood Pressure Healthy Eating Guide.txt
│   ├── How to Keep Your Heart Healthy The Essential Dos and Donts.txt
│   └── system_prompt.txt
├── model/
│   ├── __init__.py
│   ├── constants.py
│   ├── formatter.py
│   ├── pipeline.py
│   ├── predict.py
│   ├── preprocess.py
│   ├── response.py
│   ├── schemas.py
│   └── translations.py
├── routes/
│   ├── __init__.py
│   └── predict.py
└── services/
    ├── __init__.py
    ├── chatbot.py
    ├── genai_service.py
    ├── knowledge_service.py
    ├── prediction_service.py
    ├── prompt_builder.py
    └── session_service.py
```

### Frontend Files (Teammate)
```
frontend/
├── App.jsx                   # Main app component with routing
├── main.jsx                  # React entry point
├── index.html
├── package.json
├── package-lock.json
├── vite.config.js
├── components/
│   ├── AppShell.jsx
│   ├── ChatMessage.jsx
│   ├── ChatWindow.jsx
│   ├── Disclaimer.jsx
│   ├── FormField.jsx
│   ├── PrimaryButton.jsx
│   ├── ResultCard.jsx
│   └── SectionCard.jsx
├── hooks/
│   └── useAssessmentForm.js
├── pages/
│   ├── AssessmentPage.jsx
│   ├── ChatbotPage.jsx
│   ├── HomePage.jsx
│   └── ResultsPage.jsx
├── services/
│   ├── chatService.js
│   └── predictionService.js
├── styles/
│   ├── chatbot.css
│   └── global.css
├── utils/
│   ├── assessmentConfig.js
│   ├── payload.js
│   ├── risk.js
│   ├── storage.js
│   └── 5files/             # Backup/duplicate folder
│       ├── AssessmentPage.jsx
│       ├── FormField.jsx
│       ├── assessmentConfig.js
│       ├── payload.js
│       └── useAssessmentForm.js
```

### Models & Assets (Teammate)
```
models/
├── exported_model2.ubj       # XGBoost model (UBJ format)
├── imputation_bundle.pkl
└── preprocessing_bundle.pkl
```

### Config Files (Teammate)
- `.env_example` - Environment template (GEMINI_KEY)
- `.gitignore`
- `.gitattributes`
- `requirements.txt` - Python dependencies (pinned versions)
- `todo.txt`

### Dev/Model Files (Teammate)
```
.model_dev/
├── model2.ipynb
├── model3.ipynb
├── model3old.ipynb
├── model4.ipynb
├── predict.py
└── test.py
```

---

## 2. My Files (Workspace Root Level)

### Backend Files (My)
```
backend/
├── Dockerfile
├── main.py                   # FastAPI app (standalone, full implementation)
├── ml_service.py             # ML service with XGBoost inference
├── models.py                 # Pydantic models
├── genai_service.py          # GenAI service
├── utils.py                  # Utility functions
├── requirements.txt          # Python dependencies
└── scripts/
    ├── train.py
    ├── train_L.py
    └── train_XG.py
```

### Frontend Files (My)
```
frontend/
├── Dockerfile
├── index.html
├── nginx.conf
├── package.json
├── package-lock.json
├── vite.config.js
├── dist/                     # Built assets
│   ├── index.html
│   └── assets/
│       ├── index-BLs6Y64X.js
│       └── index-CepYFi2A.css
└── src/
    ├── App.jsx               # Main app component (tab-based)
    ├── main.jsx              # React entry point
    ├── index.css
    ├── components/
    │   ├── ChatInterface.jsx
    │   ├── PatientDataManager.jsx
    │   ├── PatientForm.jsx
    │   └── RiskDashboard.jsx
    └── services/
        └── api.js
```

### Data Files (My)
```
data/
├── raw/
│   └── diabetic_data.csv
└── processed/
    └── final_dataset.csv
```

### Outputs/Artifacts (My)
```
outputs/
├── readmission_model.joblib      # Trained XGBoost model
├── feature_columns.json
├── feature_defaults.json
├── model_metadata.json
├── threshold.json
├── correlation_heatmap.png
├── feature_distributions.png
├── feature_vs_target.png
├── model_comparison_bar.png
├── model_comparison_metrics.png
├── pr_curves.png
├── roc_curves.png
├── shap_beeswarm.png
├── shap_dependence.png
├── shap_force.png
├── shap_importance.png
└── target_distribution.png
```

### Samples (My)
```
Samples/
├── generate_sample_data.py
├── patient_high_risk.csv
├── patient_high_risk.xlsx
├── patient_high_risk_full.xlsx
├── patient_low_risk.csv
├── patient_low_risk.xlsx
├── patient_low_risk_full.xlsx
├── patient_moderate_risk.csv
├── patient_moderate_risk.xlsx
└── patient_moderate_risk_full.xlsx
```

### Root Config Files (My)
- `README.md`
- `.env` (empty)
- `.dockerignore`
- `.gitignore`
- `docker-compose.yml`
- `requirements.txt`
- `notebook.ipynb`

---

## 3. Likely Matching Files

| Purpose | Teammate File | My File |
|---------|--------------|---------|
| Backend Entry Point | `backend/main.py` (uvicorn wrapper) | `backend/main.py` (full FastAPI app) |
| Backend App | `backend/app.py` | `backend/main.py` (contains app) |
| ML Service | `backend/model/pipeline.py`, `backend/services/prediction_service.py` | `backend/ml_service.py` |
| GenAI Service | `backend/services/genai_service.py` | `backend/genai_service.py` |
| Pydantic Models | `backend/model/schemas.py` | `backend/models.py` |
| Utils | `backend/utils.py` (not present) | `backend/utils.py` |
| Frontend Entry | `frontend/main.jsx` | `frontend/src/main.jsx` |
| Frontend App | `frontend/App.jsx` | `frontend/src/App.jsx` |
| Frontend Config | `frontend/package.json` | `frontend/package.json` |
| Frontend Build | `frontend/vite.config.js` | `frontend/vite.config.js` |
| Requirements | `requirements.txt` | `requirements.txt` |
| Docker Compose | (none) | `docker-compose.yml` |
| Dockerfiles | (none) | `backend/Dockerfile`, `frontend/Dockerfile` |

---

## 4. Likely Duplicated Files

1. **main.jsx** - Both have React entry points with similar structure
2. **App.jsx** - Both have main App components (different architectures)
3. **package.json** - Both have frontend package configs (different deps)
4. **vite.config.js** - Both have Vite configs
5. **requirements.txt** - Both have Python requirements (teammate has pinned versions)
6. **genai_service.py** - Both have GenAI service implementations
7. **prediction_service.py / ml_service.py** - Similar ML prediction functionality

---

## 5. Likely Missing Files

### In My Files (compared to teammate):
- `backend/config.py` - Configuration module
- `backend/routes/` - Router organization
- `backend/services/` directory structure
- `backend/model/` submodules (constants, formatter, preprocess, response, translations)
- `backend/genai_documents/` - Knowledge base files for RAG
- `frontend/components/` - Reusable UI components (AppShell, ChatMessage, etc.)
- `frontend/pages/` - Page components (HomePage, ResultsPage, etc.)
- `frontend/hooks/` - Custom hooks (useAssessmentForm)
- `frontend/styles/` - CSS stylesheets
- `frontend/utils/` - Utility modules (assessmentConfig, storage, risk, payload)
- `frontend/services/chatService.js`, `predictionService.js`
- `models/` - Pre-trained model bundles

### In Teammate Files (compared to my files):
- `data/` - Raw and processed data directories
- `outputs/` - Model artifacts, visualizations, metrics
- `Samples/` - Sample patient data files
- `backend/scripts/` - Training scripts
- `docker-compose.yml` - Docker orchestration
- `Dockerfile` (both backend and frontend)
- `nginx.conf` - Nginx configuration

---

## 6. Likely Entrypoints

### Backend
- **Teammate:** `backend/main.py` → imports `app` from `backend/app.py`
- **My:** `backend/main.py` → standalone FastAPI application

### Frontend
- **Teammate:** `frontend/main.jsx` → renders `<App />` from `./App.jsx`
- **My:** `frontend/src/main.jsx` → renders `<App />` from `./App.jsx`

### Docker
- **My:** `docker-compose.yml` orchestrates both services

---

## 7. Likely Config Files

| File | Owner | Purpose |
|------|-------|---------|
| `backend/main.py` | Both | Backend entry point |
| `frontend/main.jsx` | Both | Frontend entry point |
| `frontend/package.json` | Both | Node.js dependencies |
| `requirements.txt` | Both | Python dependencies |
| `vite.config.js` | Both | Vite build config |
| `docker-compose.yml` | My | Docker orchestration |
| `.env` / `.env_example` | Both | Environment variables |
| `backend/config.py` | Teammate | App configuration |

---

## 8. Likely Shared Utilities

### Backend
- **ML Inference:** Both have XGBoost-based prediction
- **GenAI Integration:** Both integrate Google Gemini API
- **Pydantic Models:** Both use Pydantic for request/response validation
- **CORS:** Both configure CORS middleware

### Frontend
- **React + Vite:** Both use React 18 with Vite
- **API Communication:** Both have service layers for backend calls
- **State Management:** Both manage assessment state

### Key Differences
- **Teammate Frontend:** Hash-based routing, page components, more structured component architecture
- **My Frontend:** Tab-based navigation, single-page layout, Tailwind CSS

---

## 9. Import Path Analysis

### Teammate Backend
```python
from .app import app
from .routes.predict import router as predict_router
from .services.chatbot import router as chatbot_router
from .model.pipeline import run_prediction
from .model.schemas import PredictionResponse
```

### My Backend
```python
from models import PatientData, PredictionResponse, ...
from ml_service import get_ml_service, MLService
from genai_service import get_genai_service, GenAIService
from utils import parse_uploaded_file_bytes
```

### Teammate Frontend
```javascript
import App from './App';
import './styles/global.css';
import AppShell from './components/AppShell';
import AssessmentPage from './pages/AssessmentPage';
import { submitAssessment } from './services/predictionService';
```

### My Frontend
```javascript
import App from './App.jsx'
import './index.css'
import PatientForm from './components/PatientForm';
import { predictPatient, uploadPatientFile } from './services/api';
```

---

## 10. Hardcoded Paths & Working Directory Assumptions

### Teammate
- `backend/main.py`: Uses relative import `.app`
- `backend/services/prediction_service.py`: Relative imports `..model.pipeline`
- Model paths likely assume working directory is project root

### My
- `backend/main.py`: `PROJECT_ROOT = Path(__file__).resolve().parent.parent`
- `backend/ml_service.py`: `BASE_DIR = Path(__file__).parent.parent`
- Explicitly resolves paths relative to file location (more robust)

---

## Summary Statistics

| Category | Teammate Count | My Count |
|----------|---------------|----------|
| Backend Python Files | 20 | 7 |
| Frontend JS/JSX Files | 20 | 7 |
| Model/Artifact Files | 3 | 17 |
| Config Files | 6 | 8 |
| Data Files | 0 | 9 |
| Documentation | 1 (todo.txt) | 1 (README.md) |
| **Total Files** | **~50** | **~49** |
