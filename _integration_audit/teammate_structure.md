# Teammate Structure Analysis

**Source:** `aiappprj_test-main/aiappprj_test-main/`  
**Status:** READ-ONLY (must not be modified)

---

## Directory Tree

```
aiappprj_test-main/
├── backend/
│   ├── __init__.py
│   ├── app.py              # FastAPI application wrapper
│   ├── config.py           # Pydantic settings configuration
│   ├── main.py             # Uvicorn entry point
│   ├── genai_documents/    # Knowledge base for RAG
│   │   ├── Alcohol and Smoking.txt
│   │   ├── Cholesterol and Heart Disease.txt
│   │   ├── Heart Health Basic Dietary Guidelines.txt
│   │   ├── High Blood Pressure Healthy Eating Guide.txt
│   │   ├── How to Keep Your Heart Healthy The Essential Dos and Donts.txt
│   │   └── system_prompt.txt
│   ├── model/              # ML model layer
│   │   ├── __init__.py
│   │   ├── constants.py    # Feature constants and mappings
│   │   ├── formatter.py    # Response formatting
│   │   ├── pipeline.py     # Main prediction pipeline
│   │   ├── predict.py      # Prediction logic
│   │   ├── preprocess.py   # Data preprocessing
│   │   ├── response.py     # Response classes
│   │   ├── schemas.py      # Pydantic schemas
│   │   └── translations.py # Multi-language support
│   ├── routes/             # API route handlers
│   │   ├── __init__.py
│   │   └── predict.py      # Prediction endpoint
│   └── services/           # Business logic layer
│       ├── __init__.py
│       ├── chatbot.py      # Chat router
│       ├── genai_service.py    # Gemini API integration
│       ├── knowledge_service.py # Document retrieval
│       ├── prediction_service.py # ML inference wrapper
│       ├── prompt_builder.py   # Prompt construction
│       └── session_service.py  # Session management
│
├── frontend/
│   ├── App.jsx               # Root component with hash routing
│   ├── main.jsx              # React DOM render
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   ├── components/           # Reusable UI components
│   │   ├── AppShell.jsx      # Layout shell with navigation
│   │   ├── ChatMessage.jsx   # Chat message bubble
│   │   ├── ChatWindow.jsx    # Chat container
│   │   ├── Disclaimer.jsx    # Medical disclaimer
│   │   ├── FormField.jsx     # Form input component
│   │   ├── PrimaryButton.jsx # Styled button
│   │   ├── ResultCard.jsx    # Result display card
│   │   └── SectionCard.jsx   # Section container
│   ├── hooks/                # Custom React hooks
│   │   └── useAssessmentForm.js  # Form state management
│   ├── pages/                # Page components (routes)
│   │   ├── AssessmentPage.jsx    # Risk assessment form
│   │   ├── ChatbotPage.jsx       # Chat interface
│   │   ├── HomePage.jsx          # Landing page
│   │   └── ResultsPage.jsx       # Results display
│   ├── services/             # API client layer
│   │   ├── chatService.js        # Chat API calls
│   │   └── predictionService.js  # Prediction API calls
│   ├── styles/               # CSS stylesheets
│   │   ├── chatbot.css
│   │   └── global.css
│   └── utils/                # Utility functions
│       ├── assessmentConfig.js   # Form configuration
│       ├── payload.js            # Request payload builder
│       ├── risk.js               # Risk calculation utils
│       ├── storage.js            # LocalStorage helpers
│       └── 5files/               # Duplicate backup folder
│           ├── AssessmentPage.jsx
│           ├── FormField.jsx
│           ├── assessmentConfig.js
│           ├── payload.js
│           └── useAssessmentForm.js
│
├── models/                   # Pre-trained model files
│   ├── exported_model2.ubj   # XGBoost model (UBJ format)
│   ├── imputation_bundle.pkl
│   └── preprocessing_bundle.pkl
│
├── .model_dev/               # Model development notebooks
│   ├── model2.ipynb
│   ├── model3.ipynb
│   ├── model3old.ipynb
│   ├── model4.ipynb
│   ├── predict.py
│   └── test.py
│
├── .env_example              # Environment template
├── .gitignore
├── .gitattributes
├── requirements.txt          # Pinned Python dependencies
└── todo.txt                  # Task list
```

---

## Architecture Overview

### Backend Architecture (Teammate)

```
main.py (entry)
    ↓
app.py (FastAPI instance)
    ↓
routes/
    ├── predict.py → POST /api/predict
    └── chatbot.py → POST /api/chat
    ↓
services/
    ├── prediction_service.py → model/pipeline.py
    ├── genai_service.py → Google Gemini API
    ├── knowledge_service.py → Document retrieval
    └── session_service.py → Session management
    ↓
model/
    ├── schemas.py (Pydantic models)
    ├── pipeline.py (orchestration)
    ├── predict.py (inference)
    ├── preprocess.py (data prep)
    └── formatter.py (output formatting)
```

**Key Characteristics:**
- Modular service-based architecture
- Separation of concerns (routes → services → model)
- Pydantic settings via `config.py`
- RAG-based GenAI with document knowledge base
- Hash-based frontend routing integration

### Frontend Architecture (Teammate)

```
main.jsx
    ↓
App.jsx (hash-based router)
    ↓
AppShell (layout + navigation)
    ↓
Pages:
    ├── HomePage → Start assessment
    ├── AssessmentPage → Form input
    ├── ResultsPage → Show prediction results
    └── ChatbotPage → AI care navigation
    ↓
Components (reusable):
    ├── FormField, PrimaryButton, SectionCard
    ├── ChatWindow, ChatMessage
    └── ResultCard, Disclaimer
    ↓
Services (API):
    ├── predictionService.js
    └── chatService.js
    ↓
Utils:
    ├── assessmentConfig, payload, risk, storage
```

**Key Characteristics:**
- Hash-based client-side routing (`#assessment`, `#results`, `#chat`)
- Page-based organization
- Reusable component library
- Custom hook for form state (`useAssessmentForm`)
- LocalStorage persistence for assessment state
- CSS-based styling (no Tailwind)

---

## Key Files Detail

### Backend Entry Point
**File:** `backend/main.py`
```python
from .app import app

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('backend.main:app', host='0.0.0.0', port=8000, reload=True)
```

### FastAPI App
**File:** `backend/app.py`
```python
from fastapi import FastAPI
from .routes.predict import router as predict_router
from .services.chatbot import router as chatbot_router

app = FastAPI(title='CAD Risk Assessment API', ...)
app.add_middleware(CORSMiddleware, allow_origins=['*'], ...)
app.include_router(predict_router, prefix='/api', tags=['prediction'])
app.include_router(chatbot_router, prefix='/api', tags=['chat'])
```

### Frontend Entry Point
**File:** `frontend/main.jsx`
```jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/global.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode><App /></React.StrictMode>
);
```

### Main App Component
**File:** `frontend/App.jsx`
- Uses `window.location.hash` for routing
- Manages `assessmentState` with localStorage persistence
- Pages: HomePage, AssessmentPage, ResultsPage, ChatPage
- Navigation via `window.location.hash = route`

---

## Dependencies (Teammate)

### Python (requirements.txt)
```
fastapi==0.116.1
uvicorn==0.35.0
pydantic==2.13.4
pydantic-settings==2.14.2
google-genai==2.13.0
xgboost==3.3.0
numpy==2.4.6
pandas==3.0.3
scikit-learn==1.9.0
shap==0.52.0
matplotlib==3.11.0
requests==2.34.2
...
```

### Node.js (frontend/package.json)
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-markdown": "^10.1.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.1",
    "vite": "^8.1.5"
  }
}
```

---

## Environment Variables

**File:** `.env_example`
```
GEMINI_KEY="AQ.GEMINI"
```

Required environment variables:
- `GEMINI_KEY` - Google Gemini API key

---

## Model Files

Located in `models/`:
- `exported_model2.ubj` - XGBoost model in Universal Binary JSON format
- `imputation_bundle.pkl` - Pickled imputation transformers
- `preprocessing_bundle.pkl` - Pickled preprocessing pipeline

---

## Notes

1. **No Docker configuration** - Teammate does not have Dockerfiles or docker-compose.yml
2. **No data directory** - No raw/processed data included
3. **No training scripts** - Training appears to be in `.model_dev/` notebooks only
4. **Clean separation** - Clear layering between routes, services, and model
5. **RAG implementation** - Has document-based knowledge retrieval for GenAI
6. **Session management** - Has session_service for conversation tracking
