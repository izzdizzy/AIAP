"""
Request and response shapes for the Diabetes Risk Classifier API.

Using Pydantic models means FastAPI automatically validates incoming data
(e.g. rejects a request where BMI is text instead of a number) and documents
every field on the interactive /docs page. Each field has a description and a
sensible range so the API is self-explaining.
"""

from pydantic import BaseModel, Field


class HealthProfile(BaseModel):
    """One person's health/lifestyle answers. Field order does not matter here;
    the model layer re-orders them to match what the classifier expects."""

    HighBP: int = Field(..., ge=0, le=1, description="High blood pressure (0=no, 1=yes)")
    HighChol: int = Field(..., ge=0, le=1, description="High cholesterol (0=no, 1=yes)")
    CholCheck: int = Field(..., ge=0, le=1, description="Cholesterol check in last 5 years (0/1)")
    BMI: float = Field(..., ge=10, le=100, description="Body Mass Index")
    Smoker: int = Field(..., ge=0, le=1, description="Smoked 100+ cigarettes in life (0/1)")
    Stroke: int = Field(..., ge=0, le=1, description="Ever had a stroke (0/1)")
    HeartDiseaseorAttack: int = Field(..., ge=0, le=1, description="Heart disease or attack (0/1)")
    PhysActivity: int = Field(..., ge=0, le=1, description="Physical activity in past 30 days (0/1)")
    Fruits: int = Field(..., ge=0, le=1, description="Eats fruit 1+ times/day (0/1)")
    Veggies: int = Field(..., ge=0, le=1, description="Eats vegetables 1+ times/day (0/1)")
    HvyAlcoholConsump: int = Field(..., ge=0, le=1, description="Heavy alcohol consumption (0/1)")
    AnyHealthcare: int = Field(..., ge=0, le=1, description="Has any health coverage (0/1)")
    NoDocbcCost: int = Field(..., ge=0, le=1, description="Could not see doctor due to cost (0/1)")
    GenHlth: int = Field(..., ge=1, le=5, description="Self-rated general health (1=excellent .. 5=poor)")
    MentHlth: int = Field(..., ge=0, le=30, description="Days mental health not good (0-30)")
    PhysHlth: int = Field(..., ge=0, le=30, description="Days physical health not good (0-30)")
    DiffWalk: int = Field(..., ge=0, le=1, description="Difficulty walking/climbing stairs (0/1)")
    Sex: int = Field(..., ge=0, le=1, description="0=female, 1=male")
    Age: int = Field(..., ge=1, le=13, description="Age band (1=18-24 .. 13=80+)")
    Education: int = Field(..., ge=1, le=6, description="Education level (1-6)")
    Income: int = Field(..., ge=1, le=8, description="Income band (1-8)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "HighBP": 1, "HighChol": 1, "CholCheck": 1, "BMI": 34.0,
                "Smoker": 1, "Stroke": 0, "HeartDiseaseorAttack": 0,
                "PhysActivity": 0, "Fruits": 0, "Veggies": 1,
                "HvyAlcoholConsump": 0, "AnyHealthcare": 1, "NoDocbcCost": 0,
                "GenHlth": 4, "MentHlth": 5, "PhysHlth": 10, "DiffWalk": 1,
                "Sex": 1, "Age": 9, "Education": 4, "Income": 3,
            }
        }
    }


class PredictionResponse(BaseModel):
    """What /predict returns."""
    risk_label: str = Field(..., description="'At risk' or 'Not at risk'")
    risk_probability: float = Field(..., description="Model probability of being at risk (0-1)")
    risk_band: str = Field(..., description="Low / Moderate / High, derived from the probability")
    top_factors: list[str] = Field(..., description="The person's own values on the biggest risk-driving features")


class ExplainRequest(BaseModel):
    """Input to /explain: the person's profile (so the LLM can reference their
    actual values) plus the option to reuse an already-computed prediction."""
    profile: HealthProfile


class ExplainResponse(BaseModel):
    prediction: PredictionResponse
    explanation: str = Field(..., description="Plain-language explanation from the Gen AI layer")
