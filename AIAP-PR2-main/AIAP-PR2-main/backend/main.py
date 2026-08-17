"""
FastAPI backend for the Personal Chronic Disease Risk Monitor (diabetes part).

Endpoints:
  GET  /health           - quick check that the API and model are up
  POST /predict          - health profile -> diabetes risk (uses the ML model)
  POST /explain          - health profile -> risk + plain-language explanation
                           (uses the ML model, then the Gen AI explainer)

Run locally with:
  uvicorn main:app --reload
Then open http://127.0.0.1:8000/docs to try it in the browser.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from schemas import (HealthProfile, PredictionResponse,
                     ExplainRequest, ExplainResponse)
from model_service import DiabetesModel
from genai_service import generate_explanation

# A small dict holds resources loaded at startup (the trained model).
resources = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the model ONCE when the server starts, not on every request.
    This is the current FastAPI pattern (replaces the deprecated on_event)."""
    print("Loading diabetes model...")
    resources["model"] = DiabetesModel()
    print("Model loaded. API ready.")
    yield
    # Runs on shutdown: release the model.
    resources.clear()
    print("Shutdown: resources released.")


app = FastAPI(
    title="Chronic Disease Risk Monitor - Diabetes API",
    description="Predicts diabetes risk and explains it in plain language.",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow a separate frontend (e.g. a web app on another port) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # fine for a student project / local demo
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Confirms the server is running and the model is loaded."""
    return {"status": "ok", "model_loaded": "model" in resources}


@app.post("/predict", response_model=PredictionResponse)
def predict(profile: HealthProfile):
    """Run the trained classifier on one health profile and return the risk."""
    # profile is already validated by Pydantic. Convert to a plain dict.
    result = resources["model"].predict(profile.model_dump())
    return result


@app.post("/explain", response_model=ExplainResponse)
def explain(request: ExplainRequest):
    """Full flow: predict the risk, then have the Gen AI layer explain it.
    This is the endpoint the app's UI would call to show a user their result."""
    profile_dict = request.profile.model_dump()

    # Step 1: get the risk from the ML model.
    prediction = resources["model"].predict(profile_dict)

    # Step 2: get a plain-language explanation of that risk from the LLM.
    explanation = generate_explanation(profile_dict, prediction)

    return {"prediction": prediction, "explanation": explanation}
