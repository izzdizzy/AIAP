# Conflict Report

**Purpose:** Identify file path conflicts, naming conflicts, and integration risks

---

## 1. Direct Path Conflicts

### Backend Directory Conflicts

| Path | Teammate File | My File | Resolution Required |
|------|--------------|---------|---------------------|
| `backend/main.py` | Uvicorn runner (imports .app) | Full FastAPI app | **HIGH** - Different purposes |
| `backend/requirements.txt` | Pinned versions | Flexible versions | Merge needed |
| `backend/genai_service.py` | With RAG, prompt_builder | Direct API call | Merge features |

### Frontend Directory Conflicts

| Path | Teammate File | My File | Resolution Required |
|------|--------------|---------|---------------------|
| `frontend/main.jsx` | Entry point | N/A (mine is in src/) | Different locations |
| `frontend/App.jsx` | Hash-routing root | Tab-based root (in src/) | Different architectures |
| `frontend/index.html` | At frontend/ | At frontend/ | Similar content |
| `frontend/package.json` | React 18.3, no Tailwind | React 18.2, with Tailwind | Merge deps |
| `frontend/vite.config.js` | Vite 8 config | Vite 5 config | Version conflict |

---

## 2. Functional Overlaps (Same Purpose, Different Implementation)

### ML Prediction Service

| Aspect | Teammate | My | Notes |
|--------|----------|-----|-------|
| Location | `services/prediction_service.py` + `model/pipeline.py` | `ml_service.py` | |
| Model loading | Via pipeline from `models/` | Direct from `outputs/` or `artifacts/` | Different paths |
| Feature handling | preprocess.py | _align_features() | Similar logic |
| Output format | PredictionResponse via schemas.py | Dict → Pydantic in main.py | Compatible |
| SHAP support | Not explicit | Full SHAP integration | My has more features |
| Clinical scoring | Not visible | Clinical adjustment rules | My has more features |

### GenAI Service

| Aspect | Teammate | My | Notes |
|--------|----------|-----|-------|
| Package | `google-genai==2.13.0` | `google-generativeai>=0.3.0` | **CONFLICT** |
| RAG | Yes (knowledge_service.py) | No | Teammate has RAG |
| Prompt building | prompt_builder.py | Inline in service | |
| Session tracking | session_service.py | None | Teammate has sessions |
| Safety filters | Implicit | Explicit fallback handling | Both have safety |

### Pydantic Models

| Aspect | Teammate | My | Notes |
|--------|----------|-----|-------|
| Location | `model/schemas.py` | `models.py` | |
| PatientData | CAD risk fields | Readmission fields | Different domains! |
| PredictionResponse | severity_score, urgency_level | clinical_severity_score, urgency_level | Similar structure |
| ChatRequest/Response | Present | Present | Compatible |

### Frontend App Structure

| Aspect | Teammate | My | Notes |
|--------|----------|-----|-------|
| Navigation | Hash routing (#assessment, #results, #chat) | Tab state (activeTab) | Different UX |
| Pages | HomePage, AssessmentPage, ResultsPage, ChatbotPage | Single page with tabs | |
| Components | 8 reusable components | 4 components | Teammate more modular |
| Styling | Custom CSS (global.css, chatbot.css) | Tailwind CSS | **INCOMPATIBLE** |
| Form state | useAssessmentForm hook + localStorage | Inline state | |
| API calls | predictionService.js, chatService.js | api.js (unified) | |

---

## 3. Domain Mismatch

### Critical Finding: Different Medical Domains

| Domain | Teammate | My |
|--------|----------|-----|
| **Condition** | CAD (Coronary Artery Disease) Risk | Diabetes Readmission Prediction |
| **Model** | CAD risk model | XGBoost readmission model |
| **Features** | Cardiac risk factors | Diabetes patient history |
| **Assessment** | CAD risk questionnaire | Hospital admission data |
| **Documents** | Heart health guides | (No RAG documents) |

**Implication:** These are fundamentally different applications that need domain alignment before full integration.

---

## 4. File Content Conflicts

### backend/main.py

**Teammate version** (6 lines):
```python
from .app import app

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('backend.main:app', host='0.0.0.0', port=8000, reload=True)
```

**My version** (429 lines):
- Full FastAPI application
- All endpoints defined inline
- CORS configuration
- Startup events
- Error handling

**Resolution:** Cannot merge directly. Must choose one architecture.

### frontend/App.jsx

**Teammate version**:
- Hash-based routing
- Multiple page components
- Assessment state persistence
- Navigation guards

**My version**:
- Tab-based navigation
- Single-page layout
- Inline state management
- No routing

**Resolution:** UX decision required. Significant refactor either way.

---

## 5. Import Path Conflicts

### Python Imports

**Teammate uses relative imports:**
```python
from .app import app
from .routes.predict import router
from ..model.pipeline import run_prediction
from ..services.genai_service import generate_response
```

**My uses absolute/top-level imports:**
```python
from models import PatientData, PredictionResponse
from ml_service import get_ml_service
from genai_service import get_genai_service
from utils import parse_uploaded_file_bytes
```

**Issue:** If files are merged, all imports must be updated.

### JavaScript Imports

**Teammate:**
```javascript
import AppShell from './components/AppShell';
import AssessmentPage from './pages/AssessmentPage';
import { submitAssessment } from './services/predictionService';
```

**My:**
```javascript
import PatientForm from './components/PatientForm';
import { predictPatient } from './services/api';
```

**Issue:** Different folder structures (`src/` vs direct), different component names.

---

## 6. Model File Conflicts

| Model File | Teammate | My | Format |
|------------|----------|-----|--------|
| Primary model | `models/exported_model2.ubj` | `outputs/readmission_model.joblib` | UBJ vs joblib |
| Preprocessing | `models/preprocessing_bundle.pkl` | (embedded in ml_service) | pkl vs code |
| Imputation | `models/imputation_bundle.pkl` | (baseline defaults) | pkl vs JSON |

**Issue:** Different model formats, different feature sets (CAD vs diabetes).

---

## 7. Environment Variable Conflicts

| Variable | Teammate | My |
|----------|----------|-----|
| Gemini Key | `GEMINI_KEY` | `GEMINI_KEY` (expected) |
| Other | (via pydantic-settings) | python-dotenv |

**Status:** Compatible, but teammate uses pydantic-settings which my code doesn't have.

---

## 8. Docker Configuration Conflicts

**My files have:**
- `docker-compose.yml`
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `frontend/nginx.conf`

**Teammate has:**
- No Docker configuration

**Resolution:** Keep my Docker setup; teammate files can be added later if needed.

---

## 9. Conflicts Requiring Manual Review

### HIGH PRIORITY

1. **backend/main.py** - Completely different implementations
2. **frontend/App.jsx** - Different navigation paradigms
3. **Domain mismatch** - CAD vs Diabetes Readmission
4. **Google Gemini package** - `google-genai` vs `google-generativeai`
5. **Pydantic models** - Different field names and purposes

### MEDIUM PRIORITY

6. **Frontend styling** - Tailwind vs custom CSS
7. **ML service architecture** - Service class vs pipeline functions
8. **GenAI RAG** - Has documents vs no documents
9. **Session management** - Has sessions vs stateless
10. **Model formats** - UBJ vs joblib

### LOW PRIORITY

11. **Vite version** - 8.x vs 5.x
12. **React version** - 18.3 vs 18.2
13. **Folder structure** - `src/` subfolder vs direct

---

## 10. Files to Copy to Conflicts Area

The following files should be copied to `_integration_workspace/conflicts/` for manual review:

1. `backend/main.py` (my version) → conflicts/my_backend_main.py
2. `backend/models.py` → conflicts/my_models.py
3. `backend/ml_service.py` → conflicts/my_ml_service.py
4. `frontend/src/App.jsx` → conflicts/my_App.jsx
5. `frontend/src/services/api.js` → conflicts/my_api.js
6. `frontend/src/components/*` → conflicts/my_components/

---

## 11. Resolution Strategy Summary

| Conflict Type | Recommended Action |
|--------------|-------------------|
| backend/main.py | Keep my version (more complete), add teammate's route structure |
| frontend/App.jsx | Keep teammate's (better UX with routing), adapt my components |
| Domain mismatch | **BLOCKER** - Must align on single medical domain |
| Gemini package | Use teammate's `google-genai` (newer, matches their code) |
| Pydantic models | Merge: keep my fields, add teammate's structure |
| Styling | Choose one (Tailwind recommended for maintainability) |
| Model files | Use my joblib model (has training pipeline) |
| Docker | Keep my configuration |
