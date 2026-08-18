import React from 'react';
import { useNavigate } from 'react-router-dom';
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
  const displayResult = assessmentState?.prediction ?? emptyResult;

  const handleChat = onOpenChat || (() => navigate('/cad/chat'));
  const handleEdit = onEditAssessment || (() => navigate('/cad/assessment'));
  const handleOverview = onRestart || (() => navigate('/'));

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
    impact: f.impact,
    direction: f.impact < 0 ? 'negative' : 'positive'
  }));

  return (
    <UnifiedResultsCard
      title="CAD Screening Results"
      probLabel="Metric Probability"
      probValue={riskProbPct}
      riskBadgeLabel={`${displayResult.riskLevel} Risk`}
      pillClass={pillClass}
      severityScore={severityScore}
      factors={formattedFactors}
      onOpenChat={handleChat}
      onEditAssessment={handleEdit}
      onBackToOverview={handleOverview}
      disableChat={!assessmentState?.prediction}
      isMissingPrediction={!assessmentState?.prediction}
      emptyMessage="No CAD screening prediction found. Please complete the assessment form first."
    />
  );
}

