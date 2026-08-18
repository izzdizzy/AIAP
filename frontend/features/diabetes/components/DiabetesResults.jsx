import React from 'react';
import { useNavigate } from 'react-router-dom';
import PrimaryButton from '../../../components/PrimaryButton';
import SectionCard from '../../../components/SectionCard';
import FeatureImportanceBar from '../../../components/FeatureImportanceBar';

export default function DiabetesResults({
  prediction,
  onResetPrediction,
  onBackToLanding,
  onOpenChat
}) {
  const navigate = useNavigate();

  const handleEdit = onResetPrediction || (() => navigate('/diabetes/assessment'));
  const handleOverview = onBackToLanding || (() => navigate('/'));
  const handleChat = onOpenChat || (() => navigate('/cad/chat'));

  if (!prediction) {
    return (
      <div className="page-stack">
        <h2 style={{
          fontSize: '22px',
          fontWeight: 700,
          color: '#F8FAFC',
          marginTop: '16px',
          marginBottom: '16px',
          letterSpacing: '-0.01em'
        }}>
          Diabetes Assessment Findings
        </h2>
        <SectionCard>
          <div style={{ textAlign: 'center', padding: '32px 16px' }}>
            <p style={{ color: '#94A3B8', marginBottom: '20px', fontSize: '1.05rem' }}>
              No diabetes risk prediction found. Please complete the assessment form first.
            </p>
            <PrimaryButton
              type="button"
              variant="primary"
              onClick={() => navigate('/diabetes/assessment')}
            >
              Start Diabetes Assessment
            </PrimaryButton>
          </div>
        </SectionCard>
      </div>
    );
  }

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
      return { label: f, value: 0.5, impact: 0.2, direction: 'positive' };
    }
    const imp = f.importance ?? f.impact ?? 0.2;
    return {
      label: f.feature || f.name || 'Factor',
      value: Math.abs(imp),
      impact: imp,
      direction: imp < 0 ? 'negative' : 'positive'
    };
  });

  return (
    <div className="page-stack">
      {/* Extracted Form Section Title OUTSIDE and ABOVE Main Container (22px bold #F8FAFC, min 16px gap) */}
      <h2 style={{
        fontSize: '22px',
        fontWeight: 700,
        color: '#F8FAFC',
        marginTop: '16px',
        marginBottom: '16px',
        letterSpacing: '-0.01em'
      }}>
        Diabetes Assessment Findings
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
              onClick={handleChat}
            >
              Ask AI Assistant
            </PrimaryButton>

            <PrimaryButton
              type="button"
              variant="secondary"
              onClick={handleEdit}
            >
              ← Edit Inputs
            </PrimaryButton>

            <PrimaryButton
              type="button"
              variant="secondary"
              onClick={handleOverview}
            >
              Return to Module Overview
            </PrimaryButton>
          </div>
        </div>
      </SectionCard>
    </div>
  );
}
