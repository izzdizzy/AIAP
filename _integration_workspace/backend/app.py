from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import teammate CAD routers
from .routes.predict import router as predict_router
from .services.chatbot import router as chatbot_router

# Import diabetes module routers (conditionally based on feature flag)
from .config import settings

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

# Include diabetes routes (new module)
if settings.ENABLE_DIABETES:
    from .routers.diabetes.readmission import router as diabetes_router
    app.include_router(diabetes_router, prefix='/api', tags=['Diabetes'])


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
    
    return {
        "message": "Healthcare Risk Assessment API",
        "version": "0.2.0",
        "modules": modules,
        "endpoints": {
            "cad_predict": "POST /api/predict" if settings.ENABLE_CAD else None,
            "cad_chat": "POST /api/chat/session" if settings.ENABLE_CAD else None,
            "diabetes_health": "GET /api/v1/diabetes/health" if settings.ENABLE_DIABETES else None,
            "diabetes_predict": "POST /api/v1/diabetes/predict" if settings.ENABLE_DIABETES else None,
            "diabetes_chat": "POST /api/v1/diabetes/chat" if settings.ENABLE_DIABETES else None,
            "diabetes_upload": "POST /api/v1/diabetes/upload" if settings.ENABLE_DIABETES else None,
            "diabetes_model_info": "GET /api/v1/diabetes/model-info" if settings.ENABLE_DIABETES else None,
        }
    }