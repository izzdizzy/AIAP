"""
Pydantic Schemas for Centralized GenAI Endpoints and Widgets
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union
from .context_builder import UnifiedPatientContext, SHAPFactor


class GenAIRequestPayload(BaseModel):
    user_query: Optional[str] = None
    assistant_type: Optional[str] = "cad_coach"  # "cad_coach", "diabetes_explainer", "care_navigator"
    context: Optional[UnifiedPatientContext] = None
    raw_input: Optional[Dict[str, Any]] = None


class GenAIResponsePayload(BaseModel):
    message: str
    widget: Optional[Dict[str, Any]] = None
