import React from 'react';

/**
 * Reusable Form Stepper Navigation Bar
 * Renders interactive steps with active/completed indicator styling.
 */
export default function FormStepper({
  steps = [],
  currentStepIndex = 0,
  onSelectStep = () => {}
}) {
  if (!steps || steps.length <= 1) return null;

  return (
    <div className="stepper" aria-label="Assessment Form Navigation Steps">
      {steps.filter(step => step.id !== 'intro').map((step, idx) => {
        const stepNum = idx + 1;
        const isActive = stepNum === currentStepIndex;
        const isCompleted = stepNum < currentStepIndex;

        return (
          <button
            key={step.id || stepNum}
            type="button"
            className={`stepper-item ${isActive ? 'stepper-item--active' : ''} ${isCompleted ? 'stepper-item--done' : ''}`}
            onClick={() => onSelectStep(stepNum)}
            disabled={!isCompleted && !isActive}
          >
            <span className="stepper-item__index">{stepNum}</span>
            <span className="stepper-item__text">
              <strong>{step.title}</strong>
            </span>
          </button>
        );
      })}
    </div>
  );
}
