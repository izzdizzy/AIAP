import React, { useState } from 'react';
import SectionCard from '../../../components/SectionCard';
import FormField from '../../../components/FormField';
import PrimaryButton from '../../../components/PrimaryButton';
import ProgressSidebar from '../../../components/ProgressSidebar';
import FeatureImportanceBar from '../../../components/FeatureImportanceBar';
import {
  diabetesSteps,
  diabetesFieldGroups,
  diabetesFields,
  validateDiabetesField
} from '../utils/diabetesConfig';
import { useFormValidation } from '../../../hooks/useFormValidation';
import { predictRisk } from '../services/api';

const DEFAULT_DIABETES_VALUES = {
  GenHlth: '2',
  BMI: 24.5,
  Age: '6',
  Sex: '0',
  HighBP: '0',
  HighChol: '0',
  PhysActivity: '1',
  DiffWalk: '0',
  Smoker: '0',
  HeartDiseaseorAttack: '0',
  Fruits: '1',
  Veggies: '1'
};

const SAMPLE_HIGH_RISK = {
  GenHlth: '4',
  BMI: 33.2,
  Age: '10',
  Sex: '1',
  HighBP: '1',
  HighChol: '1',
  PhysActivity: '0',
  DiffWalk: '1',
  Smoker: '1',
  HeartDiseaseorAttack: '1',
  Fruits: '0',
  Veggies: '0'
};

export default function DiabetesPage({ onSubmitAssessment, loading = false, initialValues = null }) {
  const [stepIndex, setStepIndex] = useState(0);
  const [error, setError] = useState(null);

  const {
    values,
    setValues,
    errors,
    handleChange,
    handleBlur,
    validateFields,
    validateAll
  } = useFormValidation({
    initialValues: initialValues || DEFAULT_DIABETES_VALUES,
    validateFieldValue: validateDiabetesField,
    fieldOrder: Object.keys(diabetesFields)
  });

  const currentStep = diabetesSteps[stepIndex] || diabetesSteps[0];
  const canGoPrevious = stepIndex > 0;
  const canGoNext = stepIndex < diabetesSteps.length - 1;

  function getStepFieldNames(stepId) {
    if (stepId === 'demographics') return ['GenHlth', 'BMI', 'Age', 'Sex'];
    if (stepId === 'lifestyle') return ['HighBP', 'HighChol', 'PhysActivity', 'DiffWalk', 'Smoker', 'HeartDiseaseorAttack', 'Fruits', 'Veggies'];
    return [];
  }

  function goNext() {
    const fieldsToValidate = getStepFieldNames(currentStep.id);
    if (fieldsToValidate.length > 0 && !validateFields(fieldsToValidate)) {
      return;
    }
    setStepIndex(prev => Math.min(prev + 1, diabetesSteps.length - 1));
  }

  function goPrevious() {
    setStepIndex(prev => Math.max(prev - 1, 0));
  }

  // Explicit form submission handler (auto-assessment disabled on step navigation)
  async function handleSubmitForm(e) {
    e.preventDefault();

    if (!validateAll()) {
      const errorKeys = Object.keys(errors).filter(k => errors[k]);
      if (errorKeys.length > 0) {
        for (const step of diabetesSteps) {
          const fields = getStepFieldNames(step.id);
          if (fields.some(f => errorKeys.includes(f))) {
            setStepIndex(diabetesSteps.indexOf(step));
            break;
          }
        }
      }
      return;
    }

    setError(null);

    const payload = {
      GenHlth: Number(values.GenHlth),
      BMI: Number(values.BMI),
      Age: Number(values.Age),
      Sex: Number(values.Sex),
      HighBP: Number(values.HighBP),
      HighChol: Number(values.HighChol),
      PhysActivity: Number(values.PhysActivity),
      DiffWalk: Number(values.DiffWalk),
      Smoker: Number(values.Smoker),
      HeartDiseaseorAttack: Number(values.HeartDiseaseorAttack),
      Fruits: Number(values.Fruits),
      Veggies: Number(values.Veggies)
    };

    try {
      if (onSubmitAssessment) {
        await onSubmitAssessment(payload);
      } else {
        const result = await predictRisk(payload);
        if (result) {
          // handle result
        }
      }
    } catch (err) {
      setError(err.message || 'Failed to predict diabetes risk.');
    }
  }

  function handleLoadSampleData() {
    setValues(SAMPLE_HIGH_RISK);
  }

  const totalFields = Object.keys(diabetesFields).length;
  const answeredCount = Object.keys(diabetesFields).filter(
    k => values[k] !== undefined && values[k] !== null && values[k] !== ''
  ).length;

  const groupProgress = diabetesFieldGroups.map(group => {
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
    <div className="page-stack diabetes-scope">
      <div className="assessment-layout">
        <div className="assessment-main">
          {/* Extracted Form Section Title OUTSIDE and ABOVE Main Container (22px bold #F8FAFC, min 16px gap) */}
          <h2 style={{
            fontSize: '22px',
            fontWeight: 700,
            color: 'var(--dia-text, var(--text, #F8FAFC))',
            marginTop: '16px',
            marginBottom: '16px',
            letterSpacing: '-0.01em'
          }}>
            {sectionTitle}
          </h2>

          <SectionCard>
            {error && (
              <div className="alert-banner alert-banner--danger" role="alert" style={{ marginBottom: '16px' }}>
                {error}
              </div>
            )}

            <form onSubmit={handleSubmitForm} noValidate className="assessment-form">
              {currentStep.id === 'demographics' && (
                <div className="assessment-group">
                  <div className="assessment-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    <FormField
                      field={diabetesFields.GenHlth}
                      value={values.GenHlth}
                      error={errors.GenHlth}
                      onChange={handleChange}
                      onBlur={handleBlur}
                    />
                    <FormField
                      field={diabetesFields.BMI}
                      value={values.BMI}
                      error={errors.BMI}
                      onChange={handleChange}
                      onBlur={handleBlur}
                    />
                    <FormField
                      field={diabetesFields.Age}
                      value={values.Age}
                      error={errors.Age}
                      onChange={handleChange}
                      onBlur={handleBlur}
                    />
                    <FormField
                      field={diabetesFields.Sex}
                      value={values.Sex}
                      error={errors.Sex}
                      onChange={handleChange}
                      onBlur={handleBlur}
                    />
                  </div>
                </div>
              )}

              {currentStep.id === 'lifestyle' && (
                <div className="assessment-group">
                  <div className="assessment-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    <FormField
                      field={diabetesFields.HighBP}
                      value={values.HighBP}
                      error={errors.HighBP}
                      onChange={handleChange}
                      onBlur={handleBlur}
                    />
                    <FormField
                      field={diabetesFields.HighChol}
                      value={values.HighChol}
                      error={errors.HighChol}
                      onChange={handleChange}
                      onBlur={handleBlur}
                    />
                    <FormField
                      field={diabetesFields.PhysActivity}
                      value={values.PhysActivity}
                      error={errors.PhysActivity}
                      onChange={handleChange}
                      onBlur={handleBlur}
                    />
                    <FormField
                      field={diabetesFields.DiffWalk}
                      value={values.DiffWalk}
                      error={errors.DiffWalk}
                      onChange={handleChange}
                      onBlur={handleBlur}
                    />
                    <FormField
                      field={diabetesFields.Smoker}
                      value={values.Smoker}
                      error={errors.Smoker}
                      onChange={handleChange}
                      onBlur={handleBlur}
                    />
                    <FormField
                      field={diabetesFields.HeartDiseaseorAttack}
                      value={values.HeartDiseaseorAttack}
                      error={errors.HeartDiseaseorAttack}
                      onChange={handleChange}
                      onBlur={handleBlur}
                    />
                    <FormField
                      field={diabetesFields.Fruits}
                      value={values.Fruits}
                      error={errors.Fruits}
                      onChange={handleChange}
                      onBlur={handleBlur}
                    />
                    <FormField
                      field={diabetesFields.Veggies}
                      value={values.Veggies}
                      error={errors.Veggies}
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
                    {loading ? 'Evaluating Diabetes Risk…' : 'Run Assessment'}
                  </PrimaryButton>
                )}

                <PrimaryButton
                  type="button"
                  variant="utility"
                  onClick={handleLoadSampleData}
                >
                  Load Sample Data
                </PrimaryButton>
              </div>
            </form>
          </SectionCard>
        </div>

        <div style={{ position: 'sticky', top: '16px' }}>
          <ProgressSidebar
            answeredCount={answeredCount}
            totalCount={totalFields}
            groups={groupProgress}
            steps={diabetesSteps}
            currentStepIndex={stepIndex + 1}
            onSelectStep={(idx) => setStepIndex(idx - 1)}
          />
        </div>
      </div>
    </div>
  );
}
