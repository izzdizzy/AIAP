"""
Hospital Readmission Predictor Backend Package
===============================================

This package provides the FastAPI backend for the Hospital Readmission Predictor.
It includes:
- ML inference service with clinical severity scoring
- Gen AI chat service with safety guardrails
- File upload parsing utilities
- RESTful API endpoints

Usage:
    from backend import app  # FastAPI application
    from backend.ml_service import get_ml_service
    from backend.genai_service import get_genai_service
"""

from .main import app
from .ml_service import get_ml_service, MLService
from .genai_service import get_genai_service, GenAIService

__version__ = "1.0.0"
__all__ = ["app", "get_ml_service", "get_genai_service", "MLService", "GenAIService"]
