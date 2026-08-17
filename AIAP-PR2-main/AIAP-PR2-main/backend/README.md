# Chronic Disease Risk Monitor - Backend (Diabetes)

FastAPI backend for the diabetes part of the Personal Chronic Disease Risk Monitor.
It serves two capabilities:

1. **Diabetes risk classifier** (supervised ML) - predicts diabetes risk from a health profile.
2. **Personalised Risk Explainer** (Gen AI) - explains that risk in plain language via an LLM.

## Files

| File | What it does |
|------|--------------|
| `main.py` | The FastAPI app and the three endpoints. Loads the model at startup. |
| `model_service.py` | Loads the trained Random Forest and turns a profile into a prediction. |
| `genai_service.py` | The Gen AI explainer: builds a prompt and calls the LLM (with a no-key fallback). |
| `schemas.py` | Pydantic models that validate the input and shape the output. |
| `model_artifacts/` | The saved model (`.pkl`) and its feature metadata, produced from the notebook. |
| `frontend/index.html` | The web UI. Open in a browser; it calls the backend and shows the risk gauge + explanation. |
| `save_model.py` | Trains and saves the model file (the bridge from notebook to backend). |
| `requirements.txt` | Python dependencies. |
| `.env.example` | Template for the LLM API key settings. |

## Running the whole thing (backend + UI)

1. Start the backend: `uvicorn main:app --reload`
2. Open `frontend/index.html` in your browser (double-click it, or right-click → open).
3. The badge top-right shows "Backend connected" when it reaches the API. Fill the
   form (or click "Fill sample profile") and press "Assess my risk".

The UI has a built-in demo mode: if the backend isn't running it still works using a
local fallback, so a live demo never breaks. When the backend IS running, it uses the
real trained model and the real Gen AI explanation.

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) set your LLM key for real explanations
#    Copy .env.example to .env and fill in LLM_API_KEY,
#    OR run with LLM_PROVIDER=none to use the built-in template.
```

## Run

```bash
uvicorn main:app --reload
```

Then open **http://127.0.0.1:8000/docs** - an interactive page where you can
try every endpoint from the browser (great for the live demo).

## Endpoints

- `GET /health` - is the API up and the model loaded?
- `POST /predict` - health profile in, risk prediction out.
- `POST /explain` - health profile in, risk + plain-language explanation out.

### Example (predict)

Request body:
```json
{ "HighBP": 1, "HighChol": 1, "CholCheck": 1, "BMI": 34.0, "Smoker": 1,
  "Stroke": 0, "HeartDiseaseorAttack": 0, "PhysActivity": 0, "Fruits": 0,
  "Veggies": 1, "HvyAlcoholConsump": 0, "AnyHealthcare": 1, "NoDocbcCost": 0,
  "GenHlth": 4, "MentHlth": 5, "PhysHlth": 10, "DiffWalk": 1, "Sex": 1,
  "Age": 9, "Education": 4, "Income": 3 }
```

Response:
```json
{ "risk_label": "At risk", "risk_probability": 0.864, "risk_band": "High",
  "top_factors": ["GenHlth = 4", "HighBP = 1", "BMI = 34.0", "HighChol = 1", "Age = 9"] }
```

## How it fits together

```
health profile ->  /predict  -> Random Forest model  -> risk score
                       |
                       v
                   /explain   -> risk score + profile -> LLM -> plain-language advice
```

The LLM only *explains* the model's output; the risk number always comes from
the trained classifier, not the language model.

## Regenerating the model file

The model file in `model_artifacts/` was produced by training the notebook's
Random Forest and saving it with `joblib.dump`. To regenerate it, run the
`save_model.py` step described in the notebook (train, then dump to
`model_artifacts/diabetes_rf_model.pkl` and write the two JSON files).
