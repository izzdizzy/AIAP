from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import teammate CAD routers
from .routes.predict import router as predict_router
from .services.chatbot import router as chatbot_router

# Import diabetes module routers (conditionally based on feature flag)
from .config import settings

# Import the readmission router from the new location
from .routers.readmission import router as readmission_router

# Import the diabetes risk classifier router
from .routers.diabetes import router as diabetes_router

app = FastAPI(
    title='Healthcare Risk Assessment API',
    version='0.2.0',
    description='FastAPI application with CAD Risk Assessment and Diabetes Readmission Prediction modules.'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)


# =============================================================================
# MODULE ROUTER REGISTRATION
# =============================================================================

# Include teammate CAD routes (preserved functionality)
if settings.ENABLE_CAD:
    app.include_router(predict_router, prefix='/api', tags=['CAD Prediction'])
    app.include_router(chatbot_router, prefix='/api', tags=['CAD Chat'])

# Include readmission routes via the new router at /readmission prefix
if settings.ENABLE_DIABETES:
    app.include_router(readmission_router, prefix='/readmission', tags=['Hospital Readmission'])
    # Include diabetes risk classifier routes at /diabetes prefix
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