from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.predict import router as predict_router
from .services.chatbot import router as chatbot_router

app = FastAPI(
    title='CAD Risk Assessment API',
    version='0.1.0',
    description='FastAPI wrapper for the trained CAD prediction pipeline.'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)


app.include_router(predict_router, prefix='/api', tags=['prediction'])
app.include_router(chatbot_router, prefix='/api', tags=['chat'])