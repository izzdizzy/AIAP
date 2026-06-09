# Hospital Readmission Predictor for Chronic Condition Patients
## Ethical AI Healthcare Application for Singapore

### Project Overview
This project develops a machine learning model to predict 30-day hospital readmissions for patients with chronic conditions, adapted for the Singapore healthcare context. While using diabetes patient data as a proxy (due to its prevalence and well-documented nature), the framework is designed to generalize across multiple chronic conditions affecting Singapore's aging population.

### Singapore Healthcare Context
Singapore faces significant healthcare challenges:
- **Aging Population**: By 2030, 1 in 4 Singaporeans will be aged 65+
- **Chronic Disease Burden**: 11% of adults have diabetes; 40% have hypertension
- **MOH Health 2020 Goals**: Reduce avoidable hospital readmissions by 15%
- **Smart Nation Initiative**: Leverage AI for predictive healthcare analytics

**Impact on Singaporeans:**
- Early identification of high-risk chronic disease patients
- Reduced hospital burden and healthcare costs (~SGD $5,000-10,000 per prevented readmission)
- Improved patient care through proactive intervention
- Better resource allocation for public hospitals

### Dataset
UCI Diabetes 130-US Hospitals (1999-2008): https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008

*Note: This dataset serves as a proxy for chronic condition management. The clinical features (medications, lab procedures, length of stay, comorbidities) are representative of broader chronic disease patterns.*

### Setup
```bash
pip install -r requirements.txt
```

### Progress Review 1 Status
- [x] Data Collection & EDA
- [x] Supervised Model Training
- [x] Evaluation & Metrics
- [x] Code Documentation
- [ ] Gen AI Integration (Next Phase)

### Project Structure
```
├── src/                    # Modular Python packages
│   ├── data_loader.py      # Data loading utilities
│   ├── eda.py              # Exploratory Data Analysis
│   ├── preprocessing.py    # Data preprocessing pipeline
│   ├── model_training.py   # ML model training
│   └── evaluation.py       # Model evaluation metrics
├── notebooks/              # Jupyter notebook workflow
├── data/raw/               # Raw dataset
├── data/processed/         # Cleaned data
├── results/eda/            # EDA visualizations
├── results/evaluation/     # Evaluation outputs
├── models/                 # Saved models
└── docs/                   # Documentation
```

### Team Progress Update
**Completed:**
- Comprehensive data collection with Singapore healthcare context documentation
- 12+ EDA visualizations revealing chronic disease readmission patterns
- Full preprocessing pipeline with SMOTE for class imbalance
- 6 ML algorithms with hyperparameter tuning and cross-validation
- In-depth evaluation with healthcare-specific metric interpretation

**Next Steps:**
- Integrate Gen AI for explainable predictions
- Develop patient risk stratification dashboard
- Validate with Singapore hospital data (future collaboration)

