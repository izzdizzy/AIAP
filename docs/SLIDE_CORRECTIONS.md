# SLIDE CORRECTIONS FOR CANVA
## Progress Review 1 - Hospital Readmission Predictor

### CRITICAL CORRECTIONS REQUIRED

---

## SLIDE 1: "ML: Hospital Readmission Predictor"

### CURRENT TEXT (INCORRECT):
```
Inputs: Prior admissions, comorbidity count, BMI, HbA1c, systolic BP, medication count, age, discharge diagnosis
```

### CORRECTED TEXT (USE THIS):
```
Inputs: 
• Admission history (prior inpatient, outpatient, emergency visits)
• Comorbidity indicator (number of diagnoses)
• Glycemic control (HbA1c test results - categorical)
• Medication count (number of unique medications)
• Age groups (categorical ranges)
• Primary/secondary diagnosis codes (ICD-9)
• Hospital length of stay
• Lab procedures count

Note: Analysis uses clinical indicators available in UCI dataset that are 
representative of chronic condition management patterns.
```

### ADDITIONAL CLARIFICATIONS:
- Keep: "Binary classifier | Scikit-learn | Tabular features"
- Keep: "Predicts whether a chronic-condition patient will be readmitted to hospital within 30 days of discharge"
- Keep: "Primary metric: Recall — minimise missed high-risk cases; AUC-ROC as secondary"
- Keep: "Models compared: Logistic regression (baseline), Random Forest, XGBoost (final)"

### FOR "Explainability" SECTION - ADD:
```
Explainability: 
• Feature importance analysis (XGBoost built-in)
• SHAP (SHapley Additive exPlanations) summary plots
• SHAP waterfall plots for individual predictions
• Clinical interpretation of top risk factors
```

---

## SLIDE 2: "Gen AI: Care Navigation Assistant"

### CURRENT TEXT (INCORRECT - COPIED FROM SLIDE 1):
```
Description: Predicts whether a chronic-condition patient will be readmitted to hospital within 30 days of discharge.
```

### CORRECTED TEXT (USE THIS):
```
Title: Gen AI: Care Navigation Assistant
Tags: LLM-powered | System-prompted | Singapore Healthcare KB

Description: 
Provides personalized care navigation recommendations for chronic condition patients 
based on ML-predicted readmission risk. Translates risk scores into actionable 
healthcare guidance aligned with Singapore's healthcare system.

Inputs: 
• Readmission risk score (0-1) from ML model
• Patient age group and chronic condition profile
• CHAS subsidy tier (Blue/Orange/Green/Merdeka/Pioneer)
• Preferred care provider type (GP/Polyclinic/Specialist)

Knowledge Base: 
• CHAS tiers & subsidy schemes
• Healthier SG enrolment process
• Polyclinic vs GP vs specialist routing rules
• MediSave/MediShield Life/MediFund (MAF) basics
• 24-hr health hotlines (HealthHub: 1800-2255-533)

Output: 
• Triage recommendation (urgency level)
• Personalized next steps in plain English
• Relevant healthcare resources & contacts
• Follow-up scheduling guidance
```

---

## KEY POINTS TO EMPHASIZE IN PRESENTATION:

1. **Dataset Transparency**: "We use UCI Diabetes dataset as a proxy for chronic conditions. 
   While BMI and blood pressure aren't available, we leverage 50 clinical features including 
   admission history, medication patterns, lab procedures, and diagnosis codes."

2. **Singapore Context**: "Features map to Singapore healthcare realities:
   - Prior admissions → Tracks healthcare utilization patterns
   - Number of diagnoses → Comorbidity burden indicator
   - Medication count → Polypharmacy risk marker
   - Length of stay → Disease severity proxy"

3. **Clinical Relevance**: "Recall is our primary metric because missing a high-risk patient 
   could lead to emergency readmission, increased costs (~SGD $5-10K), and worse outcomes."

4. **Gen AI Integration**: "The Care Navigation Assistant bridges ML predictions with 
   actionable healthcare guidance, making AI outputs accessible to patients and caregivers."

---

## DOCUMENTATION NOTES:

- All code now uses "chronic condition" framing, not just "diabetes"
- Features are documented as chronic disease indicators
- Ethics section covers bias, privacy, elderly vulnerability
- Singapore healthcare context integrated throughout
