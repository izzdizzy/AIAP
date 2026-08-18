import React, { useState } from 'react';
import FormField from '../FormField';
import ProgressSidebar from '../ProgressSidebar';
import FileUploadZone from '../FileUploadZone';
import {
  readmissionSteps,
  readmissionFieldGroups,
  readmissionFields,
  READMISSION_SYMPTOMS_LIST,
  validateReadmissionField
} from '../../utils/readmissionConfig';
import { useFormValidation } from '../../hooks/useFormValidation';
import { uploadReadmissionPatientFile } from '../../services/readmission/api';
import RiskDashboard from './RiskDashboard'

const DEFAULT_READMISSION_VALUES = {
  age: '50-60',
  chas_tier: 'None',
  prior_admissions: 0,
  time_in_hospital: 3,
  number_inpatient: 0,
  number_emergency: 0,
  number_outpatient: 0,
  comorbidity_count: 2,
  number_diagnoses: 5,
  num_lab_procedures: 40,
  num_medications: 10
};

export default function PatientForm({ onSubmit, loading = false, onFileUpload, prediction = null, onResetPrediction }) {
  const [stepIndex, setStepIndex] = useState(1);
  const [uploading, setUploading] = useState(false);
  const [selectedSymptoms, setSelectedSymptoms] = useState([]);
  const [uploadMessage, setUploadStatus] = useState(null);

  const {
    values,
    setValues,
    errors,
    handleChange,
    handleBlur,
    validateFields,
    validateAll
  } = useFormValidation({
    initialValues: DEFAULT_READMISSION_VALUES,
    validateFieldValue: validateReadmissionField,
    fieldOrder: Object.keys(readmissionFields)
  });

  const currentStep = readmissionSteps[stepIndex] || readmissionSteps[1];

  function handleSymptomToggle(symptom) {
    setSelectedSymptoms(prev =>
      prev.includes(symptom)
        ? prev.filter(s => s !== symptom)
        : [...prev, symptom]
    );
  }

  async function handleFileUpload(file) {
    if (!file) return;
    setUploading(true);
    setUploadStatus(null);

    try {
      const response = await uploadReadmissionPatientFile(file);
      if (response && response.success && response.patient_data) {
        const d = response.patient_data;
        setValues(prev => ({
          ...prev,
          age: d.age_group || d.age_group_display || prev.age,
          chas_tier: d.chas_tier || prev.chas_tier,
          prior_admissions: d.total_prior_admissions ?? d.number_inpatient ?? prev.prior_admissions,
          time_in_hospital: d.time_in_hospital ?? prev.time_in_hospital,
          number_inpatient: d.number_inpatient ?? prev.number_inpatient,
          number_emergency: d.number_emergency ?? prev.number_emergency,
          number_outpatient: d.number_outpatient ?? prev.number_outpatient,
          comorbidity_count: d.comorbidity_count ?? prev.comorbidity_count,
          number_diagnoses: d.number_diagnoses ?? prev.number_diagnoses,
          num_lab_procedures: d.num_lab_procedures ?? prev.num_lab_procedures,
          num_medications: d.total_medications ?? d.num_medications ?? prev.num_medications
        }));

        if (Array.isArray(d.symptoms)) {
          setSelectedSymptoms(d.symptoms);
        }

        if (onFileUpload) {
          onFileUpload(response);
        }

        setUploadStatus({ type: 'success', text: 'File parsed! Form fields auto-populated successfully.' });
      } else {
        throw new Error(response?.error || 'Could not parse patient file.');
      }
    } catch (err) {
      setUploadStatus({ type: 'error', text: 'File import error: ' + err.message });
    } finally {
      setUploading(false);
    }
  }

  function getStepFieldNames(stepId) {
    if (stepId === 'demographics') return ['age', 'chas_tier', 'prior_admissions'];
    if (stepId === 'hospitalization') return ['time_in_hospital', 'number_inpatient', 'number_emergency', 'number_outpatient'];
    if (stepId === 'clinical') return ['comorbidity_count', 'number_diagnoses', 'num_lab_procedures', 'num_medications'];
    return [];
  }

  function goNext() {
    const fieldsToValidate = getStepFieldNames(currentStep.id);
    if (fieldsToValidate.length > 0 && !validateFields(fieldsToValidate)) {
      return;
    }
    setStepIndex(prev => Math.min(prev + 1, readmissionSteps.length - 1));
  }

  function goPrevious() {
    setStepIndex(prev => Math.max(prev - 1, 1));
  }

  function handleSubmitForm(e) {
    e.preventDefault();
    if (!validateAll()) return;

    const ageNum = values.age ? parseInt(String(values.age).split('-')[0], 10) + 5 : 55;

    const payload = {
      ...values,
      age: ageNum,
      age_numeric: ageNum,
      prior_admissions: Number(values.prior_admissions) || 0,
      time_in_hospital: Number(values.time_in_hospital) || 3,
      number_inpatient: Number(values.number_inpatient) || 0,
      number_emergency: Number(values.number_emergency) || 0,
      number_outpatient: Number(values.number_outpatient) || 0,
      comorbidity_count: Number(values.comorbidity_count) || 2,
      number_diagnoses: Number(values.number_diagnoses) || 5,
      num_lab_procedures: Number(values.num_lab_procedures) || 40,
      medication_count: Number(values.num_medications) || 10,
      num_medications: Number(values.num_medications) || 10,
      symptoms: selectedSymptoms
    };

    onSubmit(payload);
  }

  const totalFields = Object.keys(readmissionFields).length;
  const answeredCount = Object.keys(readmissionFields).filter(
    k => values[k] !== undefined && values[k] !== null && values[k] !== ''
  ).length;

  const groupProgress = readmissionFieldGroups.map(group => {
    const groupAnswered = group.fields.filter(
      k => values[k] !== undefined && values[k] !== null && values[k] !== ''
    ).length;
    const groupTotal = group.fields.length;
    return {
      ...group,
      answeredCount: groupAnswered,
      totalCount: groupTotal,
      statusClass: groupAnswered === groupTotal ? 'progress-group--green' : 'progress-group--orange'
    };
  });

  return (
    <div className="assessment-layout">
      <div className="assessment-main">
        <div className="section-card">
          <div className="section-card__header">
            <h2>Patient Readmission Assessment</h2>
          </div>

          {uploadMessage && (
            <div className={`alert-banner alert-banner--${uploadMessage.type === 'error' ? 'danger' : 'info'}`}>
              {uploadMessage.text}
            </div>
          )}

          <form onSubmit={handleSubmitForm} noValidate className="assessment-form">
            {currentStep.id === 'demographics' && (
              <div className="assessment-group">
                <FileUploadZone
                  onFileSelect={handleFileUpload}
                  isUploading={uploading}
                  label="Upload Patient Record (CSV/Excel) to Auto-Fill Fields"
                />

                <div className="assessment-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <FormField
                    field={readmissionFields.age}
                    value={values.age}
                    error={errors.age}
                    onChange={handleChange}
                    onBlur={handleBlur}
                  />
                  <FormField
                    field={readmissionFields.chas_tier}
                    value={values.chas_tier}
                    error={errors.chas_tier}
                    onChange={handleChange}
                    onBlur={handleBlur}
                  />
                  <FormField
                    field={readmissionFields.prior_admissions}
                    value={values.prior_admissions}
                    error={errors.prior_admissions}
                    onChange={handleChange}
                    onBlur={handleBlur}
                  />
                </div>

                <div style={{ marginTop: '20px' }}>
                  <label className="form-field__label" style={{ marginBottom: '10px', display: 'block', fontWeight: 600 }}>
                    Active Symptoms Selection
                  </label>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {READMISSION_SYMPTOMS_LIST.map(symptom => {
                      const selected = selectedSymptoms.includes(symptom);
                      return (
                        <button
                          key={symptom}
                          type="button"
                          style={{
                            padding: '8px 14px',
                            borderRadius: '999px',
                            border: selected ? '1px solid var(--accent, #14B8A6)' : '1px solid var(--border)',
                            background: selected ? 'var(--risk-low-bg, rgba(20, 184, 166, 0.15))' : 'var(--surface)',
                            color: selected ? 'var(--accent, #14B8A6)' : 'var(--text-muted)',
                            fontSize: '0.82rem',
                            fontWeight: selected ? '600' : '500',
                            cursor: 'pointer',
                            transition: 'all 0.2s ease',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px'
                          }}
                          onClick={() => handleSymptomToggle(symptom)}
                        >
                          <span>{symptom}</span>
                          <span style={{ fontWeight: 700 }}>{selected ? '✓' : '+'}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}

            {currentStep.id === 'hospitalization' && (
              <div className="assessment-group">
                <div className="assessment-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <FormField
                    field={readmissionFields.time_in_hospital}
                    value={values.time_in_hospital}
                    error={errors.time_in_hospital}
                    onChange={handleChange}
                    onBlur={handleBlur}
                  />
                  <FormField
                    field={readmissionFields.number_inpatient}
                    value={values.number_inpatient}
                    error={errors.number_inpatient}
                    onChange={handleChange}
                    onBlur={handleBlur}
                  />
                  <FormField
                    field={readmissionFields.number_emergency}
                    value={values.number_emergency}
                    error={errors.number_emergency}
                    onChange={handleChange}
                    onBlur={handleBlur}
                  />
                  <FormField
                    field={readmissionFields.number_outpatient}
                    value={values.number_outpatient}
                    error={errors.number_outpatient}
                    onChange={handleChange}
                    onBlur={handleBlur}
                  />
                </div>
              </div>
            )}

            {currentStep.id === 'clinical' && (
              <div className="assessment-group">
                <div className="assessment-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <FormField
                    field={readmissionFields.comorbidity_count}
                    value={values.comorbidity_count}
                    error={errors.comorbidity_count}
                    onChange={handleChange}
                    onBlur={handleBlur}
                  />
                  <FormField
                    field={readmissionFields.number_diagnoses}
                    value={values.number_diagnoses}
                    error={errors.number_diagnoses}
                    onChange={handleChange}
                    onBlur={handleBlur}
                  />
                  <FormField
                    field={readmissionFields.num_lab_procedures}
                    value={values.num_lab_procedures}
                    error={errors.num_lab_procedures}
                    onChange={handleChange}
                    onBlur={handleBlur}
                  />
                  <FormField
                    field={readmissionFields.num_medications}
                    value={values.num_medications}
                    error={errors.num_medications}
                    onChange={handleChange}
                    onBlur={handleBlur}
                  />
                </div>
              </div>
            )}

            <div className="form-actions" style={{ marginTop: '24px' }}>
              {stepIndex > 1 && (
                <button
                  type="button"
                  className="primary-button primary-button--ghost"
                  onClick={goPrevious}
                >
                  Previous Step
                </button>
              )}

              {stepIndex < readmissionSteps.length - 1 ? (
                <button
                  type="button"
                  className="primary-button"
                  onClick={goNext}
                >
                  Next Step
                </button>
              ) : (
                <button
                  type="submit"
                  className="primary-button"
                  disabled={loading}
                >
                  {loading ? 'Evaluating Readmission Risk…' : 'Run Readmission Assessment'}
                </button>
              )}

              <button
                type="button"
                className="primary-button primary-button--ghost"
                onClick={() => {
                  setValues({
                    age: '60-70',
                    chas_tier: 'Pioneer',
                    prior_admissions: 2,
                    time_in_hospital: 5,
                    number_inpatient: 2,
                    number_emergency: 1,
                    number_outpatient: 3,
                    comorbidity_count: 4,
                    number_diagnoses: 7,
                    num_lab_procedures: 52,
                    num_medications: 14
                  });
                  setSelectedSymptoms(['Fatigue', 'Shortness of Breath', 'Edema']);
                }}
              >
                Load Sample Data
              </button>
            </div>
          </form>
        </div>
      </div>

      <div style={{ position: 'sticky', top: '16px' }}>
        {!prediction ? (
          <ProgressSidebar
            answeredCount={answeredCount}
            totalCount={totalFields}
            groups={groupProgress}
            steps={readmissionSteps}
            currentStepIndex={stepIndex}
            onSelectStep={setStepIndex}
          />
        ) : (
          <div>
            <RiskDashboard prediction={prediction} />
            {onResetPrediction && (
              <button
                type="button"
                className="primary-button primary-button--ghost"
                onClick={onResetPrediction}
                style={{ marginTop: '16px', width: '100%' }}
              >
                ← Edit Patient Inputs
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
