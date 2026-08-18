/**
 * Mappings for Diabetes Risk Classifier
 * Provides human-readable labels and structured option sets for form controls and top factor explanations.
 */

export const DIABETES_FIELD_OPTIONS = {
  GenHlth: [
    { value: 1, label: '1 — Excellent' },
    { value: 2, label: '2 — Very Good' },
    { value: 3, label: '3 — Good' },
    { value: 4, label: '4 — Fair' },
    { value: 5, label: '5 — Poor' }
  ],
  Age: [
    { value: 1, label: '18–24 years old' },
    { value: 2, label: '25–29 years old' },
    { value: 3, label: '30–34 years old' },
    { value: 4, label: '35–39 years old' },
    { value: 5, label: '40–44 years old' },
    { value: 6, label: '45–49 years old' },
    { value: 7, label: '50–54 years old' },
    { value: 8, label: '55–59 years old' },
    { value: 9, label: '60–64 years old' },
    { value: 10, label: '65–69 years old' },
    { value: 11, label: '70–74 years old' },
    { value: 12, label: '75–79 years old' },
    { value: 13, label: '80+ years old' }
  ],
  Sex: [
    { value: 0, label: 'Female' },
    { value: 1, label: 'Male' }
  ],
  YesNo: [
    { value: 0, label: 'No' },
    { value: 1, label: 'Yes' }
  ],
  YesNoInverted: [
    { value: 1, label: 'Yes' },
    { value: 0, label: 'No' }
  ]
};

export const DIABETES_FACTOR_LABELS = {
  GenHlth: 'General Health',
  HighBP: 'High Blood Pressure',
  BMI: 'Body Mass Index (BMI)',
  HighChol: 'High Cholesterol',
  Age: 'Age Band',
  DiffWalk: 'Difficulty Walking',
  PhysActivity: 'Physical Activity',
  Smoker: 'Smoking History',
  HeartDiseaseorAttack: 'Heart Condition / Attack',
  Fruits: 'Daily Fruit Intake',
  Veggies: 'Daily Vegetable Intake'
};
