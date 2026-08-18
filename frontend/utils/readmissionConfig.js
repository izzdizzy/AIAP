/**
 * Configuration schema for Hospital Readmission Risk Assessment Form
 * Organizes fields into 3 structured steps: Patient Demographics, Hospitalization & Admission, Clinical & Medication Metrics.
 */

export const readmissionSteps = [
  { id: 'intro', title: 'File Import & Overview', description: 'Upload patient CSV/XLSX record or complete inputs manually.' },
  { id: 'demographics', title: '1. Patient Profile', description: 'Age group, subsidies, and current symptoms.' },
  { id: 'hospitalization', title: '2. Admission Details', description: 'Inpatient stay duration, visit counts, and admission classification.' },
  { id: 'clinical', title: '3. Clinical Metrics', description: 'Comorbidities, lab procedures, diagnoses, and medication flags.' }
];

export const readmissionFieldGroups = [
  {
    id: 'demographics-group',
    title: 'Patient Profile',
    fields: ['age', 'chas_tier', 'prior_admissions']
  },
  {
    id: 'hospitalization-group',
    title: 'Admission Details',
    fields: ['time_in_hospital', 'number_inpatient', 'number_emergency', 'number_outpatient']
  },
  {
    id: 'clinical-group',
    title: 'Clinical Metrics',
    fields: ['comorbidity_count', 'number_diagnoses', 'num_lab_procedures', 'num_medications']
  }
];

export const readmissionFields = {
  age: {
    name: 'age',
    label: 'Age Group',
    kind: 'select',
    inputType: 'select',
    required: true,
    helper: 'Select patient age decade range.',
    options: [
      { value: '0-10', label: '0–10 years old' },
      { value: '10-20', label: '10–20 years old' },
      { value: '20-30', label: '20–30 years old' },
      { value: '30-40', label: '30–40 years old' },
      { value: '40-50', label: '40–50 years old' },
      { value: '50-60', label: '50–60 years old' },
      { value: '60-70', label: '60–70 years old' },
      { value: '70-80', label: '70–80 years old' },
      { value: '80-90', label: '80–90 years old' },
      { value: '90-100', label: '90–100 years old' }
    ]
  },
  chas_tier: {
    name: 'chas_tier',
    label: 'CHAS / Healthcare Subsidy Tier',
    kind: 'select',
    inputType: 'select',
    required: false,
    helper: 'Patient CHAS tier status.',
    options: [
      { value: 'Blue', label: 'Blue Tier' },
      { value: 'Orange', label: 'Orange Tier' },
      { value: 'Pioneer', label: 'Pioneer Generation' },
      { value: 'Merdeka', label: 'Merdeka Generation' },
      { value: 'None', label: 'None / Standard' }
    ]
  },
  prior_admissions: {
    name: 'prior_admissions',
    label: 'Prior Inpatient Admissions (Past 1 Year)',
    kind: 'input',
    inputType: 'number',
    min: 0,
    max: 50,
    required: true,
    helper: 'Number of inpatient stays in the past 12 months.'
  },
  time_in_hospital: {
    name: 'time_in_hospital',
    label: 'Hospital Stay Duration (Days)',
    kind: 'input',
    inputType: 'number',
    min: 1,
    max: 14,
    required: true,
    helper: 'Total days spent in inpatient care.'
  },
  number_inpatient: {
    name: 'number_inpatient',
    label: 'Inpatient Visits Count',
    kind: 'input',
    inputType: 'number',
    min: 0,
    max: 30,
    required: false,
    helper: 'Number of inpatient visits in the prior year.'
  },
  number_emergency: {
    name: 'number_emergency',
    label: 'Emergency Room Visits Count',
    kind: 'input',
    inputType: 'number',
    min: 0,
    max: 30,
    required: false,
    helper: 'Number of emergency visits in prior year.'
  },
  number_outpatient: {
    name: 'number_outpatient',
    label: 'Outpatient Clinic Visits Count',
    kind: 'input',
    inputType: 'number',
    min: 0,
    max: 50,
    required: false,
    helper: 'Number of outpatient clinic visits in prior year.'
  },
  comorbidity_count: {
    name: 'comorbidity_count',
    label: 'Comorbidity Count',
    kind: 'input',
    inputType: 'number',
    min: 0,
    max: 20,
    required: true,
    helper: 'Total active diagnosed co-existing conditions.'
  },
  number_diagnoses: {
    name: 'number_diagnoses',
    label: 'Number of Diagnoses Entered',
    kind: 'input',
    inputType: 'number',
    min: 1,
    max: 16,
    required: true,
    helper: 'Diagnoses logged during hospital encounter.'
  },
  num_lab_procedures: {
    name: 'num_lab_procedures',
    label: 'Number of Lab Procedures',
    kind: 'input',
    inputType: 'number',
    min: 1,
    max: 130,
    required: true,
    helper: 'Total laboratory diagnostic tests performed.'
  },
  num_medications: {
    name: 'num_medications',
    label: 'Distinct Medications Prescribed',
    kind: 'input',
    inputType: 'number',
    min: 1,
    max: 80,
    required: true,
    helper: 'Number of distinct medications during encounter.'
  }
};

export const READMISSION_SYMPTOMS_LIST = [
  'Fatigue', 'Frequent urination', 'Excessive thirst', 'Blurred vision',
  'Slow-healing sores', 'Tingling in hands/feet', 'Increased hunger',
  'Unexplained weight loss', 'Dry skin', 'Frequent infections',
  'Irritability', 'Nausea', 'Chest Pain', 'Shortness of Breath',
  'Dizziness', 'Palpitations', 'Edema', 'Cough', 'Fever', 'Headache'
];

export function validateReadmissionField(name, value) {
  const def = readmissionFields[name];
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
