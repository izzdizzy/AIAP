import React, { useState } from 'react';
import FormField from '../../../components/FormField';
import ProgressSidebar from '../../../components/ProgressSidebar';
import FileUploadZone from '../../../components/FileUploadZone';
import PrimaryButton from '../../../components/PrimaryButton';
import FeatureImportanceBar from '../../../components/FeatureImportanceBar';
import {
  readmissionSteps,
  readmissionFieldGroups,
  readmissionFields,
  READMISSION_SYMPTOMS_LIST,
  validateReadmissionField
} from '../utils/readmissionConfig';
import { useFormValidation } from '../../../hooks/useFormValidation';
import { uploadReadmissionPatientFile } from '../services/api';

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
  const [stepIndex, setStepIndex] = useState(0);
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

  const currentStep = readmissionSteps[stepIndex] || readmissionSteps[0];
  const canGoPrevious = stepIndex > 0;
  const canGoNext = stepIndex < readmissionSteps.length - 1;

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
    setStepIndex(prev => Math.max(prev - 1, 0));
  }

  function handleSubmitForm(e) {
    e.preventDefault();

    if (!validateAll()) {
      const errorKeys = Object.keys(errors).filter(k => errors[k]);
      if (errorKeys.length > 0) {
        for (const step of readmissionSteps) {
          const fields = getStepFieldNames(step.id);
          if (fields.some(f => errorKeys.includes(f))) {
            setStepIndex(readmissionSteps.indexOf(step));
            break;
          }
        }
      }
      return;
    }

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

  const sectionTitle = currentStep.title.replace(/^\d+\.\s*/, '');

  return (
    <div className="assessment-layout">
      <div className="assessment-main">
        {/* Extracted Form Section Title OUTSIDE and ABOVE Main Container (22px bold #F8FAFC, min 16px gap) */}
        <h2 style={{
          fontSize: '22px',
          fontWeight: 700,
          color: '#F8FAFC',
          marginTop: '16px',
          marginBottom: '16px',
          letterSpacing: '-0.01em'
        }}>
          {sectionTitle}
        </h2>

        <div className="section-card">
          {uploadMessage && (
            <div className={`alert-banner alert-banner--${uploadMessage.type === 'error' ? 'danger' : 'info'}`} style={{ marginBottom: '16px' }}>
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
                {canGoPrevious ? (
                  <PrimaryButton
                    type="button"
                    variant="secondary"
                    onClick={goPrevious}
                  >
                    Previous Step
                  </PrimaryButton>
                ) : null}

                {canGoNext ? (
                  <PrimaryButton
                    key="next-button"
                    type="button"
                    variant="primary"
                    onClick={goNext}
                  >
                    Next Step
                  </PrimaryButton>
                ) : (
                  <PrimaryButton
                    key="submit-button"
                    type="submit"
                    variant="primary"
                    disabled={loading}
                  >
                    {loading ? 'Evaluating Readmission Risk…' : 'Run Assessment'}
                  </PrimaryButton>
                )}

                <PrimaryButton
                  type="button"
                  variant="utility"
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
                </PrimaryButton>
              </div>
            </form>
        </div>
      </div>

      <div style={{ position: 'sticky', top: '16px' }}>
        <ProgressSidebar
          answeredCount={answeredCount}
          totalCount={totalFields}
          groups={groupProgress}
          steps={readmissionSteps}
          currentStepIndex={stepIndex + 1}
          onSelectStep={(idx) => setStepIndex(idx - 1)}
        />
      </div>
    </div>
  );
}
