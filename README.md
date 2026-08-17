# Healthcare Risk Assessment Application - Integration Workspace

**Purpose:** Safe integration environment for merging teammate and my code

**Branch:** `IntegrationP`

**Status:** Phase 2 Integration Complete - Modular Multi-Assessment Architecture Implemented

---

## Quick Start

### Backend
```bash
pip install -r requirements.merged.txt
python -m uvicorn backend.main:app --reload
```

### Frontend
```bash
cd frontend && npm install
npm run dev
```

### Access
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

---

## Modules

| Module | Domain | API Prefix | Status |
|--------|--------|------------|--------|
| CAD Risk Assessment | Teammate | `/api/*` | Preserved |
| Diabetes Readmission | My Domain | `/api/v1/diabetes/*` | Added |

---

## Structure

See full tree in original README. Key additions marked with [NEW]:

- `backend/app.py` - Modified with feature flags
- `backend/config.py` - Added ENABLE_CAD/ENABLE_DIABETES
- `backend/routers/diabetes/` [NEW]
- `backend/services/diabetes/` [NEW]
- `backend/schemas/diabetes/` [NEW]
- `frontend/pages/diabetes/` [NEW]
- `frontend/services/diabetes/` [NEW]
- `requirements.merged.txt` [NEW]

---

## Integration Status

### Phase 2 Completed - Modular Architecture Implemented

#### Backend
- [x] Modified app.py with feature flags and conditional router registration
- [x] Modified config.py with ENABLE_CAD/ENABLE_DIABETES flags
- [x] Created routers/diabetes/readmission.py with full REST API
- [x] Created services/diabetes/ml_service.py for XGBoost inference
- [x] Created services/diabetes/genai_service.py with google-generativeai SDK
- [x] Created schemas/diabetes/__init__.py with Pydantic models
- [x] Preserved all teammate CAD functionality

#### Frontend
- [x] Created pages/diabetes/DiabetesAssessmentPage.jsx (standalone page)
- [x] Created services/diabetes/api.js API client
- [x] Preserved all teammate CAD pages and components
- [x] Preserved hash routing in App.jsx

#### Documentation
- [x] Updated README.md with integration summary
- [x] Created requirements.merged.txt
- [x] Created _integration_audit/genai_dependency_decision.md

### Pending Manual Steps

1. Install Dependencies (blocked by rules - user must run)
   ```bash
   pip install -r requirements.merged.txt
   cd frontend && npm install
   ```

2. Port PatientForm Component (optional enhancement)
   - Copy from conflicts/my_components/PatientForm.jsx to frontend/components/diabetes/
   - Update imports in DiabetesAssessmentPage.jsx

3. Add Diabetes Route to Main Navigation (optional)
   - Update frontend/App.jsx to include diabetes in hash routing
   - Add navigation button in AppShell or HomePage

4. Place Model Files
   - Ensure diabetes model exists at artifacts/diabetes/model.joblib
   - Or run training script to generate artifacts

5. Configure .env
   ```
   GEMINI_KEY=your_api_key
   ENABLE_CAD=true
   ENABLE_DIABETES=true
   ```

---

## API Endpoints

### CAD Module (Teammate)
- GET / - Root endpoint
- POST /api/predict - CAD prediction
- POST /api/chat/session - Create chat session
- POST /api/chat/message - Send message

### Diabetes Module (New)
- GET /api/v1/diabetes/health - Health check
- POST /api/v1/diabetes/predict - Readmission prediction
- POST /api/v1/diabetes/chat - Care navigation chat
- POST /api/v1/diabetes/upload - File upload
- GET /api/v1/diabetes/model-info - Model metadata

---

## GenAI SDK Decision

Both modules use different Google Gemini SDKs that coexist:
- CAD: `google-genai` (new SDK)
- Diabetes: `google-generativeai` (legacy SDK)

See `_integration_audit/genai_dependency_decision.md` for full analysis.

---

## Known Issues

1. PatientForm component placeholder in DiabetesAssessmentPage.jsx
2. Diabetes module not integrated into main App.jsx navigation
3. Model files must be placed manually before testing

---

## Next Steps

1. User installs dependencies
2. User places diabetes model files
3. User configures .env with GEMINI_KEY
4. Test backend endpoints via /docs
5. Optionally port PatientForm and integrate into main nav
