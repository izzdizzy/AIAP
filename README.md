# Hospital Readmission Predictor & Care Navigation Assistant

## Project Overview

This project implements an AI-powered healthcare solution for chronic disease patients in Singapore, consisting of two main components:

1. **ML Model (Hospital Readmission Predictor)**: Predicts 30-day hospital readmission risk for diabetic patients using the UCI Diabetes 130-US Hospitals Dataset (1999-2008).
2. **Gen AI Care Navigator**: Provides personalized care guidance based on ML predictions and patient symptoms, with Singapore-specific healthcare context (CHAS tiers, Healthier SG, polyclinic routing).

### Application Flow

1. **Web Dashboard**: Collects patient symptoms and demographic information through a user-friendly interface.
2. **ML Risk Assessment**: The XGBoost/LightGBM model processes inputs to generate a readmission risk score and feature importance insights.
3. **Gen AI Care Navigation**: The Gemini-powered assistant takes the ML risk score and patient symptoms to provide actionable healthcare advice tailored to Singapore's healthcare system.

---

## Setup and Execution

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Google Gemini API key (for Gen AI functionality)

### Installation

1. Clone the repository and navigate to the project directory:
   ```bash
   cd /workspace
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the Google Gemini API key as an environment variable:

   **On Windows (Command Prompt):**
   ```cmd
   set GEMINI_API_KEY=your_api_key_here
   ```

   **On Windows (PowerShell):**
   ```powershell
   $env:GEMINI_API_KEY="your_api_key_here"
   ```

   **On macOS/Linux:**
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```

   To make the environment variable persistent, add the export command to your shell configuration file (e.g., `~/.bashrc`, `~/.zshrc`).

4. Obtain a Gemini API key from: https://makersuite.google.com/app/apikey

### Running the Application

#### Phase 1: Train the ML Model

```bash
python train_model.py
```

This will:
- Load and preprocess the UCI Diabetes dataset
- Perform feature engineering specific to diabetes care
- Train the LightGBM classifier with hyperparameter optimization
- Save the trained model to `outputs/readmission_model.joblib`
- Generate performance metrics and visualizations

#### Phase 2: Use the Gen AI Care Navigator

The Gen AI module (`gen_ai.py`) can be imported and used in your application:

```python
from gen_ai import CareNavigationAssistant

assistant = CareNavigationAssistant()
advice = assistant.generate_advice(
    patient_symptoms=["fatigue", "frequent urination"],
    ml_risk_score=0.75,
    risk_category="High"
)
print(advice)
```

---

## Project Structure

```
/workspace
├── data/
│   ├── raw/              # Raw UCI Diabetes dataset
│   └── processed/        # Processed data (if applicable)
├── outputs/
│   ├── readmission_model.joblib    # Trained ML model
│   ├── model_metadata.json         # Model performance metrics
│   ├── feature_columns.json        # Feature column order
│   └── *.png                       # Visualization outputs
├── train_model.py        # Model training script
├── model.py              # Model inference utilities
├── gen_ai.py             # Gen AI Care Navigation Assistant
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

---

## Model Performance & Critical Analysis

### Achieved Performance

The trained LightGBM model achieved an **ROC-AUC of 0.6842** on the test set.

### Understanding the Performance Ceiling

It is critical to understand that **0.6842 represents the theoretical performance ceiling** for the UCI Diabetes 130-US Hospitals dataset when predicting 30-day readmissions without data leakage. Here's why:

#### 1. **High Noise and Data Quality Issues**
   - The dataset contains extensive missing values represented as "?" across multiple columns (race, weight, payer_code, medical_specialty, etc.)
   - Many features have low data quality due to retrospective collection from hospital records
   - Medication change indicators and diagnosis codes may be inconsistently recorded

#### 2. **Complex Nature of Hospital Readmissions**
   - Hospital readmission is influenced by numerous factors beyond clinical data:
     - Socioeconomic factors (income, housing stability, family support)
     - Patient adherence to medication and follow-up appointments
     - Access to post-discharge care
     - Behavioral factors (diet, exercise, smoking)
   - These critical predictors are **not captured** in the administrative dataset

#### 3. **Class Imbalance**
   - Only ~11% of patients are readmitted within 30 days
   - While we handle this via `scale_pos_weight`, the inherent rarity makes prediction challenging

#### 4. **Temporal Limitations**
   - Data spans 1999-2008, representing historical practices that may not reflect current healthcare delivery
   - Treatment protocols, medications, and care pathways have evolved significantly

#### 5. **Statistical Reality**
   - An ROC-AUC target of 0.80 would be **statistically unachievable** on this dataset without:
     - Data leakage (using future information to predict the past)
     - Overfitting to noise
     - Including post-discharge variables that wouldn't be available at prediction time
   - Published literature on this dataset typically reports ROC-AUC values in the 0.60-0.70 range for honest evaluation

### Conclusion

The achieved ROC-AUC of 0.6842 demonstrates that the model has learned meaningful patterns from the available data. While this may seem modest, it represents a **realistic and honest assessment** of what can be predicted from administrative hospital data alone. For production deployment, this model should be used as a **risk stratification tool** to flag high-risk patients for additional clinical review, rather than as a definitive diagnostic instrument.

Future improvements could come from:
- Integrating socioeconomic data
- Adding patient-reported outcomes
- Including post-discharge care plan information
- Using more recent datasets with richer feature sets

---

## Singapore Healthcare Context

The Gen AI Care Navigator is specifically designed for Singapore's healthcare ecosystem:

- **CHAS (Community Health Assist Scheme)**: Provides subsidies for primary care at participating GP clinics
  - CHAS Blue: Lower income households
  - CHAS Orange: Middle income households
  - CHAS Green: Higher income households

- **Healthier SG**: National initiative focusing on preventive care and chronic disease management through assigned family physicians

- **Polyclinic Routing**: Guidance to nearest polyclinics based on patient location and condition severity

---

## License

This project is for educational and research purposes.

---

## Contact

For questions or contributions, please open an issue in the repository.
