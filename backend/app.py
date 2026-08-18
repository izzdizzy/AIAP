from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .core.db import Base, engine
from .features.auth import router as auth_router
from .features.history import router as history_router
from .features.cad import router as cad_router
from .features.readmission import router as readmission_router
from .features.diabetes import router as diabetes_router
from .routers.genai_router import router as genai_router

app = FastAPI(
    title='Healthcare Risk Assessment API',
    version='0.2.0',
    description='FastAPI application with CAD Risk Assessment, Hospital Readmission, and Diabetes Risk Classifier modules.'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

Base.metadata.create_all(bind=engine)


# =============================================================================
# MODULE ROUTER REGISTRATION
# =============================================================================

app.include_router(genai_router)
app.include_router(auth_router, prefix='/auth', tags=['Authentication'])
app.include_router(history_router, prefix='/history', tags=['Assessment History'])

if settings.ENABLE_CAD:
    app.include_router(cad_router, prefix='/api', tags=['CAD Risk Assessment & Chat'])

if settings.ENABLE_DIABETES:
    app.include_router(readmission_router, prefix='/readmission', tags=['Hospital Readmission'])
    app.include_router(diabetes_router, prefix='/diabetes', tags=['Diabetes Risk Classifier'])


# =============================================================================
# ROOT ENDPOINT
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    modules = []
    if settings.ENABLE_CAD:
        modules.append("CAD Risk Assessment")
    if settings.ENABLE_DIABETES:
        modules.append("Diabetes Readmission Prediction")
        modules.append("Diabetes Risk Classifier")
    
    return {
        "message": "Healthcare Risk Assessment API",
        "version": "0.2.0",
        "modules": modules,
        "endpoints": {
            "cad_predict": "POST /api/predict" if settings.ENABLE_CAD else None,
            "cad_chat": "POST /api/chat/session" if settings.ENABLE_CAD else None,
            "readmission_health": "GET /api/v1/readmission/health" if settings.ENABLE_DIABETES else None,
            "readmission_predict": "POST /api/v1/readmission/predict" if settings.ENABLE_DIABETES else None,
            "readmission_chat": "POST /api/v1/readmission/chat" if settings.ENABLE_DIABETES else None,
            "readmission_upload": "POST /api/v1/readmission/upload" if settings.ENABLE_DIABETES else None,
            "readmission_model_info": "GET /api/v1/readmission/model-info" if settings.ENABLE_DIABETES else None,
            "original_readmission": {
                "health": "GET /readmission/health",
                "predict": "POST /readmission/api/predict",
                "chat": "POST /readmission/api/chat",
                "upload": "POST /readmission/api/upload",
                "model_info": "GET /readmission/api/model-info"
            },
            "diabetes": {
                "health": "GET /diabetes/health",
                "predict": "POST /diabetes/predict",
                "explain": "POST /diabetes/explain"
            }
        }
    }