display_cols = {
    "age": "Age",
    "sex": "Sex",
    "trestbps": "Resting Blood Pressure",
    "chol": "Cholesterol",
    "fbs": "Fasting Blood Sugar",
    "thalach": "Maximum Heart Rate",
    "exang": "Exercise-Induced Angina",
    "oldpeak": "ST Depression",
    "slope": "ST Segment Slope",
    "ca": "Number of Major Vessels",
    "thal": "Thalassemia"
}

# Reverse the one-hot encoding
cp_labels = {
    1: "Typical Angina",
    2: "Atypical Angina",
    3: "Non-anginal Pain",
    4: "Asymptomatic"
}

restecg_labels = {
    0: "Normal",
    1: "ST-T Wave Abnormality",
    2: "Left Ventricular Hypertrophy"
}


def safe_category_label(value, label_map):
    if value is None:
        return None

    try:
        return label_map[int(value)]
    except (TypeError, ValueError, KeyError):
        return None


# Convert raw prediction into output JSON
def format_prediction(raw_result, patient, top_n=5, min_impact=0.10):

    raw_shap = raw_result["shap_values"]

    combined = {}

    # Standard features
    for feature, display_name in display_cols.items():
        combined[display_name] = float(raw_shap.get(feature, 0))

    # Combine Chest Pain one-hot features
    cp_value = (raw_shap.get("cp_2.0", 0) + raw_shap.get("cp_3.0", 0) + raw_shap.get("cp_4.0", 0))
    cp_label = safe_category_label(patient.get("cp"), cp_labels)

    if cp_label is not None:
        combined[
            f"Chest Pain ({cp_label})"
            ] = float(cp_value)

    # Combine Rest ECG one-hot features
    ecg_value = (raw_shap.get("restecg_1.0", 0) + raw_shap.get("restecg_2.0", 0))
    ecg_label = safe_category_label(patient.get("restecg"), restecg_labels)

    if ecg_label is not None:
        combined[
            f"Resting ECG ({ecg_label})"
        ] = float(ecg_value)

    # Sort by absolute impact
    factors = sorted(
        combined.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )

    # Remove tiny contributors
    factors = [
        {
            "feature": feature,
            "impact": round(value, 3),
            "direction": "increase" if value > 0 else "decrease"
        }
        for feature, value in factors
        if abs(value) >= min_impact
    ]

    # Limit displayed factors
    factors = factors[:top_n]

    return {
        "prediction": raw_result["prediction"],
        "risk_probability": raw_result["risk_probability"],
        "risk_percent": raw_result["risk_percent"],
        "top_factors": factors
    }
