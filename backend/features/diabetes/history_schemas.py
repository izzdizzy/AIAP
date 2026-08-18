from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel

from .schemas import HealthProfile


class DiabetesHistoryCreate(BaseModel):
    """Input to POST /history. The prediction is recomputed server-side,
    never accepted from the client."""
    profile: HealthProfile


class DiabetesHistoryOut(BaseModel):
    id: int
    created_at: datetime
    risk_label: str
    risk_probability: float
    risk_band: str
    top_factors: List[Any]
    profile: Dict[str, Any]
