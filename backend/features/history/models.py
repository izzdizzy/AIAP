from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String

from ...core.db import Base


class ModuleAssessment(Base):
    """Generic saved assessment for modules without their own history table
    (CAD, Readmission). Diabetes uses its dedicated DiabetesAssessment table."""

    __tablename__ = 'module_assessments'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True, nullable=False)
    module = Column(String(20), index=True, nullable=False)
    payload = Column(JSON, nullable=False)
    result = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True, nullable=False)
