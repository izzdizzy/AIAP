from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String

from ...core.db import Base


class DiabetesAssessment(Base):
    __tablename__ = 'diabetes_assessments'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True, nullable=False)
    input_profile = Column(JSON, nullable=False)
    risk_label = Column(String(40), nullable=False)
    risk_probability = Column(Float, nullable=False)
    risk_band = Column(String(20), nullable=False)
    top_factors = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True, nullable=False)
