import React, { useState } from 'react';
import SectionCard from '../../components/SectionCard';
import FormField from '../../components/FormField';
import PrimaryButton from '../../components/PrimaryButton';
import ProgressSidebar from '../../components/ProgressSidebar';
import FeatureImportanceBar from '../../components/FeatureImportanceBar';
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

export default function DiabetesPage({ onBackToLanding, onOpenChat }) {
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

  // Explicit form submission handler (auto-assessment disabled on step navigation)
  async function handleSubmitForm(e) {
    e.preventDefault();

    // Prevent execution if user is navigating on earlier form steps
    if (stepIndex < diabetesSteps.length - 1) {
      goNext();
      return;
    }

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

  const sectionTitle = !prediction
    ? currentStep.title.replace(/^\d+\.\s*/, '')
    : 'Diabetes Assessment Findings';

  const riskProbPct = prediction?.risk_probability !== undefined
    ? (prediction.risk_probability * 100).toFixed(1)
    : '0.0';

  const riskLabel = prediction?.risk_band || prediction?.risk_label || (prediction?.risk_probability > 0.5 ? 'High Risk' : 'Low Risk');
  const severityScore = prediction?.risk_probability !== undefined
    ? Math.round(prediction.risk_probability * 100)
    : 0;

  const pillClass = riskLabel.toLowerCase().includes('high')
    ? 'risk-pill--high'
    : riskLabel.toLowerCase().includes('mod')
    ? 'risk-pill--moderate'
    : 'risk-pill--low';

  const formattedFactors = (prediction?.top_factors || []).map(f => {
    if (typeof f === 'string') {
      return { label: f, value: 0.5, displayValue: f, direction: 'positive' };
    }
    return {
      label: f.feature || f.name,
      value: Math.abs(f.importance || f.impact || 0.2),
      displayValue: `${f.importance > 0 ? '+' : ''}${f.importance || ''}`,
      direction: (f.importance || 0) < 0 ? 'negative' : 'positive'
    };
  });

  return (
    <div className="page-stack">
      <div className="assessment-layout">
        <div className="assessment-main">
          {/* Extracted Form Section Title OUTSIDE and ABOVE Main Container (22px bold #F8FAFC) */}
          <h2 style={{
            fontSize: '22px',
            fontWeight: 700,
            color: '#F8FAFC',
            marginBottom: '12px',
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
                      variant="secondary"
                      onClick={goPrevious}
                    >
                      Previous Step
                    </PrimaryButton>
                  )}

                  {stepIndex < diabetesSteps.length - 1 ? (
                    <PrimaryButton
                      type="button"
                      variant="primary"
                      onClick={goNext}
                    >
                      Next Step
                    </PrimaryButton>
                  ) : (
                    <PrimaryButton
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
            ) : (
              /* Standardized Results Layout: Left Main Canvas & Right Action Panel */
              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '20px' }}>
                {/* Top Summary Bar: Probability, Risk Badge, Severity Score */}
                <div style={{
                  display: 'flex',
                  justify: 'space-between',
                  alignItems: 'center',
                  padding: '16px 20px',
                  borderRadius: '12px',
                  background: '#1E293B',
                  border: '1px solid #334155',
                  flexWrap: 'wrap',
                  gap: '12px'
                }}>
                  <div>
                    <span style={{ fontSize: '0.82rem', color: '#94A3B8', display: 'block' }}>Risk Probability</span>
                    <strong style={{ fontSize: '1.6rem', color: '#38BDF8', fontWeight: 700 }}>{riskProbPct}%</strong>
                  </div>

                  <div>
                    <span style={{ fontSize: '0.82rem', color: '#94A3B8', display: 'block' }}>Risk Badge</span>
                    <span className={`risk-pill ${pillClass}`}>
                      {riskLabel}
                    </span>
                  </div>

                  <div>
                    <span style={{ fontSize: '0.82rem', color: '#94A3B8', display: 'block' }}>Severity Score</span>
                    <strong style={{ fontSize: '1.3rem', color: '#F8FAFC', fontWeight: 700 }}>{severityScore}/100</strong>
                  </div>
                </div>

                {/* Body: Contributing Risk Factors / Feature Importance */}
                <div style={{ padding: '16px 20px', borderRadius: '12px', background: '#1E293B', border: '1px solid #334155' }}>
                  <h3 style={{ margin: '0 0 12px', fontSize: '1.05rem', color: '#F8FAFC', fontWeight: 600 }}>
                    Contributing Risk Factors (SHAP Feature Importance)
                  </h3>
                  {formattedFactors.length > 0 ? (
                    <FeatureImportanceBar factors={formattedFactors} />
                  ) : (
                    <p style={{ color: '#94A3B8' }}>No individual feature impact values available.</p>
                  )}
                </div>

                {/* Bottom Action Area: Prominent Ask AI Assistant + Standard Actions */}
                <div style={{
                  display: 'flex',
                  gap: '12px',
                  flexWrap: 'wrap',
                  alignItems: 'center',
                  paddingTop: '12px',
                  borderTop: '1px solid #334155'
                }}>
                  <PrimaryButton
                    type="button"
                    variant="ai"
                    onClick={() => onOpenChat ? onOpenChat() : (window.location.hash = 'chat')}
                  >
                    Ask AI Assistant
                  </PrimaryButton>

                  <PrimaryButton
                    type="button"
                    variant="secondary"
                    onClick={() => setPrediction(null)}
                  >
                    ← Edit Inputs
                  </PrimaryButton>

                  <PrimaryButton
                    type="button"
                    variant="secondary"
                    onClick={() => onBackToLanding ? onBackToLanding() : (window.location.hash = '')}
                  >
                    Return to Module Overview
                  </PrimaryButton>
                </div>
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
    </div>
  );
}
