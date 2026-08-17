import Disclaimer from '../components/Disclaimer';
import PrimaryButton from '../components/PrimaryButton';
import ResultCard from '../components/ResultCard';
import SectionCard from '../components/SectionCard';
import { describeFactorDirection, formatPercent, getLifestyleAdvice } from '../utils/risk';

const emptyResult = {
  riskProbability: 0,
  riskPercent: '0.0%',
  riskLevel: 'Awaiting result',
  topFactors: [],
  lifestyleAdvice: getLifestyleAdvice('Low')
};

export default function ResultsPage({
  assessmentState,
  onRestart,
  onEditAssessment,
  onOpenChat
}) {
  const displayResult =
    assessmentState?.prediction ?? emptyResult;
  return (
    <div className="page-stack">
      <SectionCard title="Results" description="Placeholder result view for the prototype stage.">
        <div className="results-summary">
          <div className="results-summary__metric">
            <span className="results-summary__label">Risk Probability</span>
            <strong>{
              assessmentState
                ? displayResult.riskPercent
                : formatPercent(displayResult.riskProbability)
            }</strong>
          </div>
          <div className="results-summary__metric">
            <span className="results-summary__label">Risk Level</span>
            <strong>{displayResult.riskLevel}</strong>
          </div>
        </div>

        <div className="results-layout">
          <ResultCard title="Top Contributing Factors">
            {displayResult.topFactors.length ? (
              <ul className="result-list">
                {displayResult.topFactors.map((factor) => (
                  <li key={factor.feature}>
                    <span>{factor.feature}</span>
                    <small>{describeFactorDirection(factor.direction)} {factor.impact > 0 ? `+${factor.impact}` : factor.impact}</small>
                  </li>
                ))}
              </ul>
            ) : (
              <p>No model factors available yet.</p>
            )}
          </ResultCard>

          <ResultCard title="AI Lifestyle Advice">
            <ul className="result-list">
              {displayResult.lifestyleAdvice.map((advice) => (
                <li key={advice}>{advice}</li>
              ))}
            </ul>
          </ResultCard>
        </div>

        <ResultCard title="Medical Disclaimer" tone="neutral">
          <p>{displayResult.medicalDisclaimer ?? 'This result is for screening only and does not replace professional medical advice.'}</p>
        </ResultCard>

        <div className="form-actions form-actions--results">
          <PrimaryButton type="button" variant="ghost" onClick={onEditAssessment}>
            Edit Assessment
          </PrimaryButton>
          <PrimaryButton type="button" onClick={onRestart}>
            Return Home
          </PrimaryButton>
        </div>
        <div>
          <PrimaryButton
            type="button"
            onClick={onOpenChat}
            disabled={!assessmentState?.prediction}
          >
            Open AI Chat
          </PrimaryButton>
        </div>
      </SectionCard>

      <Disclaimer compact />
    </div>
  );
}
