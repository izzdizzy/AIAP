
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

###  Manual Steps

1. Install Dependencies (blocked by rules - user must run)
   ```bash
   pip install -r requirements.merged.txt
   cd frontend && npm install
   ```

2. Place Model Files
   - Ensure diabetes model exists at artifacts/diabetes/model.joblib
   - Or run training script to generate artifacts

3. Configure .env
   ```
   GEMINI_KEY=your_api_key
   GEMINI__API_KEY=your_api_key
   ENABLE_CAD=true
   ENABLE_DIABETES=true
   ```

