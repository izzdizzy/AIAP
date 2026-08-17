# Integration Plan

**Generated:** Integration Audit for AIAP Project  
**Branch Name:** `IntegrationP`

---

## Executive Summary

This project involves integrating two parallel implementations of a healthcare risk assessment application:
- **Teammate's code:** CAD (Coronary Artery Disease) risk assessment with RAG-based GenAI
- **My code:** Diabetes readmission prediction with direct GenAI API

Both share similar architecture patterns but differ in domain, implementation details, and features.

---

## 1. Main Entrypoint Identification

### Backend Entrypoint
**Chosen:** `backend/main.py` (my version)

**Rationale:**
- Complete FastAPI application with all endpoints
- Robust path resolution
- Comprehensive error handling
- CORS configured for development and production
- Startup event for service initialization

**Teammate's main.py** is only a uvicorn runner that imports from `app.py`.

### Frontend Entrypoint
**Chosen:** Hybrid approach

**Structure:**
- Entry file: `frontend/main.jsx` (teammate location, my content style)
- App component: Use teammate's routing architecture with my components

**Rationale:**
- Teammate's hash-routing provides better UX (bookmarkable URLs)
- My tab-based approach is simpler but less navigable
- Best of both: teammate's structure with my visualizations

---

## 2. Easiest Integration Path

### Phase 1: Backend Integration (Low Risk)

**Step 1.1:** Create merged backend structure
```
backend/
├── main.py              # Keep my version as base
├── app.py               # Add teammate's FastAPI wrapper pattern
├── config.py            # Copy from teammate
├── models.py            # Merge: my fields + teammate's structure
├── ml_service.py        # Keep mine (more features)
├── genai_service.py     # Merge: add teammate's RAG
├── utils.py             # Keep mine
├── requirements.txt     # Merge dependencies
└── services/            # Create from teammate
    ├── __init__.py
    ├── prediction_service.py
    ├── knowledge_service.py
    ├── prompt_builder.py
    └── session_service.py
└── routes/              # Create from teammate
    ├── __init__.py
    └── predict.py
```

**Step 1.2:** Update import paths in main.py
- Change from `from models import ...` to `from .models import ...`
- Or keep absolute imports and configure PYTHONPATH

**Step 1.3:** Reconcile Gemini package
- Use `google-genai==2.13.0` (teammate's version)
- Update genai_service.py to match new API

### Phase 2: Frontend Integration (Medium Risk)

**Step 2.1:** Adopt teammate's folder structure
```
frontend/
├── src/                 # Keep my src/ organization OR move to root
├── main.jsx
├── App.jsx
├── components/
├── pages/
├── hooks/
├── services/
├── styles/
└── utils/
```

**Decision:** Move my files to teammate's flat structure (no src/) for consistency.

**Step 2.2:** Styling decision
- Option A: Migrate to Tailwind (my choice) - requires rewriting all teammate CSS
- Option B: Migrate to custom CSS (teammate choice) - requires rewriting my components
- **Recommended:** Keep Tailwind, add teammate's components with Tailwind classes

### Phase 3: Model & Data Integration (Low Risk)

**Step 3.1:** Keep my model artifacts
- `outputs/readmission_model.joblib`
- `outputs/feature_columns.json`
- `outputs/feature_defaults.json`
- `outputs/threshold.json`

**Step 3.2:** Copy teammate's RAG documents
- `backend/genai_documents/` → needed for knowledge-based chat

---

## 3. Component Integration Priority

### First to Integrate (My Components)

1. **RiskDashboard.jsx** - Unique SHAP visualization, recharts-based
2. **PatientForm.jsx** - File upload support, comprehensive form
3. **ml_service.py** - Clinical scoring, SHAP analysis, robust feature alignment

### To Remain Unchanged (Teammate Components)

1. **AppShell.jsx** - Clean navigation structure
2. **HomePage.jsx** - Good landing page design
3. **ResultsPage.jsx** - Clear results presentation
4. **genai_documents/** - Essential for RAG functionality
5. **knowledge_service.py** - Document retrieval logic
6. **prompt_builder.py** - Structured prompt construction

---

## 4. Required Import/Path Changes

### Backend Python Imports

**Current (my code):**
```python
from models import PatientData
from ml_service import get_ml_service
```

**After integration:**
```python
from backend.models import PatientData
from backend.ml_service import get_ml_service
# OR set PYTHONPATH=/workspace so imports work without 'backend.' prefix
```

### Frontend JavaScript Imports

**Current (my code):**
```javascript
import PatientForm from './components/PatientForm';
```

**After integration (if using teammate structure):**
```javascript
import PatientForm from './components/PatientForm';  // Same if structure preserved
```

### Model Path Updates

**In ml_service.py:**
```python
# Already handles multiple paths
ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
FALLBACK_MODEL_PATH = BASE_DIR / "outputs" / "readmission_model.joblib"
```
No change needed - already robust.

---

## 5. Required Config/Environment Changes

### Environment Variables (.env)

```bash
# Required
GEMINI_KEY="your-gemini-api-key-here"

# Optional (for teammate's pydantic-settings)
# Any additional settings from config.py
```

### requirements.txt (Merged)

```txt
# Web Framework
fastapi==0.116.1
uvicorn==0.35.0
pydantic==2.13.4
pydantic-settings==2.14.2

# Data Processing
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

# Gen AI (use teammate's package)
google-genai==2.13.0

# Utilities
python-dotenv>=1.0.0
requests==2.34.2
```

### frontend/package.json (Merged)

```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-markdown": "^10.1.0",
    "axios": "^1.6.0",
    "recharts": "^2.10.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.1",
    "vite": "^5.0.8",
    "tailwindcss": "^3.4.0"
  }
}
```

---

## 6. Duplicate Dependencies

| Package | Teammate | My | Resolution |
|---------|----------|-----|------------|
| react | ^18.3.1 | ^18.2.0 | Use ^18.3.1 |
| vite | ^8.1.5 | ^5.0.8 | Use ^5.0.8 (v8 may have breaking changes) |
| numpy | 2.4.6 | >=1.24.0 | Compatible |
| pandas | 3.0.3 | >=2.0.0 | Compatible |
| xgboost | 3.3.0 | >=1.7.0 | Compatible |
| google-genai | 2.13.0 | - | Use this, remove google-generativeai |

---

## 7. Missing Dependencies (To Add)

### In My requirements.txt:
- `fastapi==0.116.1`
- `uvicorn==0.35.0`
- `pydantic==2.13.4`
- `pydantic-settings==2.14.2`

### In My frontend/package.json:
- `react-markdown` (for chat message rendering)

---

## 8. Possible Runtime Errors

### High Risk

1. **Import errors** - If PYTHONPATH not set correctly
   - Mitigation: Use absolute imports with `backend.` prefix

2. **Gemini API failures** - Different package APIs
   - Mitigation: Test genai_service.py thoroughly after package switch

3. **Model loading failures** - Wrong path or format
   - Mitigation: Verify `outputs/` contains all required JSON files

### Medium Risk

4. **CORS issues** - If frontend/backend ports mismatch
   - Mitigation: Verify CORS origins in main.py

5. **Tailwind not compiling** - If config missing
   - Mitigation: Ensure tailwind.config.js exists

### Low Risk

6. **Styling glitches** - CSS conflicts during migration
   - Mitigation: Test each component individually

---

## 9. Minimal Steps to Test Combined App

### Backend Testing

```bash
# 1. Install dependencies
cd /workspace
pip install -r requirements.txt

# 2. Set environment
echo "GEMINI_KEY=your-key-here" > .env

# 3. Run backend
cd backend
python main.py

# 4. Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/model-info
```

### Frontend Testing

```bash
# 1. Install dependencies
cd /workspace/frontend
npm install

# 2. Run dev server
npm run dev

# 3. Open browser
# Navigate to http://localhost:5173
```

### Integration Testing

1. Submit patient data via form
2. Verify prediction response with severity score
3. Send chat message
4. Verify GenAI response
5. Upload CSV file
6. Verify parsed data pre-fills form

---

## 10. Recommended Next Change (Smallest Diff)

### Smallest Safe Change: Add Missing Dependencies

**File:** `requirements.txt`

**Action:** Add the four missing packages to my requirements.txt

**Diff:**
```diff
+fastapi==0.116.1
+uvicorn==0.35.0
+pydantic==2.13.4
+pydantic-settings==2.14.2
```

**Risk:** Zero - adding dependencies doesn't break existing code

**Benefit:** Enables running teammate's code structure

---

## 11. Structure Option Selected

### Chosen: **Option A - Separate but Mirrored**

**Rationale:**
1. Preserves teammate's code as reference (read-only)
2. Allows incremental integration without breaking either codebase
3. Conflicts can be resolved one file at a time
4. Easy to rollback individual changes
5. Clear audit trail of what was changed

**Implementation:**
- `_integration_workspace/` mirrors teammate's structure
- My files copied into matching locations
- Conflicts placed in `_integration_workspace/conflicts/`
- Original `aiappprj_test-main/` untouched

---

## 12. Files Requiring Manual Review

### Critical (Must Review Before Running)

1. `backend/main.py` - Choose architecture
2. `backend/models.py` vs `backend/model/schemas.py` - Merge Pydantic models
3. `backend/genai_service.py` - Reconcile Gemini package difference
4. `frontend/App.jsx` - Choose navigation paradigm
5. Domain alignment - CAD vs diabetes (business decision needed)

### Important (Review Before Production)

6. `backend/ml_service.py` - Verify clinical rules are correct
7. `frontend/components/*` - Ensure consistent styling
8. `docker-compose.yml` - Verify ports and volumes
9. `.env` configuration - Ensure all variables documented

### Nice to Have

10. Training script integration
11. Sample data consolidation
12. Documentation merge

---

## 13. Blocked Items (No Package Installation Allowed)

The following items would normally require package installation but cannot be completed under current constraints:

1. **Installing merged requirements.txt** - Would need `pip install`
2. **Installing frontend dependencies** - Would need `npm install`
3. **Building frontend for production** - Would need `npm run build`
4. **Running training scripts** - Would need all ML packages installed
5. **Testing Docker containers** - Would need docker-compose

**Workaround:** All file modifications are prepared; installation commands are documented in reports for manual execution by user.

---

## 14. Integration Checklist

- [ ] Create `_integration_workspace/` with mirrored structure
- [ ] Copy teammate files to workspace (read-only reference)
- [ ] Copy my files to matching locations
- [ ] Place conflicting files in `conflicts/` subdirectory
- [ ] Generate merged `requirements.txt`
- [ ] Generate merged `package.json`
- [ ] Update `.env` template with all required variables
- [ ] Document manual review items
- [ ] Create GitHub branch `IntegrationP`

---

## 15. Success Criteria

Integration is successful when:
1. Backend starts without import errors
2. Frontend builds without compilation errors
3. `/health` endpoint returns 200
4. `/api/predict` accepts valid patient data
5. `/api/chat` returns GenAI response
6. File upload parses CSV correctly
7. No console errors in browser DevTools
