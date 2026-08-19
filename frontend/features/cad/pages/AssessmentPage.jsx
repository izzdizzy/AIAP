import PrimaryButton from '../../../components/PrimaryButton';
import FormField from '../../../components/FormField';
import SectionCard from '../../../components/SectionCard';
import ProgressSidebar from '../../../components/ProgressSidebar';
import {
  assessmentFieldGroups,
  assessmentSteps,
  fieldOrder,
  getFieldDefinition,
  stepFieldMap
} from '../utils/assessmentConfig';
import {
  getChestPainTriageAnswers,
  isFieldAnswered
} from '../utils/payload';
import { useAssessmentForm } from '../hooks/useAssessmentForm';
import { useMemo, useState } from 'react';

function formatFieldValue(field, values, fieldName) {
  if (fieldName === 'cp') {

    if (values.cpAssessment === 'none') {
      return 'No chest pain';
    }

    if (values.cpAssessment === 'manual') {
      const manual = getFieldDefinition('cpManual');

      const option = manual.options.find(
        (entry) => String(entry.value) === String(values.cpManual)
      );

      return option ? option.label : 'Not provided';
    }

    // Existing guided questionnaire logic continues below...
    const answers = getChestPainTriageAnswers(values);
    if (!Object.keys(answers).length) {
      return 'Not provided';
    }

    const labels = {
      yes: 'Yes',
      no: 'No'
    };
    return field.options
      .filter((question) => answers[question.id])
      .map((question) => `${question.label.replace(/\?$/, '')}: ${labels[answers[question.id]]}`)
      .join('; ');
  }

  const value = values[fieldName];
  if (!isFieldAnswered(fieldName, values)) {
    return 'Not provided';
  }

  if (field.kind === 'select') {
    const option = field.options.find((entry) => String(entry.value) === String(value));
    return option ? option.label : String(value);
  }

  return String(value);
}

export default function AssessmentPage({
  onSubmitAssessment,
  loading,
  onCancel,
  initialValues = null
}) {
  const [stepIndex, setStepIndex] = useState(0);
  const {
    values,
    errors,
    handleChange,
    handleBlur,
    validateFields,
    validateAll,
    getAnsweredCount,
    getAnsweredNames
  } = useAssessmentForm(initialValues);

  const answeredFieldNames = getAnsweredNames();
  const answeredSet = useMemo(() => new Set(answeredFieldNames), [answeredFieldNames]);
  const currentStep = assessmentSteps[stepIndex];
  const currentStepFields = stepFieldMap[currentStep?.id] ?? [];
  const currentFields = currentStepFields.map((fieldName) => getFieldDefinition(fieldName)).filter(Boolean);
  const validationErrors = Object.values(errors).filter(Boolean);

  const canGoPrevious = stepIndex > 0;
  const canGoNext = stepIndex < assessmentSteps.length - 1;

  function goNext() {
    if (currentStep?.id !== 'intro' && currentStepFields.length > 0 && !validateFields(currentStepFields)) {
      return;
    }

    setStepIndex((current) => Math.min(current + 1, assessmentSteps.length - 1));
  }

  function goPrevious() {
    setStepIndex((current) => Math.max(current - 1, 0));
  }

  function goToStep(nextStepIndex) {
    setStepIndex(nextStepIndex);
  }

  function getGroupProgress() {
    return assessmentFieldGroups.map((group) => {
      const answeredCount = group.fields.filter((fieldName) => answeredSet.has(fieldName)).length;
      const totalCount = group.fields.length;
      const isOptional = group.id === 'ecg-clinical-findings';

      let statusClass = 'progress-group--orange';
      if (answeredCount === totalCount) {
        statusClass = 'progress-group--green';
      } else if (isOptional && answeredCount > 0) {
        statusClass = 'progress-group--lime';
      }

      return {
        ...group,
        answeredCount,
        totalCount,
        statusClass
      };
    });
  }

  function renderStepSummary() {
    const groupProgress = getGroupProgress();

    return (
      <aside className="assessment-progress" aria-label="Assessment progress">
        <SectionCard title="Progress" description="Sections you have completed.">
          <div className="progress-metric">
            <strong>{getAnsweredCount()}</strong>
            <span>of {fieldOrder.length} answered</span>
          </div>
          <div className="progress-list">
            {groupProgress.map((group) => (
              <div key={group.id} className={`progress-group ${group.statusClass}`}>
                <div className="progress-group__header">
                  <strong>{group.title}</strong>
                  <span className="progress-group__count">
                    {group.answeredCount}/{group.totalCount}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </SectionCard>
      </aside>
    );
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!validateAll()) {
      // If validation fails, jump to first step with error so inline validation error is highlighted
      const errorKeys = Object.keys(errors).filter(k => errors[k]);
      if (errorKeys.length > 0) {
        for (const step of assessmentSteps) {
          const fields = stepFieldMap[step.id] || [];
          if (fields.some(f => errorKeys.includes(f))) {
            setStepIndex(assessmentSteps.indexOf(step));
            break;
          }
        }
      }
      return;
    }
    await onSubmitAssessment(values);
  }

  const answeredFields = fieldOrder.filter((fieldName) => isFieldAnswered(fieldName, values));
  const blankFields = fieldOrder.filter((fieldName) => !isFieldAnswered(fieldName, values));
  const visibleFields = currentFields.filter((field) => {
    // Hide manual selector unless Advanced mode is chosen
    if (field.name === 'cpManual') {
      return values.cpAssessment === 'manual';
    }

    // Hide guided triage unless "Currently experiencing chest pain" is chosen
    if (field.name === 'cp') {
      return values.cpAssessment === 'guided';
    }

    return true;
  });

  const sectionTitle = currentStep?.title.replace(/^\d+\.\s*/, '') || 'Personal Info';

  return (
    <div className="page-stack">
      <div className="assessment-layout">
        <div className="assessment-main">
          {/* Extracted Form Section Title OUTSIDE and ABOVE Main Container (22px bold #F8FAFC, min 16px gap) */}
          <h2 style={{
            fontSize: '22px',
            fontWeight: 700,
            color: 'var(--text)',
            marginTop: '16px',
            marginBottom: '16px',
            letterSpacing: '-0.01em'
          }}>
            {sectionTitle}
          </h2>

          <SectionCard>
            <form className="assessment-form" onSubmit={handleSubmit} noValidate>
              <div className="assessment-group">
                <div className="assessment-grid">
                  {visibleFields.map((field) => (
                    <FormField
                      key={field.name}
                      field={field}
                      value={values[field.name]}
                      values={values}
                      error={errors[field.name]}
                      onChange={handleChange}
                      onBlur={handleBlur}
                    />
                  ))}
                </div>
              </div>

              <div className="form-actions" style={{ marginTop: '24px' }}>
                {canGoPrevious ? (
                  <PrimaryButton type="button" variant="secondary" onClick={goPrevious}>
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
                    {loading ? 'Checking...' : 'Run Assessment'}
                  </PrimaryButton>
                )}
                <PrimaryButton
                  type="button"
                  variant="utility"
                  onClick={() => {
                    const sample = {
                      age: 58,
                      sex: 1,
                      cpAssessment: 'none',
                      exang: 0,
                      trestbps: 130,
                      chol: 240,
                      fbs: 0,
                      restecg: 0,
                      thalach: 150,
                      oldpeak: 1.2,
                      slope: 2,
                      ca: 1,
                      thal: 3
                    };
                    Object.entries(sample).forEach(([k, v]) => handleChange({ target: { name: k, value: v } }));
                  }}
                >
                  Load Sample Data
                </PrimaryButton>
              </div>
            </form>
          </SectionCard>
        </div>

        <ProgressSidebar
          answeredCount={getAnsweredCount()}
          totalCount={fieldOrder.length}
          groups={getGroupProgress()}
          steps={assessmentSteps}
          currentStepIndex={stepIndex + 1}
          onSelectStep={(idx) => goToStep(idx - 1)}
        />
      </div>
    </div>
  );
}
