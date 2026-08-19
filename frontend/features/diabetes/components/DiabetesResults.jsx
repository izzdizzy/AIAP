import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import UnifiedResultsCard from '../../../components/UnifiedResultsCard';

export default function DiabetesResults({
  prediction,
  onResetPrediction,
  onBackToLanding,
  onOpenChat
}) {
  const navigate = useNavigate();
  const { user } = useAuth();

  const handleEdit = onResetPrediction || (() => navigate('/diabetes/assessment'));
  const handleOverview = onBackToLanding || (() => navigate('/'));
  const handleChat = onOpenChat || (() => navigate('/ai-insights'));

  const probability = prediction?.risk_probability ?? 0;
  const riskLabel =
    prediction?.risk_band || prediction?.risk_label || (probability > 0.5 ? 'High' : 'Low');

  return (
    <div className="diabetes-scope w-full">
      <UnifiedResultsCard
        title="Diabetes Assessment Findings"
        probLabel="Diabetes Risk Probability"
        probValue={`${(probability * 100).toFixed(1)}%`}
        riskBadgeLabel={`${riskLabel} Risk`}
        riskLevel={riskLabel}
        factors={prediction?.top_factors || []}
        onOpenChat={handleChat}
        onEditAssessment={handleEdit}
        onBackToOverview={handleOverview}
        isMissingPrediction={!prediction}
        emptyMessage="No diabetes risk prediction found. Please complete the assessment form first."
        user={user}
      />
    </div>
  );
}
