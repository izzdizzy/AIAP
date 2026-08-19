import React, { useState } from 'react';

export default function ShapFactorCardWidget({ data }) {
  const [activeModule, setActiveModule] = useState('all');

  if (!data) return null;

  const { overall_risk, probability, module_risks = {}, factors = [] } = data;

  // Detect available modules in factors payload
  const availableModules = ['all'];
  if (factors.some(f => f.module === 'cad')) availableModules.push('cad');
  if (factors.some(f => f.module === 'diabetes')) availableModules.push('diabetes');
  if (factors.some(f => f.module === 'readmission')) availableModules.push('readmission');

  const tabLabels = {
    all: '⭐ Top 6 Drivers',
    cad: '🫀 CAD',
    diabetes: '🥗 Diabetes',
    readmission: '🏥 Readmission'
  };

  // Determine current active risk label and color
  let currentRisk = overall_risk;
  let currentProb = probability;

  if (activeModule === 'cad' && module_risks.cad) {
    currentRisk = `CAD: ${module_risks.cad.risk}`;
    currentProb = module_risks.cad.prob;
  } else if (activeModule === 'diabetes' && module_risks.diabetes) {
    currentRisk = `Diabetes: ${module_risks.diabetes.risk}`;
    currentProb = module_risks.diabetes.prob;
  } else if (activeModule === 'readmission' && module_risks.readmission) {
    currentRisk = `Readmission: ${module_risks.readmission.risk}`;
    currentProb = module_risks.readmission.prob;
  }

  const riskBadgeColor =
    currentRisk?.toLowerCase().includes('high') || currentRisk?.toLowerCase().includes('immediate') ? '#ef4444' :
    currentRisk?.toLowerCase().includes('mod') || currentRisk?.toLowerCase().includes('surveillance') ? '#f59e0b' : '#10b981';

  // Sort all factors by absolute impact magnitude descending
  const sortedFactors = [...factors].sort((a, b) => {
    const impA = Math.abs(typeof a.rawImpact === 'number' ? a.rawImpact : (parseFloat(String(a.impact).replace('+', '')) || 0));
    const impB = Math.abs(typeof b.rawImpact === 'number' ? b.rawImpact : (parseFloat(String(b.impact).replace('+', '')) || 0));
    return impB - impA;
  });

  // Filter factors by active module tab
  const displayedFactors = (
    activeModule === 'all'
      ? sortedFactors.slice(0, 6)
      : sortedFactors.filter(f => f.module === activeModule).slice(0, 6)
  );

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
      {/* Header Bar */}
      <div style={{
        display: 'flex',
        justify: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '8px',
        marginBottom: '12px',
        borderBottom: '1px solid var(--border, #334155)',
        paddingBottom: '10px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '1.2rem' }}>📊</span>
          <strong style={{ fontSize: '0.95rem' }}>Clinical SHAP Risk Factors</strong>
        </div>

        {currentRisk && (
          <span style={{
            padding: '4px 12px',
            borderRadius: '12px',
            fontSize: '0.78rem',
            fontWeight: '700',
            backgroundColor: `${riskBadgeColor}22`,
            color: riskBadgeColor,
            border: `1px solid ${riskBadgeColor}`
          }}>
            {currentRisk} {currentProb ? `(${currentProb})` : ''}
          </span>
        )}
      </div>

      {/* Internal Filter Tabs */}
      {availableModules.length > 2 && (
        <div style={{
          display: 'flex',
          gap: '8px',
          marginBottom: '12px',
          paddingBottom: '8px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
          overflowX: 'auto'
        }}>
          {availableModules.map(modKey => {
            const isActive = activeModule === modKey;
            return (
              <button
                key={modKey}
                type="button"
                onClick={() => setActiveModule(modKey)}
                style={{
                  padding: '5px 12px',
                  borderRadius: '16px',
                  fontSize: '0.78rem',
                  fontWeight: isActive ? '700' : '600',
                  border: isActive ? '1px solid #3b82f6' : '1px solid rgba(255, 255, 255, 0.12)',
                  background: isActive ? 'rgba(59, 130, 246, 0.25)' : 'rgba(0, 0, 0, 0.2)',
                  color: isActive ? '#ffffff' : 'var(--text-muted, #94a3b8)',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  transition: 'all 0.15s ease'
                }}
              >
                {tabLabels[modKey] || modKey}
              </button>
            );
          })}
        </div>
      )}

      {/* Factor List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {displayedFactors.length === 0 ? (
          <div style={{ fontSize: '0.82rem', color: '#94a3b8', fontStyle: 'italic', padding: '8px 0' }}>
            No factors available for this assessment module.
          </div>
        ) : (
          displayedFactors.map((factor, idx) => {
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
            const rawImpact = factor.rawImpact ?? factor.impact ?? factor.shap_value ?? factor.importance ?? 0;
            
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
            const rawValStr = factor.value != null ? String(factor.value).trim() : '';
            const displayValue = rawValStr && rawValStr.toLowerCase() !== 'observed' ? rawValStr : null;

            return (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  justify: 'space-between',
                  alignItems: 'center',
                  gap: '24px',
                  padding: '10px 14px',
                  borderRadius: '8px',
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid rgba(255, 255, 255, 0.06)'
                }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: '600', fontSize: '0.88rem', color: 'var(--text, #f8fafc)', lineHeight: 1.3 }}>
                    {name}
                  </div>
                  {displayValue && (
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted, #94a3b8)', marginTop: '3px' }}>
                      <strong>Value:</strong> {displayValue}
                    </div>
                  )}
                </div>

                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-end',
                  flexShrink: 0
                }}>
                  <div style={{
                    fontSize: '0.85rem',
                    fontWeight: '700',
                    color: impactColor,
                    fontFamily: 'monospace',
                    backgroundColor: 'rgba(0, 0, 0, 0.3)',
                    padding: '4px 10px',
                    borderRadius: '6px'
                  }}>
                    {impactStr}
                  </div>
                  <span style={{ fontSize: '0.68rem', fontWeight: '600', color: impactColor, marginTop: '2px', opacity: 0.9 }}>
                    {isRisk ? 'Increases Risk' : 'Protective Factor'}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
