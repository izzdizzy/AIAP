/**
 * Configuration schema for Diabetes Risk Classifier Form
 * Organizes fields into 2 structured steps: Patient Demographics & Baseline Metrics, Lifestyle & Clinical Conditions.
 */

import { DIABETES_FIELD_OPTIONS } from './diabetesMappings';

export const DIABETES_FEATURE_LABELS = {
  GenHlth: 'General Health Rating',
  BMI: 'Body Mass Index (BMI)',
  Age: 'Age Group',
  Sex: 'Biological Sex',
  HighBP: 'High Blood Pressure',
  HighChol: 'High Cholesterol',
  PhysActivity: 'Physical Activity',
  DiffWalk: 'Difficulty Walking/Stairs',
  Smoker: 'Smoking Status',
  HeartDiseaseorAttack: 'Heart Disease History',
  Fruits: 'Fruit Consumption',
  Veggies: 'Vegetable Consumption'
};

export const diabetesSteps = [
  { id: 'demographics', title: '1. Demographics & Metrics', description: 'General health, BMI, age group, and biological sex.' },
  { id: 'lifestyle', title: '2. Lifestyle & Medical History', description: 'Blood pressure, cholesterol, physical activity, and habits.' }
];

export const diabetesFieldGroups = [
  {
    id: 'demographics-group',
    title: 'Demographics & Metrics',
    fields: ['GenHlth', 'BMI', 'Age', 'Sex']
  },
  {
    id: 'lifestyle-group',
    title: 'Lifestyle & Conditions',
    fields: ['HighBP', 'HighChol', 'PhysActivity', 'DiffWalk', 'Smoker', 'HeartDiseaseorAttack', 'Fruits', 'Veggies']
  }
];

export const diabetesFields = {
  GenHlth: {
    name: 'GenHlth',
    label: 'General Health Rating',
    kind: 'select',
    inputType: 'select',
    required: true,
    helper: 'Patient self-reported or clinical general health scale.',
    options: DIABETES_FIELD_OPTIONS.GenHlth
  },
  BMI: {
    name: 'BMI',
    label: 'Body Mass Index (BMI)',
    kind: 'input',
    inputType: 'number',
    min: 10,
    max: 99,
    step: 0.1,
    required: true,
    helper: 'Weight (kg) / Height (m)².'
  },
  Age: {
    name: 'Age',
    label: 'Age Group',
    kind: 'select',
    inputType: 'select',
    required: true,
    helper: 'Age decade group bracket.',
    options: DIABETES_FIELD_OPTIONS.Age
  },
  Sex: {
    name: 'Sex',
    label: 'Biological Sex',
    kind: 'select',
    inputType: 'select',
    required: true,
    helper: 'Biological sex at birth.',
    options: DIABETES_FIELD_OPTIONS.Sex
  },
  HighBP: {
    name: 'HighBP',
    label: 'High Blood Pressure Diagnosis',
    kind: 'select',
    inputType: 'select',
    required: true,
    helper: 'Ever diagnosed with hypertension.',
    options: DIABETES_FIELD_OPTIONS.YesNo
  },
  HighChol: {
    name: 'HighChol',
    label: 'High Cholesterol Diagnosis',
    kind: 'select',
    inputType: 'select',
    required: true,
    helper: 'Ever diagnosed with hypercholesterolemia.',
    options: DIABETES_FIELD_OPTIONS.YesNo
  },
  PhysActivity: {
    name: 'PhysActivity',
    label: 'Regular Physical Activity',
    kind: 'select',
    inputType: 'select',
    required: true,
    helper: 'Physical activity or exercise in past 30 days.',
    options: DIABETES_FIELD_OPTIONS.YesNoInverted
  },
  DiffWalk: {
    name: 'DiffWalk',
    label: 'Difficulty Walking or Climbing Stairs',
    kind: 'select',
    inputType: 'select',
    required: true,
    helper: 'Serious difficulty walking or climbing stairs.',
    options: DIABETES_FIELD_OPTIONS.YesNo
  },
  Smoker: {
    name: 'Smoker',
    label: 'Lifetime Smoking History',
    kind: 'select',
    inputType: 'select',
    required: true,
    helper: 'Smoked at least 100 cigarettes in lifetime.',
    options: DIABETES_FIELD_OPTIONS.YesNo
  },
  HeartDiseaseorAttack: {
    name: 'HeartDiseaseorAttack',
    label: 'Coronary Heart Disease / Attack',
    kind: 'select',
    inputType: 'select',
    required: true,
    helper: 'History of myocardial infarction or angina.',
    options: DIABETES_FIELD_OPTIONS.YesNo
  },
  Fruits: {
    name: 'Fruits',
    label: 'Daily Fruit Consumption',
    kind: 'select',
    inputType: 'select',
    required: true,
    helper: 'Consumes fruit 1 or more times per day.',
    options: DIABETES_FIELD_OPTIONS.YesNoInverted
  },
  Veggies: {
    name: 'Veggies',
    label: 'Daily Vegetable Consumption',
    kind: 'select',
    inputType: 'select',
    required: true,
    helper: 'Consumes vegetables 1 or more times per day.',
    options: DIABETES_FIELD_OPTIONS.YesNoInverted
  }
};

export function validateDiabetesField(name, value) {
  const def = diabetesFields[name];
  if (!def) return '';

  if (def.required && (value === undefined || value === null || value === '')) {
    return `${def.label} is required.`;
  }

  if (def.inputType === 'number' && value !== '') {
    const num = Number(value);
    if (isNaN(num)) return `${def.label} must be a valid number.`;
    if (def.min !== undefined && num < def.min) return `${def.label} cannot be less than ${def.min}.`;
    if (def.max !== undefined && num > def.max) return `${def.label} cannot exceed ${def.max}.`;
  }

  return '';
}
