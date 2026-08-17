MODEL_INPUT_FIELDS = [
    'age',
    'sex',
    'cp',
    'trestbps',
    'chol',
    'fbs',
    'restecg',
    'thalach',
    'exang',
    'oldpeak',
    'slope',
    'ca',
    'thal'
]

DISPLAY_NAMES = {
    'age': 'Age',
    'sex': 'Sex',
    'cp': 'Chest Pain Type',
    'trestbps': 'Resting Blood Pressure',
    'chol': 'Cholesterol',
    'fbs': 'Fasting Blood Sugar',
    'restecg': 'Rest ECG',
    'thalach': 'Maximum Heart Rate',
    'exang': 'Exercise Induced Angina',
    'oldpeak': 'ST Depression (Oldpeak)',
    'slope': 'ST Slope',
    'ca': 'Number of Major Vessels',
    'thal': 'Thalassemia'
}

RISK_LEVELS = (
    ('Low', 0.3),
    ('Moderate', 0.6),
    ('High', 1.0)
)

MEDICAL_DISCLAIMER = (
    'This result is a screening aid for educational use only. It does not diagnose coronary artery disease, and it should not replace professional medical advice or urgent assessment.'
)

LIFESTYLE_ADVICE = {
    'Low': [
        'Keep a regular activity routine and continue routine health screening.',
        'Track blood pressure, cholesterol, and symptom changes over time.',
        'Use this result as a screening indicator rather than a diagnosis.'
    ],
    'Moderate': [
        'Discuss the result with a clinician when you next have access to care.',
        'Focus on diet quality, walking, and consistent sleep habits.',
        'Watch for worsening chest discomfort, breathlessness, or fatigue.'
    ],
    'High': [
        'Arrange clinical review promptly, especially if symptoms persist or worsen.',
        'Avoid strenuous exertion until a clinician confirms it is safe.',
        'Record symptoms, triggers, and medications so they can be reviewed later.'
    ]
}
