import React, { useState } from 'react';
import SectionCard from '../../components/SectionCard';
import FormField from '../../components/FormField';
import PrimaryButton from '../../components/PrimaryButton';
import ProgressSidebar from '../../components/ProgressSidebar';
import FeatureImportanceBar from '../../components/FeatureImportanceBar';
import Disclaimer from '../../components/Disclaimer';
import {
  diabetesSteps,
  diabetesFieldGroups,
  diabetesFields,
  validateDiabetesField
} from '../../utils/diabetesConfig';
import { useFormValidation } from '../../hooks/useFormValidation';
import { predictRisk } from '../../services/diabetes/api';

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

export default function DiabetesPage({ onBackToLanding }) {
  const [stepIndex, setStepIndex] = useState(1);
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState(null);
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
    initialValues: DEFAULT_DIABETES_VALUES,
    validateFieldValue: validateDiabetesField,
    fieldOrder: Object.keys(diabetesFields)
  });

  const currentStep = diabetesSteps[stepIndex] || diabetesSteps[1];

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
    setStepIndex(prev => Math.max(prev - 1, 1));
  }

  async function handleSubmitForm(e) {
    e.preventDefault();
    if (!validateAll()) return;

    setLoading(true);
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
      const result = await predictRisk(payload);
      setPrediction(result);
    } catch (err) {
      setError(err.message || 'Failed to predict diabetes risk.');
    } finally {
      setLoading(false);
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

  return (
    <div className="page-stack">
      <div className="assessment-layout">
        <div className="assessment-main">
          <SectionCard title="Diabetes Risk Classifier">
            {error && (
              <div className="alert-banner alert-banner--danger" role="alert">
                {error}
              </div>
            )}

            {!prediction ? (
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
                  {stepIndex > 1 && (
                    <PrimaryButton
                      type="button"
                      variant="ghost"
                      onClick={goPrevious}
                    >
                      Previous Step
                    </PrimaryButton>
                  )}

                  {stepIndex < diabetesSteps.length - 1 ? (
                    <PrimaryButton
                      type="button"
                      onClick={goNext}
                    >
                      Next Step
                    </PrimaryButton>
                  ) : (
                    <PrimaryButton
                      type="submit"
                      disabled={loading}
                    >
                      {loading ? 'Evaluating Diabetes Risk…' : 'Run Diabetes Assessment'}
                    </PrimaryButton>
                  )}

                  <PrimaryButton
                    type="button"
                    variant="ghost"
                    onClick={handleLoadSampleData}
                  >
                    Load Sample Data
                  </PrimaryButton>
                </div>
              </form>
            ) : (
              <div style={{ display: 'grid', gap: '20px' }}>
                <div style={{
                  padding: '20px',
                  borderRadius: '16px',
                  background: 'var(--surface-muted)',
                  border: '1px solid var(--border)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Diabetes Risk Result</h3>
                    <span className={`risk-pill risk-pill--${(prediction.risk_band || prediction.risk_label || 'low').toLowerCase()}`}>
                      {prediction.risk_band || prediction.risk_label || 'Risk Assessment Complete'}
                    </span>
                  </div>

                  {prediction.risk_probability !== undefined && (
                    <div style={{ margin: '16px 0' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                        <span style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>Calculated Probability</span>
                        <strong style={{ fontSize: '1.1rem', color: 'var(--accent)' }}>
                          {(prediction.risk_probability * 100).toFixed(1)}%
                        </strong>
                      </div>
                      <div style={{ height: '10px', borderRadius: '999px', background: 'var(--surface)', overflow: 'hidden', border: '1px solid var(--border)' }}>
                        <div style={{
                          width: `${Math.min(100, Math.max(0, prediction.risk_probability * 100))}%`,
                          height: '100%',
                          background: prediction.risk_probability > 0.5 ? 'var(--risk-high-text)' : 'var(--risk-low-text)',
                          borderRadius: '999px',
                          transition: 'width 0.4s ease'
                        }} />
                      </div>
                    </div>
                  )}

                  {prediction.top_factors && prediction.top_factors.length > 0 && (
                    <div style={{ marginTop: '16px' }}>
                      <h4 style={{ margin: '0 0 8px', fontSize: '0.9rem', color: 'var(--text-muted)' }}>Top Contributing Risk Factors</h4>
                      <FeatureImportanceBar
                        factors={prediction.top_factors.map(f => typeof f === 'string' ? { feature: f, importance: 1 } : f)}
                      />
                    </div>
                  )}
                </div>

                <PrimaryButton
                  type="button"
                  variant="ghost"
                  onClick={() => setPrediction(null)}
                >
                  ← Edit Patient Inputs
                </PrimaryButton>
              </div>
            )}
          </SectionCard>
        </div>

        <div style={{ position: 'sticky', top: '16px' }}>
          <ProgressSidebar
            answeredCount={answeredCount}
            totalCount={totalFields}
            groups={groupProgress}
            steps={diabetesSteps}
            currentStepIndex={stepIndex}
            onSelectStep={setStepIndex}
          />
        </div>
      </div>

      <Disclaimer compact />
    </div>
  );
}
