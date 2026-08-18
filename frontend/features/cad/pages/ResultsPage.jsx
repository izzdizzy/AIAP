import PrimaryButton from '../../../components/PrimaryButton';
import SectionCard from '../../../components/SectionCard';
import FeatureImportanceBar from '../../../components/FeatureImportanceBar';
import { describeFactorDirection, formatPercent } from '../utils/risk';

const emptyResult = {
  riskProbability: 0,
  riskPercent: '0.0%',
  riskLevel: 'Low',
  topFactors: []
};

export default function ResultsPage({
  assessmentState,
  onRestart,
  onEditAssessment,
  onOpenChat
}) {
  const displayResult = assessmentState?.prediction ?? emptyResult;

  const riskLevelText = (displayResult.riskLevel || 'Low').toLowerCase();
  const pillClass = riskLevelText.includes('high')
    ? 'risk-pill--high'
    : riskLevelText.includes('mod')
    ? 'risk-pill--moderate'
    : 'risk-pill--low';

  const riskProbPct = assessmentState
    ? displayResult.riskPercent
    : formatPercent(displayResult.riskProbability);

  const severityScore = displayResult.riskProbability !== undefined
    ? Math.round(displayResult.riskProbability * 100)
    : 0;

  const formattedFactors = (displayResult.topFactors || []).map((f) => ({
    label: f.feature,
    value: Math.abs(f.impact || 0.2),
    displayValue: `${describeFactorDirection(f.direction)} (${f.impact > 0 ? '+' : ''}${f.impact})`,
    direction: f.impact < 0 ? 'negative' : 'positive'
  }));

  return (
    <div className="page-stack">
      {/* Extracted Section Title OUTSIDE and ABOVE Main Card (22px bold #F8FAFC) */}
      <h2 style={{
        fontSize: '22px',
        fontWeight: 700,
        color: '#F8FAFC',
        marginBottom: '12px',
        letterSpacing: '-0.01em'
      }}>
        CAD Screening Results
      </h2>

      <SectionCard>
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
              <span style={{ fontSize: '0.82rem', color: '#94A3B8', display: 'block' }}>Metric Probability</span>
              <strong style={{ fontSize: '1.6rem', color: '#38BDF8', fontWeight: 700 }}>{riskProbPct}</strong>
            </div>

            <div>
              <span style={{ fontSize: '0.82rem', color: '#94A3B8', display: 'block' }}>Risk Badge</span>
              <span className={`risk-pill ${pillClass}`}>
                {displayResult.riskLevel} Risk
              </span>
            </div>

            <div>
              <span style={{ fontSize: '0.82rem', color: '#94A3B8', display: 'block' }}>Clinical Severity Score</span>
              <strong style={{ fontSize: '1.3rem', color: '#F8FAFC', fontWeight: 700 }}>{severityScore}/100</strong>
            </div>
          </div>

          {/* Body: Contributing Risk Factors / Feature Importance (SHAP horizontal bar visualizer) */}
          <div style={{ padding: '16px 20px', borderRadius: '12px', background: '#1E293B', border: '1px solid #334155' }}>
            <h3 style={{ margin: '0 0 12px', fontSize: '1.05rem', color: '#F8FAFC', fontWeight: 600 }}>
              Contributing Risk Factors (SHAP Feature Importance)
            </h3>
            {formattedFactors.length ? (
              <FeatureImportanceBar factors={formattedFactors} />
            ) : (
              <p style={{ color: '#94A3B8' }}>No model factors available yet.</p>
            )}
          </div>

          {/* Bottom Action Area: Prominent Ask AI Assistant + Standardized Navigation */}
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
              onClick={onOpenChat}
              disabled={!assessmentState?.prediction}
            >
              Ask AI Assistant
            </PrimaryButton>

            <PrimaryButton
              type="button"
              variant="secondary"
              onClick={onEditAssessment}
            >
              ← Edit Inputs
            </PrimaryButton>

            <PrimaryButton
              type="button"
              variant="secondary"
              onClick={onRestart}
            >
              Return to Module Overview
            </PrimaryButton>
          </div>
        </div>
      </SectionCard>
    </div>
  );
}

