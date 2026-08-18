import { useState, useEffect } from 'react';
import { checkHealth, predictRisk, explainRisk } from '../../services/diabetes/api';
import FormField from '../../components/FormField';
import FormStepper from '../../components/FormStepper';
import ProgressSidebar from '../../components/ProgressSidebar';
import FeatureImportanceBar from '../../components/FeatureImportanceBar';
import {
  diabetesSteps,
  diabetesFieldGroups,
  diabetesFields,
  validateDiabetesField
} from '../../utils/diabetesConfig';
import { DIABETES_FACTOR_LABELS } from '../../utils/diabetesMappings';
import { useFormValidation } from '../../hooks/useFormValidation';

const DEFAULTS = {
  CholCheck: 1, Stroke: 0, HvyAlcoholConsump: 0, AnyHealthcare: 1,
  NoDocbcCost: 0, MentHlth: 2, PhysHlth: 3, Education: 4, Income: 5
};

const DEFAULT_DIABETES_PROFILE = {
  GenHlth: 3,
  BMI: 28,
  Age: 9,
  Sex: 1,
  HighBP: 1,
  HighChol: 1,
  PhysActivity: 1,
  DiffWalk: 0,
  Smoker: 0,
  HeartDiseaseorAttack: 0,
  Fruits: 1,
  Veggies: 1
};

export default function DiabetesPage({ onBackToLanding }) {
  const [live, setLive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [explaining, setExplaining] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [explanation, setExplanation] = useState('');
  const [stepIndex, setStepIndex] = useState(1);

  const {
    values,
    setValues,
    errors,
    handleChange,
    handleBlur,
    validateFields,
    validateAll
  } = useFormValidation({
    initialValues: DEFAULT_DIABETES_PROFILE,
    validateFieldValue: validateDiabetesField,
    fieldOrder: Object.keys(diabetesFields)
  });

  useEffect(() => {
    checkHealth().then(result => {
      setLive(result.status === 'ok' && result.model_loaded);
    });
  }, []);

  const currentStep = diabetesSteps[stepIndex] || diabetesSteps[1];

  function getStepFieldNames(stepId) {
    if (stepId === 'demographics') return ['GenHlth', 'BMI', 'Age', 'Sex'];
    if (stepId === 'lifestyle') return ['HighBP', 'HighChol', 'PhysActivity', 'DiffWalk', 'Smoker', 'HeartDiseaseorAttack', 'Fruits', 'Veggies'];
    return [];
  }

  function goNext() {
    const stepFields = getStepFieldNames(currentStep.id);
    if (stepFields.length > 0 && !validateFields(stepFields)) {
      return;
    }
    setStepIndex(prev => Math.min(prev + 1, diabetesSteps.length - 1));
  }

  function goPrevious() {
    setStepIndex(prev => Math.max(prev - 1, 1));
  }

  async function handleAssess(e) {
    if (e) e.preventDefault();
    if (!validateAll()) return;

    setLoading(true);
    setErrorMessage(null);
    try {
      const numericValues = {};
      Object.keys(values).forEach(k => {
        numericValues[k] = Number(values[k]);
      });
      const fullProfile = { ...DEFAULTS, ...numericValues };
      const result = await predictRisk(fullProfile);
      setPrediction(result);
    } catch (error) {
      setErrorMessage('Prediction request failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleExplain() {
    if (!prediction) return;
    setExplaining(true);
    setErrorMessage(null);
    try {
      const numericValues = {};
      Object.keys(values).forEach(k => {
        numericValues[k] = Number(values[k]);
      });
      const fullProfile = { ...DEFAULTS, ...numericValues };
      const result = await explainRisk(fullProfile);
      setExplanation(result.explanation);
    } catch (error) {
      setErrorMessage('Explanation generation failed: ' + error.message);
    } finally {
      setExplaining(false);
    }
  }

  function loadSample() {
    const sample = {
      GenHlth: 4, BMI: 34, Age: 9, Sex: 1, HighBP: 1, HighChol: 1,
      PhysActivity: 0, DiffWalk: 1, Smoker: 1, HeartDiseaseorAttack: 0,
      Fruits: 0, Veggies: 1
    };
    setValues(sample);
    setErrorMessage(null);
  }

  const renderBandPill = () => {
    if (!prediction) return null;
    const band = (prediction.risk_band || 'Low').toLowerCase();
    const pillClass = band.includes('high')
      ? 'risk-pill--high'
      : band.includes('mod')
      ? 'risk-pill--moderate'
      : 'risk-pill--low';

    return (
      <span className={`risk-pill ${pillClass}`}>
        {prediction.risk_band} Risk · {prediction.risk_label}
      </span>
    );
  };

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

  const formattedFactors = prediction?.top_factors ? prediction.top_factors.map(f => {
    const [k, v] = f.split(' = ');
    return {
      label: DIABETES_FACTOR_LABELS[k] || k,
      value: 0.7,
      displayValue: v,
      direction: 'positive'
    };
  }) : [];

  return (
    <div className="page-stack">
      {/* Sub-Header / Intro */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <p className="eyebrow">Endocrine Health Module</p>
          <h2 style={{ fontSize: '1.8rem', margin: '0 0 8px 0', color: 'var(--text)' }}>
            Diabetes Chronic Risk Classifier
          </h2>
          <p style={{ margin: 0, color: 'var(--text-muted)', maxWidth: '640px' }}>
            Evaluate patient health parameters across demographic and clinical factors to gauge diabetes risk and receive AI guidance.
          </p>
        </div>

        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 14px',
          borderRadius: '999px',
          background: 'var(--surface-muted)',
          border: '1px solid var(--border)',
          fontSize: '0.85rem',
          color: 'var(--text-muted)'
        }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: live ? 'var(--risk-low-text)' : 'var(--text-muted)'
          }} />
          <span>{live ? 'Service Online' : 'Demo Mode (Offline)'}</span>
        </div>
      </div>

      {errorMessage && (
        <div className="alert-banner alert-banner--danger" role="alert">
          <strong>Error:</strong> {errorMessage}
        </div>
      )}

      {/* Grid Layout */}
      <div className="assessment-layout" style={{ gridTemplateColumns: 'minmax(0, 1.1fr) minmax(0, 0.9fr)', gap: '20px' }}>
        {/* Form Card */}
        <div className="section-card">
          <div className="section-card__header">
            <h2>Patient Health Profile</h2>
            <p>Complete multi-step parameters or load sample data for evaluation.</p>
          </div>

          <FormStepper
            steps={diabetesSteps}
            currentStepIndex={stepIndex}
            onSelectStep={setStepIndex}
          />

          <form onSubmit={handleAssess} noValidate className="assessment-form">
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
                <button
                  type="button"
                  className="primary-button primary-button--ghost"
                  onClick={goPrevious}
                >
                  Previous Step
                </button>
              )}

              {stepIndex < diabetesSteps.length - 1 ? (
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
                  {loading ? 'Calculating Risk…' : 'Assess Diabetes Risk'}
                </button>
              )}

              <button
                type="button"
                className="primary-button primary-button--ghost"
                onClick={loadSample}
              >
                Load Sample Data
              </button>
            </div>
          </form>
        </div>

        {/* Right Column: Progress Sidebar BEFORE assessment, Results Card AFTER assessment */}
        <div style={{ position: 'sticky', top: '16px' }}>
          {!prediction ? (
            <ProgressSidebar
              answeredCount={answeredCount}
              totalCount={totalFields}
              groups={groupProgress}
            />
          ) : (
            <div className="result-card" style={{ padding: '24px' }}>
              <div style={{ display: 'grid', gap: '20px' }}>
                <div style={{ textAlign: 'center', borderBottom: '1px solid var(--border)', paddingBottom: '18px' }}>
                  <div style={{ fontSize: '2.8rem', fontWeight: 700, color: 'var(--text)' }}>
                    {Math.round(prediction.risk_probability * 100)}%
                  </div>
                  <div style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
                    Predicted Diabetes Likelihood
                  </div>
                  {renderBandPill()}
                </div>

                {/* Top Factors */}
                <div>
                  <h4 style={{ fontSize: '0.95rem', margin: '0 0 10px 0', color: 'var(--text)' }}>
                    Top Risk Drivers
                  </h4>
                  <FeatureImportanceBar factors={formattedFactors} />
                </div>

                {/* AI Explanation */}
                <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <h4 style={{ fontSize: '0.95rem', margin: 0, color: 'var(--text)' }}>
                      Personalized AI Explanation
                    </h4>
                    <span className="risk-pill risk-pill--low" style={{ fontSize: '0.72rem', padding: '2px 8px' }}>
                      GenAI
                    </span>
                  </div>

                  {explaining ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                      <span className="typing-dot" style={{ background: 'var(--accent)' }} />
                      Generating Clinical AI Explanation…
                    </div>
                  ) : explanation ? (
                    <div style={{
                      fontSize: '0.88rem',
                      color: 'var(--text)',
                      background: 'var(--surface-muted)',
                      padding: '14px',
                      borderRadius: '12px',
                      border: '1px solid var(--border)',
                      lineHeight: '1.5',
                      whiteSpace: 'pre-wrap'
                    }}>
                      {explanation}
                    </div>
                  ) : (
                    <button
                      type="button"
                      className="primary-button primary-button--ghost"
                      style={{ width: '100%' }}
                      onClick={handleExplain}
                    >
                      Generate AI Explanation
                    </button>
                  )}
                </div>

                <button
                  type="button"
                  className="primary-button primary-button--ghost"
                  onClick={() => setPrediction(null)}
                  style={{ marginTop: '12px' }}
                >
                  ← Edit Form Parameters
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div style={{
        fontSize: '0.82rem',
        color: 'var(--text-muted)',
        background: 'var(--surface-muted)',
        padding: '12px 16px',
        borderRadius: '12px',
        border: '1px solid var(--border)',
        marginTop: '16px'
      }}>
        <strong>Clinical Disclaimer:</strong> This risk assessment is a statistical screening decision-support tool. It does not replace formal clinical diagnosis. Please consult a licensed medical provider for diagnostic evaluation.
      </div>
    </div>
  );
}
