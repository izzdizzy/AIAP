# Dependency Map

**Purpose:** Map dependencies between files, modules, and external packages

---

## 1. Python Package Dependencies

### Teammate Backend Dependencies
```
fastapi==0.116.1          # Web framework
uvicorn==0.35.0           # ASGI server
pydantic==2.13.4          # Data validation
pydantic-settings==2.14.2 # Settings management
google-genai==2.13.0      # Google Gemini SDK
xgboost==3.3.0            # ML model
numpy==2.4.6              # Numerical computing
pandas==3.0.3             # Data manipulation
scikit-learn==1.9.0       # ML utilities
shap==0.52.0              # Model interpretability
matplotlib==3.11.0        # Visualization
requests==2.34.2          # HTTP client
```

### My Backend Dependencies
```
pandas>=2.0.0             # Data manipulation
numpy>=1.24.0             # Numerical computing
scikit-learn>=1.3.0       # ML utilities
imbalanced-learn>=0.11.0  # Imbalanced datasets
joblib>=1.3.0             # Model serialization
xgboost>=1.7.0            # ML model
lightgbm>=4.0.0           # Alternative ML model
catboost>=1.2.0           # Alternative ML model
shap>=0.42.0              # Model interpretability
matplotlib>=3.7.0         # Visualization
seaborn>=0.12.0           # Visualization
streamlit>=1.28.0         # Alternative UI (not used in API)
google-generativeai>=0.3.0 # Google Gemini SDK
python-dotenv>=1.0.0      # Environment variables
```

### Frontend Dependencies Comparison

| Package | Teammate | My | Notes |
|---------|----------|-----|-------|
| react | ^18.3.1 | ^18.2.0 | Compatible |
| react-dom | ^18.3.1 | ^18.2.0 | Compatible |
| vite | ^8.1.5 | ^5.0.8 | Different major versions |
| @vitejs/plugin-react | ^4.3.1 | ^4.2.1 | Compatible |
| react-markdown | ^10.1.0 | - | Teammate only (for chat rendering) |
| axios | - | ^1.6.0 | My only (API calls) |
| recharts | - | ^2.10.0 | My only (charts) |
| tailwindcss | - | ^3.4.0 | My only (styling) |

---

## 2. Internal Module Dependencies

### Teammate Backend Import Graph

```
backend/
├── main.py
│   └── .app → app
│
├── app.py
│   ├── fastapi (external)
│   ├── .routes.predict → router
│   └── .services.chatbot → router
│
├── routes/predict.py
│   ├── fastapi (external)
│   ├── ..services.prediction_service → predict_cad_risk
│   └── ..model.schemas → PredictionResponse
│
├── services/
│   ├── prediction_service.py
│   │   ├── ..model.pipeline → run_prediction
│   │   └── ..model.schemas → PredictionResponse
│   │
│   ├── genai_service.py
│   │   ├── google.genai (external)
│   │   ├── .prompt_builder → build_prompt
│   │   └── .knowledge_service → retrieve_documents
│   │
│   ├── knowledge_service.py
│   │   └── Path operations for genai_documents/
│   │
│   ├── chatbot.py (FastAPI router)
│   │   ├── .genai_service → generate_response
│   │   └── .session_service → manage sessions
│   │
│   └── session_service.py
│       └── In-memory session storage
│
└── model/
    ├── pipeline.py
    │   ├── .predict → make_prediction
    │   ├── .preprocess → prepare_input
    │   └── .formatter → format_output
    │
    ├── schemas.py (Pydantic models)
    ├── predict.py (inference logic)
    ├── preprocess.py (data preprocessing)
    ├── formatter.py (response formatting)
    ├── constants.py (feature mappings)
    ├── response.py (response classes)
    └── translations.py (i18n)
```

### My Backend Import Graph

```
backend/
├── main.py
│   ├── fastapi (external)
│   ├── models → PatientData, PredictionResponse, etc.
│   ├── ml_service → get_ml_service, MLService
│   ├── genai_service → get_genai_service, GenAIService
│   └── utils → parse_uploaded_file_bytes
│
├── ml_service.py
│   ├── xgboost (external)
│   ├── joblib (external)
│   ├── shap (external, optional)
│   ├── numpy, pandas (external)
│   └── utils → calculate_clinical_adjustment
│
├── models.py
│   ├── pydantic (external)
│   └── typing (stdlib)
│
├── genai_service.py
│   ├── google.generativeai (external)
│   └── os, pathlib (stdlib)
│
└── utils.py
    ├── pandas (external)
    └── io (stdlib)
```

---

## 3. Frontend Import Graphs

### Teammate Frontend

```
frontend/
├── main.jsx
│   ├── ./App
│   └── ./styles/global.css
│
├── App.jsx
│   ├── ./components/AppShell
│   ├── ./pages/AssessmentPage
│   ├── ./pages/HomePage
│   ├── ./pages/ResultsPage
│   ├── ./pages/ChatbotPage
│   ├── ./services/predictionService
│   └── ./utils/storage
│
├── pages/AssessmentPage.jsx
│   ├── ../hooks/useAssessmentForm
│   ├── ../components/FormField
│   ├── ../components/PrimaryButton
│   └── ../utils/assessmentConfig
│
├── pages/ResultsPage.jsx
│   ├── ../components/ResultCard
│   ├── ../components/SectionCard
│   └── ../utils/risk
│
├── pages/ChatbotPage.jsx
│   ├── ../components/ChatWindow
│   ├── ../components/ChatMessage
│   └── ../services/chatService
│
└── services/
    ├── predictionService.js → axios/fetch to /api/predict
    └── chatService.js → axios/fetch to /api/chat
```

### My Frontend

```
frontend/
├── src/
│   ├── main.jsx
│   │   ├── ./App
│   │   └── ./index.css
│   │
│   ├── App.jsx
│   │   ├── ./components/PatientForm
│   │   ├── ./components/RiskDashboard
│   │   ├── ./components/ChatInterface
│   │   └── ./services/api
│   │
│   ├── components/
│   │   ├── PatientForm.jsx
│   │   │   └── ../services/api (upload)
│   │   ├── RiskDashboard.jsx
│   │   │   └── recharts (external)
│   │   ├── ChatInterface.jsx
│   │   └── PatientDataManager.jsx
│   │
│   └── services/
│       └── api.js
│           ├── axios (external)
│           └── endpoints: /api/predict, /api/chat, /api/upload
│
└── dist/ (build output)
```

---

## 4. File Path Dependencies

### Teammate Backend Path Assumptions

| File | Path Reference | Type |
|------|---------------|------|
| `main.py` | `.app` | Relative import |
| `app.py` | `.routes`, `.services` | Relative imports |
| `services/prediction_service.py` | `..model.pipeline` | Relative import |
| `services/genai_service.py` | `genai_documents/` | Relative to backend/ |
| `model/pipeline.py` | `../models/` | Model files location |

### My Backend Path Assumptions

| File | Path Reference | Type |
|------|---------------|------|
| `main.py` | `Path(__file__).parent.parent` | Resolves to workspace root |
| `main.py` | `.env` at PROJECT_ROOT | Environment file |
| `ml_service.py` | `ARTIFACTS_DIR = backend/artifacts/` | Primary model path |
| `ml_service.py` | `FALLBACK = outputs/` | Fallback model path |
| `genai_service.py` | `os.environ.get('GEMINI_KEY')` | Environment variable |

---

## 5. External API Dependencies

### Google Gemini API
- **Used by:** Both teammate and my genai_service
- **Environment:** `GEMINI_KEY` or `GOOGLE_API_KEY`
- **Purpose:** Generate healthcare advice responses

### Backend API Endpoints (for Frontend)

| Endpoint | Method | Purpose | Used By |
|----------|--------|---------|---------|
| `/health` | GET | Health check | Monitoring |
| `/api/predict` | POST | ML prediction | Both frontends |
| `/api/chat` | POST | GenAI chat | Both frontends |
| `/api/upload` | POST | File upload | My frontend only |
| `/api/model-info` | GET | Model metadata | My frontend only |

---

## 6. Duplicate/Overlapping Dependencies

### Python Packages (Version Conflicts Possible)

| Package | Teammate Version | My Version | Conflict Risk |
|---------|-----------------|------------|---------------|
| numpy | 2.4.6 | >=1.24.0 | Low (my is flexible) |
| pandas | 3.0.3 | >=2.0.0 | Low |
| scikit-learn | 1.9.0 | >=1.3.0 | Low |
| xgboost | 3.3.0 | >=1.7.0 | Low |
| shap | 52.0 | >=0.42.0 | Low |
| matplotlib | 3.11.0 | >=3.7.0 | Low |
| google-generativeai | 2.13.0 (google-genai) | >=0.3.0 (google-generativeai) | **HIGH** - Different package names! |

### Critical Note: Google Gemini Package
- **Teammate uses:** `google-genai==2.13.0`
- **My uses:** `google-generativeai>=0.3.0`
- These are **different packages** with different APIs
- Must reconcile before integration

---

## 7. Missing Dependencies

### My Files Missing (compared to teammate):
- `fastapi` - Not in my requirements.txt (but code uses it!)
- `uvicorn` - Not in my requirements.txt
- `pydantic` - Not in my requirements.txt (but code imports it!)
- `pydantic-settings` - Not in my requirements.txt

### Teammate Files Missing (compared to my files):
- `imbalanced-learn` - For handling imbalanced datasets
- `lightgbm`, `catboost` - Alternative ML models
- `seaborn` - Additional visualization
- `streamlit` - Alternative UI framework

---

## 8. Circular Dependency Risks

### Current State: No circular dependencies detected

**Teammate:**
- Clean layered architecture prevents cycles
- Services → Model (one direction)
- Routes → Services (one direction)

**My:**
- Flat structure with minimal inter-dependencies
- main.py imports services, services don't import main.py

---

## 9. Integration Impact Analysis

### High-Impact Dependencies

1. **Pydantic Models**
   - Teammate: `backend/model/schemas.py`
   - My: `backend/models.py`
   - **Action:** Merge schemas, resolve field name differences

2. **ML Service**
   - Teammate: `backend/services/prediction_service.py` + `backend/model/pipeline.py`
   - My: `backend/ml_service.py`
   - **Action:** Choose one implementation or merge features

3. **GenAI Service**
   - Teammate: `backend/services/genai_service.py` (with RAG)
   - My: `backend/genai_service.py` (direct API)
   - **Action:** Integrate RAG from teammate into my service

4. **Frontend Styling**
   - Teammate: Custom CSS (`global.css`, `chatbot.css`)
   - My: Tailwind CSS
   - **Action:** Choose one approach; migration required

5. **Frontend Navigation**
   - Teammate: Hash-based routing with pages
   - My: Tab-based single page
   - **Action:** Choose UX approach; significant refactor needed

---

## 10. Recommended Dependency Resolution Order

1. **First:** Reconcile Google Gemini package (`google-genai` vs `google-generativeai`)
2. **Second:** Add missing FastAPI/pydantic to my requirements.txt
3. **Third:** Merge Pydantic schemas (request/response models)
4. **Fourth:** Decide on ML service architecture
5. **Fifth:** Integrate GenAI RAG functionality
6. **Sixth:** Resolve frontend styling approach
7. **Seventh:** Unify navigation/routing pattern
