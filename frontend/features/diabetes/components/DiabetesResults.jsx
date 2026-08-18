import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import RiskFactorBreakdown from './RiskFactorBreakdown';

function pillClass(band) {
  const b = (band || '').toLowerCase();
  if (b.includes('high')) return 'dia-pill dia-pill--high';
  if (b.includes('mod')) return 'dia-pill dia-pill--moderate';
  return 'dia-pill dia-pill--low';
}

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

  if (!prediction) {
    return (
      <div className="diabetes-scope page-stack">
        <div className="dia-card" style={{ textAlign: 'center', padding: 'var(--dia-sp-12)' }}>
          <h3 className="dia-section-title" style={{ marginBottom: 'var(--dia-sp-2)' }}>
            No results yet
          </h3>
          <p className="dia-muted" style={{ marginTop: 0, marginBottom: 'var(--dia-sp-5)' }}>
            No diabetes risk prediction found. Please complete the assessment form first.
          </p>
          <button type="button" className="dia-btn" onClick={handleEdit}>
            Go to Assessment
          </button>
        </div>
      </div>
    );
  }

  const probability = prediction.risk_probability ?? 0;
  const riskLabel =
    prediction.risk_band || prediction.risk_label || (probability > 0.5 ? 'High' : 'Low');

  return (
    <div
      className="diabetes-scope page-stack"
      style={{ display: 'flex', flexDirection: 'column', gap: 'var(--dia-sp-6)' }}
    >
      {/* Actions */}
      <div style={{ display: 'flex', gap: 'var(--dia-sp-3)', flexWrap: 'wrap' }}>
        <button type="button" className="dia-btn" onClick={handleChat}>
          Ask the AI Assistant
        </button>
        <button type="button" className="dia-btn dia-btn--ghost" onClick={handleEdit}>
          New Assessment
        </button>
        <button type="button" className="dia-btn dia-btn--ghost" onClick={handleOverview}>
          Back to Dashboard
        </button>
      </div>

      {/* Headline result */}
      <div className="dia-card" style={{ padding: 'var(--dia-sp-10)' }}>
        <p className="dia-eyebrow">Diabetes Assessment Findings</p>
        <div
          style={{
            display: 'flex',
            alignItems: 'baseline',
            gap: 'var(--dia-sp-5)',
            flexWrap: 'wrap',
            marginTop: 'var(--dia-sp-4)'
          }}
        >
          <span className="dia-display-number">{(probability * 100).toFixed(1)}%</span>
          <span className={pillClass(riskLabel)} style={{ transform: 'translateY(-6px)' }}>
            {riskLabel} Risk
          </span>
        </div>
        <p className="dia-muted" style={{ marginTop: 'var(--dia-sp-4)', marginBottom: 0, maxWidth: '52ch' }}>
          This is the model's estimated probability of elevated diabetes risk based on your
          answers. It is a screening aid, not a diagnosis — discuss results with a healthcare
          professional.
        </p>
      </div>

      {/* Guest save prompt */}
      {!user && (
        <div className="dia-guest-banner">
          <span>
            Create a free account to save this result and track your risk over time.
          </span>
          <Link className="dia-link" to="/register">
            Create account →
          </Link>
        </div>
      )}

      {/* Factor breakdown */}
      <div className="dia-card">
        <p className="dia-eyebrow" style={{ marginBottom: 'var(--dia-sp-4)' }}>
          What's Driving This Result
        </p>
        <RiskFactorBreakdown factors={prediction.top_factors} variant="full" />
      </div>

    </div>
  );
}
