import React from 'react';

export default function ShapFactorCardWidget({ data }) {
  if (!data) return null;

  const { overall_risk, probability, factors = [] } = data;

  const riskBadgeColor =
    overall_risk?.toLowerCase().includes('high') ? '#ef4444' :
    overall_risk?.toLowerCase().includes('mod') ? '#f59e0b' : '#10b981';

  return (
    <div style={{
      marginTop: '12px',
      marginBottom: '12px',
      padding: '16px',
      borderRadius: '12px',
      background: 'var(--surface-muted, #1e293b)',
      border: '1px solid var(--border, #334155)',
      color: 'var(--text, #f8fafc)',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
    }}>
      <div style={{
        display: 'flex',
        justify: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '8px',
        marginBottom: '12px',
        borderBottom: '1px solid var(--border, #334155)',
        paddingBottom: '8px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '1.2rem' }}>📊</span>
          <strong style={{ fontSize: '0.95rem' }}>Clinical SHAP Risk Factors</strong>
        </div>
        {overall_risk && (
          <span style={{
            padding: '4px 10px',
            borderRadius: '12px',
            fontSize: '0.75rem',
            fontWeight: '700',
            backgroundColor: `${riskBadgeColor}22`,
            color: riskBadgeColor,
            border: `1px solid ${riskBadgeColor}`
          }}>
            {overall_risk} {probability ? `(${probability})` : ''}
          </span>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {factors.map((factor, idx) => {
          if (typeof factor === 'string') {
            return (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  justify: 'space-between',
                  alignItems: 'center',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid rgba(255, 255, 255, 0.06)'
                }}
              >
                <div style={{ fontWeight: '600', fontSize: '0.85rem' }}>{factor}</div>
              </div>
            );
          }

          const name = factor.name || factor.feature || factor.feature_name || `Factor ${idx + 1}`;
          const rawImpact = factor.impact ?? factor.shap_value ?? factor.importance ?? 0;
          
          let impactStr = '';
          let isRisk = false;

          if (typeof rawImpact === 'number') {
            isRisk = rawImpact >= 0;
            impactStr = rawImpact >= 0 ? `+${rawImpact.toFixed(3)}` : rawImpact.toFixed(3);
          } else if (typeof rawImpact === 'string') {
            isRisk = factor.type === 'risk_driver' || rawImpact.startsWith('+') || (!rawImpact.startsWith('-') && !rawImpact.toLowerCase().includes('protect'));
            impactStr = rawImpact;
          } else {
            isRisk = factor.type === 'risk_driver';
            impactStr = String(rawImpact);
          }

          if (factor.type === 'protective_factor') {
            isRisk = false;
          } else if (factor.type === 'risk_driver') {
            isRisk = true;
          }

          const impactColor = isRisk ? '#f87171' : '#34d399';
          const displayValue = factor.value != null ? String(factor.value) : null;

          return (
            <div
              key={idx}
              style={{
                display: 'flex',
                justify: 'space-between',
                alignItems: 'center',
                padding: '8px 12px',
                borderRadius: '8px',
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid rgba(255, 255, 255, 0.06)'
              }}
            >
              <div>
                <div style={{ fontWeight: '600', fontSize: '0.85rem' }}>{name}</div>
                {displayValue && (
                  <div style={{ fontSize: '0.75rem', opacity: 0.7 }}>
                    Value: {displayValue}
                  </div>
                )}
              </div>
              <div style={{
                fontSize: '0.85rem',
                fontWeight: '700',
                color: impactColor,
                fontFamily: 'monospace',
                backgroundColor: 'rgba(0, 0, 0, 0.2)',
                padding: '3px 8px',
                borderRadius: '6px'
              }}>
                {impactStr}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
