import React from 'react';
import { useNavigate } from 'react-router-dom';
import UnifiedResultsCard from '../../../components/UnifiedResultsCard';

export default function DiabetesResults({
  prediction,
  onResetPrediction,
  onBackToLanding,
  onOpenChat
}) {
  const navigate = useNavigate();

  const handleEdit = onResetPrediction || (() => navigate('/diabetes/assessment'));
  const handleOverview = onBackToLanding || (() => navigate('/'));
  const handleChat = onOpenChat || (() => navigate('/ai-insights'));

  const riskProbPct = prediction?.risk_probability !== undefined
    ? `${(prediction.risk_probability * 100).toFixed(1)}%`
    : '0.0%';

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
    const imp = f.impact ?? f.shap_value ?? f.importance ?? 0.2;
    return {
      label: f.feature || f.name || 'Factor',
      value: Math.abs(imp),
      impact: imp,
      shap_value: imp,
      direction: imp < 0 ? 'negative' : 'positive'
    };
  });

  return (
    <UnifiedResultsCard
      title="Diabetes Assessment Findings"
      probLabel="Risk Probability"
      probValue={riskProbPct}
      riskBadgeLabel={`${riskLabel}`}
      pillClass={pillClass}
      severityScore={severityScore}
      factors={formattedFactors}
      onOpenChat={handleChat}
      onEditAssessment={handleEdit}
      onBackToOverview={handleOverview}
      isMissingPrediction={!prediction}
      emptyMessage="No diabetes risk prediction found. Please complete the assessment form first."
    />
  );
}
