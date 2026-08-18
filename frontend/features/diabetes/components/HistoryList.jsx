import React, { useState } from 'react';
import RiskFactorBreakdown from './RiskFactorBreakdown';

function pillClass(band) {
  const b = (band || '').toLowerCase();
  if (b.includes('high')) return 'dia-pill dia-pill--high';
  if (b.includes('mod')) return 'dia-pill dia-pill--moderate';
  return 'dia-pill dia-pill--low';
}

function formatDateTime(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  }) + ' · ' + d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}

function DetailModal({ entry, onClose }) {
  return (
    <div
      className="dia-modal-overlay"
      role="dialog"
      aria-modal="true"
      onClick={onClose}
    >
      <div className="dia-modal" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 'var(--dia-sp-4)' }}>
          <div>
            <p className="dia-eyebrow">Assessment Details</p>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--dia-sp-3)', marginTop: '8px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '1.5rem', fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
                {entry.probability !== null && entry.probability !== undefined
                  ? `${(entry.probability * 100).toFixed(1)}%`
                  : '—'}
              </span>
              {entry.band && <span className={pillClass(entry.band)}>{entry.band}</span>}
            </div>
            <p className="dia-muted" style={{ margin: '6px 0 0', fontSize: '0.82rem' }}>
              {formatDateTime(entry.created_at)}
            </p>
          </div>
          <button type="button" className="dia-modal-close" onClick={onClose}>
            Close ✕
          </button>
        </div>

        <div>
          <p className="dia-eyebrow" style={{ marginBottom: 'var(--dia-sp-3)' }}>
            Contributing Factors
          </p>
          {(entry.factors || []).length > 0 ? (
            <RiskFactorBreakdown factors={entry.factors} variant="full" />
          ) : (
            <p className="dia-muted" style={{ margin: 0 }}>
              No factor details were recorded for this assessment.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Clickable assessment log. Entries are normalized:
 * { id, created_at, probability (0-1|null), band, label, factors, inputs }
 * Clicking a row opens a popup with that assessment's contributing factors.
 */
export default function HistoryList({ entries, onDelete }) {
  const [selected, setSelected] = useState(null);

  if (!entries || entries.length === 0) {
    return (
      <div className="dia-card" style={{ textAlign: 'center', padding: 'var(--dia-sp-10)' }}>
        <p className="dia-muted" style={{ margin: 0 }}>
          No saved assessments yet. Complete an assessment while signed in and it will appear here.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="dia-card" style={{ padding: 0 }}>
        {entries.map((entry) => (
          <div
            key={entry.id}
            className="dia-history-row"
            role="button"
            tabIndex={0}
            onClick={() => setSelected(entry)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                setSelected(entry);
              }
            }}
            style={{ cursor: 'pointer' }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              <span style={{ fontSize: '0.88rem', fontWeight: 600 }}>
                {formatDateTime(entry.created_at)}
              </span>
              <span className="dia-muted" style={{ fontSize: '0.78rem' }}>
                {entry.label || ''}
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--dia-sp-4)' }}>
              <span style={{ fontSize: '1rem', fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
                {entry.probability !== null && entry.probability !== undefined
                  ? `${(entry.probability * 100).toFixed(1)}%`
                  : '—'}
              </span>
              {entry.band && <span className={pillClass(entry.band)}>{entry.band}</span>}
              <button
                type="button"
                className="dia-delete-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  if (window.confirm('Delete this assessment from your history?')) {
                    onDelete(entry.id);
                  }
                }}
              >
                Delete
              </button>
              <span className="dia-muted" aria-hidden="true" style={{ fontSize: '0.78rem' }}>
                View →
              </span>
            </div>
          </div>
        ))}
      </div>

      {selected && <DetailModal entry={selected} onClose={() => setSelected(null)} />}
    </>
  );
}
