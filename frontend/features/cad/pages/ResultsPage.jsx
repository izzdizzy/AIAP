import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import UnifiedResultsCard from '../../../components/UnifiedResultsCard';
import { formatPercent } from '../utils/risk';

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
  const navigate = useNavigate();
  const { user } = useAuth();
  const displayResult = assessmentState?.prediction ?? emptyResult;

  const handleChat = onOpenChat || (() => navigate('/ai-insights'));
  const handleEdit = onEditAssessment || (() => navigate('/cad/assessment'));
  const handleOverview = onRestart || (() => navigate('/'));

  const riskProbPct = assessmentState
    ? displayResult.riskPercent
    : formatPercent(displayResult.riskProbability);

  const formattedFactors = (displayResult.topFactors || []).map((f) => ({
    feature: f.feature,
    label: f.feature,
    impact: f.impact,
    value: Math.abs(f.impact || 0.2)
  }));

  return (
    <UnifiedResultsCard
      title="CAD Screening Results"
      probLabel="CAD Metric Probability"
      probValue={riskProbPct}
      riskBadgeLabel={`${displayResult.riskLevel || 'Low'} Risk`}
      riskLevel={displayResult.riskLevel || 'Low'}
      factors={formattedFactors}
      onOpenChat={handleChat}
      onEditAssessment={handleEdit}
      onBackToOverview={handleOverview}
      disableChat={!assessmentState?.prediction}
      isMissingPrediction={!assessmentState?.prediction}
      emptyMessage="No CAD screening prediction found. Please complete the assessment form first."
      user={user}
    />
  );
}

