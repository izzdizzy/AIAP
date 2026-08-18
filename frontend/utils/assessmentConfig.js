export const sexOptions = [
  { label: 'Female', value: 0 },
  { label: 'Male', value: 1 }
];

export const yesNoOptions = [
  { label: 'No', value: 0 },
  { label: 'Yes', value: 1 }
];

// Chest pain triage questions for clinical assessment
export const chestPainTriageQuestions = [
  { id: 'center-location', label: 'Is the pain located in the center of your chest?', required: true, options: yesNoOptions },
  { id: 'exercise-trigger', label: 'Is it brought on by physical exercise or emotional stress?', required: true, options: yesNoOptions },
  { id: 'rest-relief', label: 'Does it go away within 5 to 15 minutes when you rest?', required: true, options: yesNoOptions }
];

// Map triage answers to CAD dataset values (1-4)
export const chestPainTriageToValue = {
  'no-no-yes': 3,   // Non-anginal pain
  'no-yes-yes': 2,  // Atypical angina
  'yes-no-yes': 2,  // Atypical angina
  'yes-yes-yes': 1, // Typical angina
  default: 4        // Asymptomatic (fallback)
};


export const restingEcgOptions = [
  { label: 'Normal', value: 0 },
  { label: 'ST-T wave abnormality', value: 1 },
  { label: 'Left ventricular hypertrophy', value: 2 }
];

export const slopeOptions = [
  { label: 'Upsloping', value: 1 },
  { label: 'Flat', value: 2 },
  { label: 'Downsloping', value: 3 }
];

export const thalOptions = [
  { label: 'Normal', value: 3 },
  { label: 'Fixed defect', value: 6 },
  { label: 'Reversible defect', value: 7 }
];

export const caOptions = [
  { label: '0 major vessels', value: 0 },
  { label: '1 major vessel', value: 1 },
  { label: '2 major vessels', value: 2 },
  { label: '3 major vessels', value: 3 },
  { label: '4 major vessels', value: 4 }
];

export const assessmentFields = {
  age: {
    name: 'age',
    label: 'Age',
    kind: 'number',
    inputType: 'number',
    required: true,
    min: 18,
    max: 128,
    step: 1,
    helper: '(in years)'
  },
  sex: {
    name: 'sex',
    label: 'Biological Sex',
    kind: 'select',
    required: true,
    options: sexOptions,
    helper: '(Biological sex at birth)'
  },
  cpAssessment: {
    name: 'cpAssessment',
    label: 'Chest pain assessment',
    kind: 'select',
    inputType: 'radio',
    required: true,
    options: [
      {
        label: 'I am currently experiencing chest pain',
        value: 'guided'
      },
      {
        label: 'I am NOT experiencing chest pain',
        value: 'none'
      },
      {
        label: 'I already know my chest pain classification (Advanced)',
        value: 'manual'
      }
    ]
  },

  cpManual: {
    name: 'cpManual',
    label: 'Chest pain classification',
    kind: 'select',
    required: true,
    options: [
      { label: 'Typical angina', value: 1 },
      { label: 'Atypical angina', value: 2 },
      { label: 'Non-anginal pain', value: 3 },
      { label: 'No chest pain', value: 4 }
    ]
  },
  cp: {
    name: 'cp',
    label: 'Chest pain type',
    kind: 'triage',
    required: true,
    inputType: 'radio',
    options: chestPainTriageQuestions,
    helper: 'Answer all three questions below to determine your chest pain category.'
  },
  trestbps: {
    name: 'trestbps',
    label: 'Resting blood pressure',
    kind: 'number',
    inputType: 'number',
    required: false,
    min: 50,
    max: 250,
    step: 1,
    helper: '(mmHg, from recent blood test if available)'
  },
  chol: {
    name: 'chol',
    label: 'Cholesterol',
    kind: 'number',
    inputType: 'number',
    required: false,
    min: 100,
    max: 700,
    step: 1,
    helper: '(mg/dL, from recent blood test if available)'
  },
  fbs: {
    name: 'fbs',
    label: 'High fasting blood sugar',
    kind: 'select',
    required: false,
    options: yesNoOptions,
    helper: '(Yes if ≥120 mg/dL, no otherwise)'
  },
  restecg: {
    name: 'restecg',
    label: 'Resting ECG',
    kind: 'select',
    required: false,
    optionalLabel: 'Not sure / not available',
    options: restingEcgOptions,
    helper: '(from recent ECG test if available)'
  },
  thalach: {
    name: 'thalach',
    label: 'Highest heart rate during exercise',
    kind: 'number',
    inputType: 'number',
    required: false,
    min: 60,
    max: 250,
    step: 1,
    helper: '(bpm, from exercise test if available)'
  },
  exang: {
    name: 'exang',
    label: 'Chest pain during exercise',
    kind: 'select',
    required: true,
    options: yesNoOptions,
    helper: 'Pain, pressure, or tightness that comes on with exercise'
  },
  oldpeak: {
    name: 'oldpeak',
    label: 'ST depression (oldpeak)',
    kind: 'number',
    inputType: 'number',
    required: false,
    min: 0,
    max: 10,
    step: 0.1,
    helper: '(mm, from exercise ECG report if available)'
  },
  slope: {
    name: 'slope',
    label: 'ST Slope',
    kind: 'select',
    required: false,
    optionalLabel: 'Not sure / not available',
    options: slopeOptions,
    helper: '(from exercise ECG report if available)'
  },
  ca: {
    name: 'ca',
    label: 'Number of Major Vessels',
    kind: 'select',
    required: false,
    optionalLabel: 'Not sure / not available',
    options: caOptions,
    helper: '(from clinic report if available)'
  },
  thal: {
    name: 'thal',
    label: 'Thalassemia',
    kind: 'select',
    required: false,
    optionalLabel: 'Not sure / not available',
    options: thalOptions,
    helper: '(from clinic report if available)'
  }
};

export const assessmentFieldGroups = [
  {
    id: 'personalInformation',
    title: 'Personal Information',
    description: 'Basic patient context used by the trained model.',
    fields: ['age', 'sex']
  },
  {
    id: 'symptoms',
    title: 'Symptoms',
    description: 'Reported chest pain and exercise response.',
    fields: [
      'cpAssessment',
      'cpManual',
      'cp',
      'exang']
  },
  {
    id: 'clinical-measurements',
    title: 'Clinical Measurements',
    description: 'Vital signs and core lab measurements.',
    fields: ['trestbps', 'chol', 'thalach', 'fbs']
  },
  {
    id: 'ecg-clinical-findings',
    title: 'ECG / Clinical Findings',
    description: 'Cardiac indicators and imaging-derived findings.',
    fields: ['restecg', 'oldpeak', 'slope', 'ca', 'thal']
  }
];

export const assessmentSteps = [
  {
    id: 'personalInformation',
    title: '1. Personal Info',
    description: 'Basic patient context used by the trained model.'
  },
  {
    id: 'symptoms',
    title: '2. Symptoms',
    description: 'Reported chest pain and exercise response.'
  },
  {
    id: 'measurements',
    title: '3. Measurements',
    description: 'Vital signs and core lab measurements.'
  },
  {
    id: 'clinicDetails',
    title: '4. Clinic Details',
    description: 'Optional report-only details.'
  },
  {
    id: 'review',
    title: '5. Review',
    description: 'Check what you answered before submitting.'
  }
];

export const stepFieldMap = {
  personalInformation: ['age', 'sex'],
  symptoms: [
    'cpAssessment',
    'cpManual',
    'cp',
    'exang'
  ],
  measurements: ['trestbps', 'chol', 'fbs', 'thalach'],
  clinicDetails: ['restecg', 'oldpeak', 'slope', 'ca', 'thal']
};

export const fieldOrder = [
  'age',
  'sex',
  'cp',
  'exang',
  'trestbps',
  'chol',
  'fbs',
  'restecg',
  'thalach',
  'oldpeak',
  'slope',
  'ca',
  'thal'
];

export function createInitialAssessmentValues() {
  return fieldOrder.reduce((accumulator, fieldName) => {
    accumulator[fieldName] = '';
    return accumulator;
  }, {});
}

export function getFieldDefinition(fieldName) {
  return assessmentFields[fieldName];
}

export function validateAssessmentValue(fieldName, value) {
  const field = getFieldDefinition(fieldName);

  if (!field) {
    return '';
  }

  if (value === '' || value === null || value === undefined) {
    if (!field.required) {
      return '';
    }
    return `${field.label} is required.`;
  }

  if (field.kind === 'select') {
    const optionValues = field.options.map((option) => String(option.value));
    if (!optionValues.includes(String(value))) {
      return `Select a valid ${field.label.toLowerCase()} option.`;
    }
    return '';
  }

  const numericValue = Number(value);
  if (Number.isNaN(numericValue)) {
    return `${field.label} must be a number.`;
  }

  if (typeof field.min === 'number' && numericValue < field.min) {
    return `${field.label} must be at least ${field.min}.`;
  }

  if (typeof field.max === 'number' && numericValue > field.max) {
    return `${field.label} must be ${field.max} or less.`;
  }

  return '';
}
