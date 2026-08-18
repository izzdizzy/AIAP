import React from 'react';
import PrimaryButton from './PrimaryButton';
import SectionCard from './SectionCard';
import FeatureImportanceBar from './FeatureImportanceBar';

/**
 * Reusable Unified Results Card Component
 * Shared across CAD, Hospital Readmission, and Diabetes Chronic Risk Classifier modules.
 * Features:
 * - Extracted Title above main card
 * - 3-Column CSS Grid summary cards with top-aligned headers for Metric Probability, Risk Badge, and Severity Score
 * - SHAP Feature Importance horizontal bar visualizers
 * - Standardized action buttons (Ask AI Assistant, Edit Inputs, Return to Overview)
 */
export default function UnifiedResultsCard({
  title = 'Assessment Findings',
  probLabel = 'Risk Probability',
  probValue = '0.0%',
  riskBadgeLabel = 'Standard Risk',
  pillClass = 'risk-pill--low',
  severityScore = 0,
  factors = [],
  onOpenChat,
  onEditAssessment,
  onBackToOverview,
  disableChat = false,
  emptyMessage = 'No assessment prediction found. Please complete the assessment form first.',
  isMissingPrediction = false
}) {
  if (isMissingPrediction) {
    return (
      <div className="page-stack">
        <h2 style={{
          fontSize: '22px',
          fontWeight: 700,
          color: 'var(--text)',
          marginTop: '16px',
          marginBottom: '16px',
          letterSpacing: '-0.01em'
        }}>
          {title}
        </h2>
        <SectionCard>
          <div style={{ textAlign: 'center', padding: '32px 16px' }}>
            <p style={{ color: 'var(--text-muted)', marginBottom: '20px', fontSize: '1.05rem' }}>
              {emptyMessage}
            </p>
            {onEditAssessment && (
              <PrimaryButton type="button" variant="primary" onClick={onEditAssessment}>
                Start Assessment
              </PrimaryButton>
            )}
          </div>
        </SectionCard>
      </div>
    );
  }

  return (
    <div className="page-stack">
      {/* Extracted Section Title OUTSIDE and ABOVE Main Container (22px bold) */}
      <h2 style={{
        fontSize: '22px',
        fontWeight: 700,
        color: 'var(--text)',
        marginTop: '16px',
        marginBottom: '16px',
        letterSpacing: '-0.01em'
      }}>
        {title}
      </h2>

      <SectionCard>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '20px' }}>
          {/* Top Summary Bar: 3-Column CSS Grid for Exact Horizontal Label Alignment */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '16px',
            padding: '16px 20px',
            borderRadius: '12px',
            background: 'var(--surface-muted)',
            border: '1px solid var(--border)'
          }}>
            {/* Metric Probability Column */}
            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', alignItems: 'flex-start', gap: '6px' }}>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontWeight: 500, lineHeight: '1.2' }}>
                {probLabel}
              </span>
              <strong style={{ fontSize: '1.6rem', color: 'var(--accent, #38BDF8)', fontWeight: 700, lineHeight: '1.2' }}>
                {probValue}
              </strong>
            </div>

            {/* Risk Badge Column */}
            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', alignItems: 'flex-start', gap: '6px' }}>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontWeight: 500, lineHeight: '1.2' }}>
                Risk Badge
              </span>
              <span className={`risk-pill ${pillClass}`} style={{ marginTop: '2px' }}>
                {riskBadgeLabel}
              </span>
            </div>

            {/* Clinical Severity Score Column */}
            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', alignItems: 'flex-start', gap: '6px' }}>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontWeight: 500, lineHeight: '1.2' }}>
                Clinical Severity Score
              </span>
              <strong style={{ fontSize: '1.3rem', color: 'var(--text)', fontWeight: 700, lineHeight: '1.2' }}>
                {severityScore}/100
              </strong>
            </div>
          </div>

          {/* Body: Contributing Risk Factors / Feature Importance (SHAP horizontal bar visualizer) */}
          <div style={{ padding: '16px 20px', borderRadius: '12px', background: 'var(--surface-muted)', border: '1px solid var(--border)' }}>
            <h3 style={{ margin: '0 0 12px', fontSize: '1.05rem', color: 'var(--text)', fontWeight: 600 }}>
              Contributing Risk Factors (SHAP Feature Importance)
            </h3>
            {factors && factors.length > 0 ? (
              <FeatureImportanceBar factors={factors} />
            ) : (
              <p style={{ color: 'var(--text-muted)', margin: 0 }}>No feature impact factors calculated yet.</p>
            )}
          </div>

          {/* Bottom Action Area: Prominent Ask AI Assistant + Standard Actions */}
          <div style={{
            display: 'flex',
            gap: '12px',
            flexWrap: 'wrap',
            alignItems: 'center',
            paddingTop: '12px',
            borderTop: '1px solid var(--border)'
          }}>
            {onOpenChat && (
              <PrimaryButton
                type="button"
                variant="ai"
                onClick={onOpenChat}
                disabled={disableChat}
              >
                Ask AI Assistant
              </PrimaryButton>
            )}

            {onEditAssessment && (
              <PrimaryButton
                type="button"
                variant="secondary"
                onClick={onEditAssessment}
              >
                Edit Inputs
              </PrimaryButton>
            )}

            {onBackToOverview && (
              <PrimaryButton
                type="button"
                variant="secondary"
                onClick={onBackToOverview}
              >
                Return to Module Overview
              </PrimaryButton>
            )}
          </div>
        </div>
      </SectionCard>
    </div>
  );
}
