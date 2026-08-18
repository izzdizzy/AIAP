import Disclaimer from '../components/Disclaimer';
import PrimaryButton from '../components/PrimaryButton';
import ResultCard from '../components/ResultCard';
import SectionCard from '../components/SectionCard';
import FeatureImportanceBar from '../components/FeatureImportanceBar';
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

  const riskLevelText = (displayResult.riskLevel || 'Low').toLowerCase();
  const pillClass = riskLevelText.includes('high')
    ? 'risk-pill--high'
    : riskLevelText.includes('mod')
    ? 'risk-pill--moderate'
    : 'risk-pill--low';

  const formattedFactors = (displayResult.topFactors || []).map((f) => ({
    label: f.feature,
    value: Math.abs(f.impact || 0.2),
    displayValue: `${describeFactorDirection(f.direction)} (${f.impact > 0 ? '+' : ''}${f.impact})`,
    direction: f.impact < 0 ? 'negative' : 'positive'
  }));

  return (
    <div className="page-stack">
      <SectionCard title="CAD Screening Results" description="AI model evaluation based on patient clinical parameters.">
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
            <div>
              <span className={`risk-pill ${pillClass}`}>
                {displayResult.riskLevel} Risk
              </span>
            </div>
          </div>
        </div>

        <div className="results-layout">
          <ResultCard title="Top Contributing Factors">
            {formattedFactors.length ? (
              <FeatureImportanceBar factors={formattedFactors} />
            ) : (
              <p>No model factors available yet.</p>
            )}
          </ResultCard>

          <ResultCard title="AI Lifestyle Guidance">
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

        <div className="form-actions form-actions--results" style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '16px' }}>
          <PrimaryButton type="button" variant="ghost" onClick={onEditAssessment}>
            Edit Form Inputs
          </PrimaryButton>
          <PrimaryButton type="button" onClick={onRestart}>
            Return Home
          </PrimaryButton>
          <PrimaryButton
            type="button"
            onClick={onOpenChat}
            disabled={!assessmentState?.prediction}
          >
            Ask AI Assistant
          </PrimaryButton>
        </div>
      </SectionCard>

      <Disclaimer compact />
    </div>
  );
}
