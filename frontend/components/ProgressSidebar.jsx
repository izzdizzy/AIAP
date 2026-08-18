import React from 'react';

/**
 * Reusable Integrated Progress & Stepper Sidebar
 * Visual Hierarchy Rules:
 * Top Section: Total counter with a subtle progress bar background.
 * Middle Section: Integrated Stepper List with active (teal/highlighted ring), completed (solid check mark/filled green), and pending (greyed out) states.
 * Bottom Section: Field Completion Counters per section with a min 24px vertical gap.
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

        {/* Middle Section: Integrated Stepper List */}
        {validSteps.length > 0 && (
          <div style={{ display: 'grid', gap: '8px' }}>
            {validSteps.map((step, idx) => {
              const stepNum = idx + 1;
              const isActive = stepNum === currentStepIndex;
              const isCompleted = stepNum < currentStepIndex;
              const isPending = stepNum > currentStepIndex;

              return (
                <button
                  key={step.id || stepNum}
                  type="button"
                  onClick={() => onSelectStep?.(stepNum)}
                  disabled={!onSelectStep}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
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
                    color: isActive ? 'var(--text)' : isPending ? 'var(--text-muted)' : 'var(--text)'
                  }}>
                    {step.title}
                  </span>
                </button>
              );
            })}
          </div>
        )}

        {/* Bottom Section: Field Completion Counters with min 24px gap */}
        {groups.length > 0 && (
          <div style={{ marginTop: '28px', borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
            <h4 style={{ margin: '0 0 12px', fontSize: '0.82rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)' }}>
              Field Completion
            </h4>
            <div style={{ display: 'grid', gap: '8px' }}>
              {groups.map((group) => {
                const groupAnswered = group.answeredCount ?? 0;
                const groupTotal = group.totalCount ?? 0;
                const isGroupComplete = groupTotal > 0 && groupAnswered === groupTotal;

                return (
                  <div
                    key={group.id || group.title}
                    style={{
                      display: 'flex',
                      justify: 'space-between',
                      alignItems: 'center',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      background: 'var(--surface-muted)',
                      border: '1px solid var(--border)',
                      fontSize: '0.82rem'
                    }}
                  >
                    <span style={{ fontWeight: 500, color: 'var(--text)' }}>{group.title}</span>
                    <span style={{
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '999px',
                      background: isGroupComplete ? 'var(--risk-low-bg)' : 'var(--surface)',
                      color: isGroupComplete ? 'var(--risk-low-text)' : 'var(--text-muted)',
                      border: `1px solid ${isGroupComplete ? 'var(--risk-low-border)' : 'var(--border)'}`
                    }}>
                      {groupAnswered}/{groupTotal}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
