import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  getHistory,
  deleteAssessment,
  getModuleHistory,
  deleteModuleAssessment
} from '../features/diabetes/services/historyApi';
import RiskTrendChart from '../features/diabetes/components/RiskTrendChart';
import HistoryList from '../features/diabetes/components/HistoryList';

/**
 * Dashboard (Landing Page) - Healthcare Risk Assessment Portal
 *
 * Two tabs: Modules (assessment picker) and History (per-module saved
 * assessments for the signed-in user, with a compact summary strip and a
 * clickable, expandable log).
 */

const MODULES = [
  {
    key: 'cad',
    title: 'CAD Risk Assessment',
    accent: '#3b82f6',
    icon: (
      <svg style={{ width: '24px', height: '24px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
      </svg>
    ),
    description: 'Coronary artery disease is the single biggest cause of death. Estimate your risk with or without clinical information.',
    cta: 'Start CAD Assessment'
  },
  {
    key: 'readmission',
    title: 'Hospital Readmission Predictor',
    accent: '#10b981',
    icon: (
      <svg style={{ width: '24px', height: '24px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
    ),
    description: 'Have you been admitted to the hospital? Check your risk of being readmitted within 30 days based on your admission and medical history.',
    cta: 'Start Readmission Assessment'
  },
  {
    key: 'diabetes',
    title: 'Diabetes Risk Classifier',
    accent: '#0f766e',
    icon: (
      <svg style={{ width: '24px', height: '24px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    description: 'Are you at risk of Diabetes? Check your risk here with your characteristics and lifestyle behaviour.',
    cta: 'Start Diabetes Assessment'
  },
  {
    key: 'ai',
    title: 'AI Insights Workspace',
    accent: '#8b5cf6',
    icon: <span style={{ fontSize: '20px' }}>✨</span>,
    description: 'Interactive 3-chatbot workspace: CAD Lifestyle Coach, SHAP Diabetes Explainer, and Care Navigator.',
    cta: 'Open AI Insights Workspace'
  }
];

const HISTORY_CATEGORIES = [
  { key: 'diabetes', label: 'Diabetes' },
  { key: 'cad', label: 'CAD' },
  { key: 'readmission', label: 'Readmission' }
];

function pillClass(band) {
  const b = (band || '').toLowerCase();
  if (b.includes('high')) return 'dia-pill dia-pill--high';
  if (b.includes('mod')) return 'dia-pill dia-pill--moderate';
  return 'dia-pill dia-pill--low';
}

function normalizeDiabetesRow(row) {
  return {
    id: row.id,
    created_at: row.created_at,
    probability: row.risk_probability ?? null,
    band: row.risk_band || null,
    label: row.risk_label || null,
    factors: row.top_factors || [],
    inputs: row.profile || {}
  };
}

function normalizeGenericRow(row) {
  const r = row.result || {};
  const probability =
    r.risk_probability ?? r.raw_probability ?? r.riskProbability ?? null;
  const band = r.risk_band ?? r.risk_category ?? r.riskLevel ?? null;
  return {
    id: row.id,
    created_at: row.created_at,
    probability,
    band,
    label: r.risk_label ?? (band ? `${band} Risk` : null),
    factors: r.top_factors ?? r.shap_values ?? r.topFactors ?? [],
    inputs: row.payload || {}
  };
}

function ModuleCard({ module, onOpen }) {
  return (
    <div
      className="dia-card"
      onClick={onOpen}
      style={{
        cursor: 'pointer',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--dia-sp-4)',
        transition: 'border-color 180ms ease, transform 180ms ease'
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = module.accent;
        e.currentTarget.style.transform = 'translateY(-2px)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--dia-border)';
        e.currentTarget.style.transform = 'translateY(0)';
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--dia-sp-3)' }}>
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: 'var(--dia-radius-sm)',
          background: module.accent,
          color: 'white',
          display: 'grid',
          placeItems: 'center',
          flexShrink: 0
        }}>
          {module.icon}
        </div>
        <h2 className="dia-section-title">{module.title}</h2>
      </div>
      <p className="dia-muted" style={{ margin: 0, flex: 1 }}>{module.description}</p>
      <button
        type="button"
        onClick={(e) => { e.stopPropagation(); onOpen(); }}
        style={{
          width: '100%',
          padding: '10px 16px',
          background: 'transparent',
          color: module.accent,
          border: `1px solid ${module.accent}`,
          borderRadius: 'var(--dia-radius-sm)',
          fontWeight: 600,
          fontSize: '0.9rem',
          cursor: 'pointer',
          transition: 'background-color 180ms ease, color 180ms ease'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = module.accent;
          e.currentTarget.style.color = 'white';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'transparent';
          e.currentTarget.style.color = module.accent;
        }}
      >
        {module.cta}
      </button>
    </div>
  );
}

export default function LandingPage({ onStartCADAssessment, onStartReadmissionAssessment, onStartDiabetesAssessment }) {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [tab, setTab] = useState('modules');
  const [category, setCategory] = useState('diabetes');
  const [histories, setHistories] = useState({ diabetes: null, cad: null, readmission: null });
  const [historyError, setHistoryError] = useState(null);

  const moduleHandlers = {
    cad: onStartCADAssessment || (() => navigate('/cad/assessment')),
    readmission: onStartReadmissionAssessment || (() => navigate('/readmission/assessment')),
    diabetes: onStartDiabetesAssessment || (() => navigate('/diabetes/assessment')),
    ai: () => navigate('/ai-insights')
  };

  useEffect(() => {
    if (!user) {
      setHistories({ diabetes: null, cad: null, readmission: null });
      return;
    }
    let cancelled = false;
    Promise.all([
      getHistory().catch(() => []),
      getModuleHistory('cad').catch(() => []),
      getModuleHistory('readmission').catch(() => [])
    ]).then(([diabetesRows, cadRows, readmissionRows]) => {
      if (cancelled) return;
      setHistories({
        diabetes: diabetesRows.map(normalizeDiabetesRow),
        cad: cadRows.map(normalizeGenericRow),
        readmission: readmissionRows.map(normalizeGenericRow)
      });
    });
    return () => {
      cancelled = true;
    };
  }, [user]);

  async function handleDelete(id) {
    try {
      if (category === 'diabetes') {
        await deleteAssessment(id);
      } else {
        await deleteModuleAssessment(category, id);
      }
      setHistories((prev) => ({
        ...prev,
        [category]: (prev[category] || []).filter((row) => row.id !== id)
      }));
    } catch (err) {
      setHistoryError(err.message || 'Failed to delete the assessment.');
    }
  }

  const entries = histories[category] || [];
  const loaded = histories.diabetes !== null;
  const latest = entries[0] || null;
  const previous = entries[1] || null;
  const trendDelta =
    latest?.probability != null && previous?.probability != null
      ? Math.round((latest.probability - previous.probability) * 1000) / 10
      : null;
  const trendRows = entries
    .filter((e) => e.probability != null)
    .map((e) => ({ created_at: e.created_at, risk_probability: e.probability }));

  const memberSince = user?.created_at
    ? new Date(user.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'long' })
    : null;

  return (
    <div className="diabetes-scope page-stack" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--dia-sp-6)' }}>
      {/* Hero / greeting */}
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--dia-sp-4)' }}>
        <div>
          <p className="dia-eyebrow">Healthcare Risk Assessment Portal</p>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 600, letterSpacing: '-0.01em', margin: '8px 0 4px' }}>
            {user ? `Welcome back, ${user.name?.split(' ')[0] || 'there'}` : 'Your health, clearly assessed'}
          </h2>
          <p className="dia-muted" style={{ margin: 0 }}>
            {user
              ? (memberSince ? `Member since ${memberSince}` : 'Your saved assessments are in the History tab.')
              : 'Select a module below to begin a clinical risk assessment.'}
          </p>
        </div>
        {!user && (
          <div style={{ display: 'flex', gap: 'var(--dia-sp-3)' }}>
            <Link
              to="/login"
              className="dia-btn"
              style={{ textDecoration: 'none', background: '#1e3a8a', borderColor: '#1e3a8a' }}
            >
              Sign in
            </Link>
            <Link to="/register" className="dia-btn" style={{ textDecoration: 'none' }}>
              Create account
            </Link>
          </div>
        )}
      </div>

      {/* Modules / History toggle */}
      <div className="dia-segmented" role="tablist" style={{ alignSelf: 'flex-start' }}>
        <button
          type="button"
          role="tab"
          aria-selected={tab === 'modules'}
          className={tab === 'modules' ? 'active' : ''}
          onClick={() => setTab('modules')}
        >
          Modules
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === 'history'}
          className={tab === 'history' ? 'active' : ''}
          onClick={() => setTab('history')}
        >
          History
        </button>
      </div>

      {/* ---- Modules tab ---- */}
      {tab === 'modules' && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: 'var(--dia-sp-5)'
        }}>
          {MODULES.map((module) => (
            <ModuleCard
              key={module.key}
              module={module}
              onOpen={moduleHandlers[module.key]}
            />
          ))}
        </div>
      )}

      {/* ---- History tab ---- */}
      {tab === 'history' && !user && (
        <div className="dia-card" style={{ textAlign: 'center', padding: 'var(--dia-sp-12)' }}>
          <h3 className="dia-section-title" style={{ marginBottom: 'var(--dia-sp-2)' }}>
            Sign in to see your assessment history
          </h3>
          <p className="dia-muted" style={{ marginTop: 0, marginBottom: 'var(--dia-sp-5)' }}>
            Your assessments are saved to your account automatically and tracked over time.
          </p>
          <div style={{ display: 'flex', gap: 'var(--dia-sp-3)', justifyContent: 'center' }}>
            <Link
              to="/login"
              className="dia-btn"
              style={{ textDecoration: 'none', background: '#1e3a8a', borderColor: '#1e3a8a' }}
            >
              Sign in
            </Link>
            <Link to="/register" className="dia-btn" style={{ textDecoration: 'none' }}>
              Create account
            </Link>
          </div>
        </div>
      )}

      {tab === 'history' && user && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--dia-sp-4)' }}>
          {/* Category selector */}
          <div className="dia-segmented" role="tablist" style={{ alignSelf: 'flex-start' }}>
            {HISTORY_CATEGORIES.map((cat) => {
              const count = (histories[cat.key] || []).length;
              return (
                <button
                  key={cat.key}
                  type="button"
                  role="tab"
                  aria-selected={category === cat.key}
                  className={category === cat.key ? 'active' : ''}
                  onClick={() => setCategory(cat.key)}
                >
                  {cat.label}{count > 0 ? ` (${count})` : ''}
                </button>
              );
            })}
          </div>

          {historyError && <div className="dia-error" role="alert">{historyError}</div>}

          {!loaded && <p className="dia-muted">Loading your assessments…</p>}

          {loaded && (
            <>
              {/* Compact summary strip */}
              {latest && (
                <div
                  className="dia-card"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: 'var(--dia-sp-6)',
                    padding: 'var(--dia-sp-4) var(--dia-sp-5)'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--dia-sp-3)' }}>
                    <span className="dia-eyebrow">Latest</span>
                    <span style={{ fontSize: '1.3rem', fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
                      {latest.probability != null ? `${(latest.probability * 100).toFixed(1)}%` : '—'}
                    </span>
                    {latest.band && <span className={pillClass(latest.band)}>{latest.band}</span>}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--dia-sp-2)' }}>
                    <span className="dia-eyebrow">Total</span>
                    <span style={{ fontSize: '1.05rem', fontWeight: 600 }}>{entries.length}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--dia-sp-2)' }}>
                    <span className="dia-eyebrow">Trend</span>
                    {trendDelta === null ? (
                      <span className="dia-muted" style={{ fontSize: '0.85rem' }}>—</span>
                    ) : (
                      <span
                        style={{
                          fontSize: '1.05rem',
                          fontWeight: 600,
                          fontVariantNumeric: 'tabular-nums',
                          color:
                            trendDelta < 0
                              ? 'var(--risk-low-text, #16a34a)'
                              : trendDelta > 0
                              ? 'var(--risk-high-text, #dc2626)'
                              : 'var(--dia-text)'
                        }}
                      >
                        {trendDelta > 0 ? '+' : ''}{trendDelta}%
                      </span>
                    )}
                  </div>
                  {trendRows.length >= 2 && (
                    <div style={{ flex: 1, minWidth: '240px' }}>
                      <RiskTrendChart history={trendRows} height={90} />
                    </div>
                  )}
                </div>
              )}

              {/* History log — the main content */}
              <HistoryList entries={entries} onDelete={handleDelete} />
            </>
          )}
        </div>
      )}
    </div>
  );
}
