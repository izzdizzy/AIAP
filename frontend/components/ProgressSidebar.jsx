import React from 'react';

/**
 * Reusable Integrated Progress & Stepper Sidebar
 * Features:
 * - Top Section: Total completion bar
 * - Stepper List: Integrated step items with step numbers/checkmarks and completion counters inside each pill (e.g. "1. Personal Info (2/2)")
 */
export default function ProgressSidebar({
  answeredCount = 0,
  totalCount = 0,
  groups = [],
  steps = [],
  currentStepIndex = 1,
  onSelectStep = null
}) {
  const percentage = totalCount > 0 ? Math.min(100, Math.round((answeredCount / totalCount) * 100)) : 0;
  const validSteps = steps.filter(s => s.id !== 'intro');

  return (
    <aside className="assessment-progress" aria-label="Form Progress Sidebar">
      <div className="section-card" style={{ padding: '20px' }}>
        <h3 style={{ margin: '0 0 16px', fontSize: '1.05rem', fontWeight: 600, color: 'var(--text)' }}>
          Form Progress
        </h3>

        {/* Top Section: Total Counter with Subtle Progress Bar Background */}
        <div style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Completion</span>
            <span style={{ fontSize: '0.88rem', fontWeight: '700', color: 'var(--accent, #14B8A6)' }}>
              {answeredCount} of {totalCount} completed ({percentage}%)
            </span>
          </div>
          <div style={{
            width: '100%',
            height: '8px',
            borderRadius: '999px',
            background: 'var(--surface-muted)',
            border: '1px solid var(--border)',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${percentage}%`,
              height: '100%',
              background: 'var(--accent, #14B8A6)',
              borderRadius: '999px',
              transition: 'width 0.3s ease'
            }} />
          </div>
        </div>

        {/* Integrated Stepper List with Completion Counters in Pills */}
        {validSteps.length > 0 && (
          <div style={{ display: 'grid', gap: '8px' }}>
            {validSteps.map((step, idx) => {
              const stepNum = idx + 1;
              const isActive = stepNum === currentStepIndex;
              const isCompleted = stepNum < currentStepIndex;
              const isPending = stepNum > currentStepIndex;

              const stepAnswered = step.answeredCount ?? groups[idx]?.answeredCount ?? 0;
              const stepTotal = step.totalCount ?? groups[idx]?.totalCount ?? 0;
              const isStepComplete = stepTotal > 0 && stepAnswered === stepTotal;

              return (
                <button
                  key={step.id || stepNum}
                  type="button"
                  onClick={() => onSelectStep?.(stepNum)}
                  disabled={!onSelectStep}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '12px',
                    padding: '10px 12px',
                    borderRadius: '12px',
                    border: isActive
                      ? '1px solid var(--accent, #14B8A6)'
                      : isCompleted
                      ? '1px solid var(--risk-low-border, rgba(45, 212, 191, 0.3))'
                      : '1px solid var(--border)',
                    background: isActive
                      ? 'var(--surface-muted)'
                      : isCompleted
                      ? 'var(--risk-low-bg, rgba(20, 184, 166, 0.1))'
                      : 'var(--surface)',
                    color: isPending ? 'var(--text-muted)' : 'var(--text)',
                    cursor: onSelectStep ? 'pointer' : 'default',
                    textAlign: 'left',
                    width: '100%',
                    fontSize: '0.85rem',
                    boxShadow: isActive ? '0 0 0 1px var(--accent, #14B8A6)' : 'none',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
                    <span style={{
                      width: '24px',
                      height: '24px',
                      borderRadius: '50%',
                      background: isCompleted
                        ? 'var(--accent, #14B8A6)'
                        : isActive
                        ? 'transparent'
                        : 'var(--surface-muted)',
                      color: isCompleted ? '#ffffff' : isActive ? 'var(--accent, #14B8A6)' : 'var(--text-muted)',
                      border: isActive ? '2px solid var(--accent, #14B8A6)' : '1px solid var(--border)',
                      display: 'grid',
                      placeItems: 'center',
                      fontWeight: 700,
                      fontSize: '0.78rem',
                      flex: '0 0 auto'
                    }}>
                      {isCompleted ? '✓' : stepNum}
                    </span>
                    <span style={{
                      fontWeight: isActive ? 600 : 500,
                      color: isActive ? 'var(--text)' : isPending ? 'var(--text-muted)' : 'var(--text)',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}>
                      {step.title}
                    </span>
                  </div>

                  {stepTotal > 0 && (
                    <span style={{
                      marginLeft: 'auto',
                      fontWeight: 700,
                      fontSize: '0.78rem',
                      padding: '2px 8px',
                      borderRadius: '999px',
                      background: isStepComplete ? 'var(--risk-low-bg, rgba(20, 184, 166, 0.15))' : 'var(--surface-muted)',
                      color: isStepComplete ? 'var(--risk-low-text, #2DD4BF)' : 'var(--text-muted)',
                      border: `1px solid ${isStepComplete ? 'var(--risk-low-border, rgba(45, 212, 191, 0.3))' : 'var(--border)'}`,
                      flexShrink: 0
                    }}>
                      ({stepAnswered}/{stepTotal})
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </aside>
  );
}
