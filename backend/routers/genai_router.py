"""
Centralized GenAI FastAPI Router
Exposes decoupled GenAI endpoints for CAD Coach, Diabetes Explainer, and Care Navigator.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..services.genai.schemas import GenAIRequestPayload, GenAIResponsePayload
from ..services.genai.context_builder import build_unified_context, UnifiedPatientContext
from ..services.genai.cad_coach import get_cad_coach_service
from ..services.genai.diabetes_explainer import get_diabetes_explainer_service
from ..services.genai.care_navigator import get_care_navigator_service

router = APIRouter(prefix="/api/genai", tags=["Centralized GenAI AI-Workspace"])


def _extract_context(payload: GenAIRequestPayload) -> UnifiedPatientContext:
    if payload.context:
        return payload.context
    if payload.raw_input:
        return build_unified_context(payload.raw_input)
    return build_unified_context({})


@router.post("/chat", response_model=GenAIResponsePayload)
async def genai_chat(payload: GenAIRequestPayload):
    """
    Unified multi-assistant GenAI chat endpoint supporting cad_coach, diabetes_explainer, and care_navigator.
    """
    try:
        context = _extract_context(payload)
        assistant = (payload.assistant_type or "cad_coach").lower()

        if assistant == "diabetes_explainer":
            service = get_diabetes_explainer_service()
            res = service.generate_explanation(context=context, user_query=payload.user_query, history=payload.history)
        elif assistant == "care_navigator":
            service = get_care_navigator_service()
            res = service.generate_navigation_advice(context=context, user_query=payload.user_query, history=payload.history)
        else:
            service = get_cad_coach_service()
            res = service.generate_advice(context=context, user_query=payload.user_query, history=payload.history)

        return GenAIResponsePayload(
            message=res.get("message", ""),
            widget=res.get("widget")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GenAI response generation failed: {str(e)}")


@router.post("/cad-coach", response_model=GenAIResponsePayload)
async def cad_coach_endpoint(payload: GenAIRequestPayload):
    try:
        context = _extract_context(payload)
        service = get_cad_coach_service()
        res = service.generate_advice(context=context, user_query=payload.user_query, history=payload.history)
        return GenAIResponsePayload(message=res.get("message", ""), widget=res.get("widget"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CAD Coach failed: {str(e)}")


@router.post("/diabetes-explainer", response_model=GenAIResponsePayload)
async def diabetes_explainer_endpoint(payload: GenAIRequestPayload):
    try:
        context = _extract_context(payload)
        service = get_diabetes_explainer_service()
        res = service.generate_explanation(context=context, user_query=payload.user_query, history=payload.history)
        return GenAIResponsePayload(message=res.get("message", ""), widget=res.get("widget"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diabetes Explainer failed: {str(e)}")


@router.post("/care-navigator", response_model=GenAIResponsePayload)
async def care_navigator_endpoint(payload: GenAIRequestPayload):
    try:
        context = _extract_context(payload)
        service = get_care_navigator_service()
        res = service.generate_navigation_advice(context=context, user_query=payload.user_query, history=payload.history)
        return GenAIResponsePayload(message=res.get("message", ""), widget=res.get("widget"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Care Navigator failed: {str(e)}")
