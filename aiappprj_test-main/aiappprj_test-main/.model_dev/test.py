from predict import predict
from formatter import format_prediction, pretty_print

patient = {
    'age': 69.0,
    'sex': 1.0,
    'cp': 4.0,
    'trestbps': 150.0,
    'chol': 260.0,
    'fbs': 0.0,
    'restecg': 1.0,
    'thalach': 120.0,
    'exang': 1.0,
    'oldpeak': 2.3,
    'slope': 2.0,
    'ca': 2.0,
    'thal': 7.0
}

# 2	65.0	1.0	4.0	155	0	?	0	154	0	1	1	?	?	0
raw = predict(patient)
print('Raw', raw['raw_probability'])
formatted = format_prediction(raw, patient)

pretty_print(formatted)