from fastapi import APIRouter, HTTPException
from pathlib import Path

from .schemas import (
    AssessmentRequest,
    PredictionResponse,
    ChatSessionRequest,
    ChatSessionResponse,
    ChatMessageRequest,
    ChatMessageResponse,
)
from .prediction_service import predict_cad_risk
from .session_service import (
    create_session,
    get_session,
    add_user_message,
    add_assistant_message,
)
from .knowledge_service import get_relevant_knowledge
from .prompt_builder import build_prompt
from .genai_service import generate_response
from ...services.genai import get_cad_coach_service, build_unified_context

router = APIRouter(tags=["CAD Risk Assessment & Chat"])


@router.post('/predict', response_model=PredictionResponse)
def predict(payload: AssessmentRequest) -> PredictionResponse:
    return predict_cad_risk(payload.model_dump())


@router.post("/chat/session", response_model=ChatSessionResponse)
def create_chat_session(payload: ChatSessionRequest):
    session_id = create_session(
        assessment=payload.assessment,
        prediction=payload.prediction,
    )
    return ChatSessionResponse(session_id=session_id)


@router.post("/chat/message", response_model=ChatMessageResponse)
def chat(payload: ChatMessageRequest):
    session = get_session(payload.session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found."
        )

    add_user_message(payload.session_id, payload.message)

    try:
        context = build_unified_context({
            "assessment": session.get("assessment"),
            "prediction": session.get("prediction")
        })
        service = get_cad_coach_service()
        res = service.generate_advice(context=context, user_query=payload.message)
        reply = res.get("message", "Unable to generate CAD advice.")
    except Exception as e:
        reply = f"I am unable to generate a response right now. Error: {str(e)}"

    add_assistant_message(payload.session_id, reply)

    return ChatMessageResponse(reply=reply)
