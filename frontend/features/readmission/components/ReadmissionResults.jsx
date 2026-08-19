import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import UnifiedResultsCard from '../../../components/UnifiedResultsCard';

export default function ReadmissionResults({
  prediction,
  onResetPrediction,
  onBackToLanding
}) {
  const navigate = useNavigate();
  const { user } = useAuth();

  const handleEdit = onResetPrediction || (() => navigate('/readmission/assessment'));
  const handleOverview = onBackToLanding || (() => navigate('/'));

  const riskProbPct = prediction?.raw_probability !== undefined
    ? `${(prediction.raw_probability * 100).toFixed(1)}%`
    : '0.0%';

  const riskCat = prediction?.risk_category || 'Standard';

  const formattedShap = (prediction?.shap_values || prediction?.top_factors || []).map(s => {
    const val = s.shap_value !== undefined ? s.shap_value : (s.impact !== undefined ? s.impact : s.importance);
    return {
      feature: s.feature,
      label: s.feature,
      impact: val,
      shap_value: val,
      value: Math.abs(val || 0)
    };
  });

  return (
    <UnifiedResultsCard
      title="Hospital Readmission Risk Findings"
      probLabel="Readmission Probability"
      probValue={riskProbPct}
      riskBadgeLabel={`${riskCat} Risk`}
      riskLevel={riskCat}
      factors={formattedShap}
      onOpenChat={() => navigate('/ai-insights')}
      onEditAssessment={handleEdit}
      onBackToOverview={handleOverview}
      isMissingPrediction={!prediction}
      emptyMessage="No readmission risk prediction found. Please complete the assessment form first."
      user={user}
    />
  );
}
