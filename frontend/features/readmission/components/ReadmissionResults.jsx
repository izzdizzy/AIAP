import React from 'react';
import { useNavigate } from 'react-router-dom';
import UnifiedResultsCard from '../../../components/UnifiedResultsCard';

export default function ReadmissionResults({
  prediction,
  onResetPrediction,
  onBackToLanding
}) {
  const navigate = useNavigate();

  const handleEdit = onResetPrediction || (() => navigate('/readmission/assessment'));
  const handleOverview = onBackToLanding || (() => navigate('/'));

  const riskProbPct = prediction?.raw_probability !== undefined
    ? `${(prediction.raw_probability * 100).toFixed(1)}%`
    : '0.0%';

  const riskCat = prediction?.risk_category || 'Standard';
  const pillClass = riskCat.toLowerCase().includes('high')
    ? 'risk-pill--high'
    : riskCat.toLowerCase().includes('mod')
    ? 'risk-pill--moderate'
    : 'risk-pill--low';

  const severityScore = prediction?.clinical_severity_score ?? 0;

  const formattedShap = (prediction?.shap_values || []).map(s => {
    const val = s.shap_value !== undefined ? s.shap_value : s.importance;
    return {
      label: s.feature,
      value: Math.abs(val || 0),
      impact: val,
      shap_value: val,
      direction: val < 0 ? 'negative' : 'positive'
    };
  });

  return (
    <UnifiedResultsCard
      title="Hospital Readmission Risk Findings"
      probLabel="Readmission Probability"
      probValue={riskProbPct}
      riskBadgeLabel={`${riskCat} Risk`}
      pillClass={pillClass}
      severityScore={severityScore}
      factors={formattedShap}
      onOpenChat={() => navigate('/ai-insights')}
      onEditAssessment={handleEdit}
      onBackToOverview={handleOverview}
      isMissingPrediction={!prediction}
      emptyMessage="No readmission risk prediction found. Please complete the assessment form first."
    />
  );
}
