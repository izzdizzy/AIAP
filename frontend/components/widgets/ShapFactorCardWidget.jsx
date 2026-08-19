import React, { useState } from 'react';

const FEATURE_NAME_MAP = {
  // CAD
  'Chest Pain': 'Chest Pain Category',
  'Chest Pain Category': 'Chest Pain Category',
  'Number of Major Vessels': 'Major Vessels Count',
  'Major Vessels Count': 'Major Vessels Count',
  'Exercise-Induced Angina': 'Exercise-Induced Angina',
  'Resting Blood Pressure': 'Resting Blood Pressure',
  'Serum Cholesterol': 'Serum Cholesterol',
  'Cholesterol': 'Serum Cholesterol',
  'ST Depression': 'ST Depression (Oldpeak)',
  'ST Depression (Oldpeak)': 'ST Depression (Oldpeak)',
  'Maximum Heart Rate': 'Max Heart Rate',
  'Max Heart Rate': 'Max Heart Rate',
  'Fasting Blood Sugar': 'Fasting Blood Sugar',
  'Resting ECG': 'Resting ECG Findings',
  'Resting ECG Findings': 'Resting ECG Findings',
  'ST Segment Slope': 'ST Segment Slope',
  'ST Slope': 'ST Segment Slope',
  'Thalassemia': 'Thalassemia Category',
  'Thalassemia Category': 'Thalassemia Category',
  cp: 'Chest Pain Category',
  ca: 'Major Vessels Count',
  chol: 'Serum Cholesterol',
  trestbps: 'Resting Blood Pressure',
  thalach: 'Max Heart Rate',
  oldpeak: 'ST Depression (Oldpeak)',
  exang: 'Exercise-Induced Angina',
  fbs: 'Fasting Blood Sugar',
  restecg: 'Resting ECG Findings',
  slope: 'ST Segment Slope',
  thal: 'Thalassemia Category',

  // Readmission
  number_inpatient: 'Inpatient Admissions (Past 1 Year)',
  number_emergency: 'Emergency Visits (Past 1 Year)',
  number_outpatient: 'Outpatient Visits (Past 1 Year)',
  num_lab_procedures: 'Lab Procedures Conducted',
  num_medications: 'Prescribed Medications Count',
  medication_count: 'Prescribed Medications Count',
  prior_admissions: 'Prior Hospital Admissions',
  total_prior_admissions: 'Total Prior Admissions',
  time_in_hospital: 'Hospital Stay Duration',
  comorbidity_count: 'Comorbidity Count',
  number_diagnoses: 'Number of Diagnoses',
  num_procedures: 'Procedures Count',
  discharge_disposition_id: 'Discharge Disposition',
  admission_type_id: 'Admission Type',
  admission_source_id: 'Admission Source',
  diabetes_diag_count: 'Diabetes Diagnoses Count',
  chas_tier: 'CHAS Subsidy Tier',
  age_numeric: 'Patient Age',

  // Diabetes
  GenHlth: 'General Health Rating',
  HighBP: 'High Blood Pressure',
  BMI: 'Body Mass Index (BMI)',
  HighChol: 'High Cholesterol',
  Age: 'Age Group',
  DiffWalk: 'Difficulty Walking / Stairs',
  PhysActivity: 'Physical Activity',
  Smoker: 'Smoking History',
  HeartDiseaseorAttack: 'Heart Condition / Attack',
  Fruits: 'Daily Fruit Intake',
  Veggies: 'Daily Veggie Intake'
};

function formatFeatureTitle(rawName) {
  if (!rawName) return { title: 'Clinical Factor', extractedValue: null };

  let key = String(rawName).trim();
  let moduleTag = '';
  const match = key.match(/\s*\((CAD|Diabetes|Readmission)\)$/i);
  if (match) {
    moduleTag = ` (${match[1]})`;
    key = key.replace(/\s*\((CAD|Diabetes|Readmission)\)$/i, '').trim();
  }

  let extractedValue = null;
  const parenMatch = key.match(/^([^(]+)\(([^)]+)\)$/);
  if (parenMatch && !FEATURE_NAME_MAP[key]) {
    const candidateKey = parenMatch[1].trim();
    if (FEATURE_NAME_MAP[candidateKey]) {
      key = candidateKey;
      extractedValue = parenMatch[2].trim();
    }
  }

  let title = FEATURE_NAME_MAP[key];
  if (!title) {
    // Fallback: Convert snake_case strings to Title Case with spaces
    title = key
      .replace(/_/g, ' ')
      .replace(/([a-z])([A-Z])/g, '$1 $2')
      .replace(/\b\w/g, c => c.toUpperCase());
  }

  return {
    title: `${title}${moduleTag}`,
    extractedValue
  };
}

function getModuleBadgeStyle(riskStr = '', probStr = '') {
  const lower = (String(riskStr) + ' ' + String(probStr)).toLowerCase();

  // High Risk / Urgent / At Risk
  if (
    lower.includes('high') ||
    lower.includes('immediate') ||
    lower.includes('at risk') ||
    lower.includes('at-risk') ||
    lower.includes('elevated') ||
    lower.includes('severe')
  ) {
    return { bg: 'rgba(239, 68, 68, 0.18)', text: '#f87171', border: '#ef4444' };
  }

  // Moderate / Increased / Surveillance
  if (
    lower.includes('mod') ||
    lower.includes('surveillance') ||
    lower.includes('increased') ||
    lower.includes('caution')
  ) {
    return { bg: 'rgba(245, 158, 11, 0.18)', text: '#fbbf24', border: '#f59e0b' };
  }

  // Low / Normal / Routine
  return { bg: 'rgba(16, 185, 129, 0.18)', text: '#34d399', border: '#10b981' };
}

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

  // Calculate max absolute SHAP value among displayed factors
  const maxShap = Math.max(...displayedFactors.map(f => {
    const num = typeof f.rawImpact === 'number'
      ? Math.abs(f.rawImpact)
      : Math.abs(parseFloat(String(f.impact).replace('+', '')) || 0);
    return num > 0 ? num : 0.01;
  }), 0.01);

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
          <strong style={{ fontSize: '0.95rem' }}>Your Risk Factors</strong>
        </div>

        {/* Separate Header Module Context Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
          {module_risks.cad && (
            <span style={{
              padding: '3px 10px',
              borderRadius: '12px',
              fontSize: '0.74rem',
              fontWeight: '700',
              backgroundColor: getModuleBadgeStyle(module_risks.cad.risk, module_risks.cad.prob).bg,
              color: getModuleBadgeStyle(module_risks.cad.risk, module_risks.cad.prob).text,
              border: `1px solid ${getModuleBadgeStyle(module_risks.cad.risk, module_risks.cad.prob).border}`
            }}>
              🫀 CAD: {module_risks.cad.risk} {module_risks.cad.prob ? `(${module_risks.cad.prob})` : ''}
            </span>
          )}

          {module_risks.diabetes && (
            <span style={{
              padding: '3px 10px',
              borderRadius: '12px',
              fontSize: '0.74rem',
              fontWeight: '700',
              backgroundColor: getModuleBadgeStyle(module_risks.diabetes.risk, module_risks.diabetes.prob).bg,
              color: getModuleBadgeStyle(module_risks.diabetes.risk, module_risks.diabetes.prob).text,
              border: `1px solid ${getModuleBadgeStyle(module_risks.diabetes.risk, module_risks.diabetes.prob).border}`
            }}>
              🥗 Diabetes: {module_risks.diabetes.risk} {module_risks.diabetes.prob ? `(${module_risks.diabetes.prob})` : ''}
            </span>
          )}

          {module_risks.readmission && (
            <span style={{
              padding: '3px 10px',
              borderRadius: '12px',
              fontSize: '0.74rem',
              fontWeight: '700',
              backgroundColor: getModuleBadgeStyle(module_risks.readmission.risk, module_risks.readmission.prob).bg,
              color: getModuleBadgeStyle(module_risks.readmission.risk, module_risks.readmission.prob).text,
              border: `1px solid ${getModuleBadgeStyle(module_risks.readmission.risk, module_risks.readmission.prob).border}`
            }}>
              🏥 Readmission: {module_risks.readmission.risk} {module_risks.readmission.prob ? `(${module_risks.readmission.prob})` : ''}
            </span>
          )}

          {!module_risks.cad && !module_risks.diabetes && !module_risks.readmission && overall_risk && (
            <span style={{
              padding: '3px 10px',
              borderRadius: '12px',
              fontSize: '0.74rem',
              fontWeight: '700',
              backgroundColor: getModuleBadgeStyle(overall_risk, probability).bg,
              color: getModuleBadgeStyle(overall_risk, probability).text,
              border: `1px solid ${getModuleBadgeStyle(overall_risk, probability).border}`
            }}>
              {overall_risk} {probability ? `(${probability})` : ''}
            </span>
          )}
        </div>
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

            const rawName = factor.name || factor.feature || factor.feature_name || `Factor ${idx + 1}`;
            const { title, extractedValue } = formatFeatureTitle(rawName);

            const numImpact = typeof factor.rawImpact === 'number'
              ? factor.rawImpact
              : (parseFloat(String(factor.impact ?? factor.shap_value ?? 0).replace('+', '')) || 0);

            const absImpact = Math.abs(numImpact);
            const widthPct = Math.min(100, Math.max(6, (absImpact / maxShap) * 100));

            let impactFormatted = '';
            let isRisk = false;

            if (typeof numImpact === 'number') {
              isRisk = numImpact >= 0;
              impactFormatted = numImpact >= 0 ? `+${numImpact.toFixed(3)}` : numImpact.toFixed(3);
            } else {
              impactFormatted = String(factor.impact || '0.000');
              if (!impactFormatted.startsWith('+') && !impactFormatted.startsWith('-')) {
                impactFormatted = `+${impactFormatted}`;
              }
            }

            if (factor.type === 'protective_factor') {
              isRisk = false;
            } else if (factor.type === 'risk_driver') {
              isRisk = true;
            }

            const impactTextColor = isRisk ? '#fb7185' : '#34d399';
            const rawValStr = factor.value != null ? String(factor.value).trim() : '';
            const hasVal = rawValStr && rawValStr.toLowerCase() !== 'observed' && rawValStr.toLowerCase() !== 'null';
            const displayValue = hasVal ? rawValStr : extractedValue;

            return (
              <div
                key={idx}
                style={{
                  position: 'relative',
                  overflow: 'hidden',
                  display: 'flex',
                  justify: 'space-between',
                  alignItems: 'center',
                  gap: '24px',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  background: isRisk ? 'rgba(244, 63, 94, 0.06)' : 'rgba(16, 185, 129, 0.06)',
                  border: isRisk ? '1px solid rgba(244, 63, 94, 0.22)' : '1px solid rgba(16, 185, 129, 0.22)'
                }}
              >
                {/* Visual Proportional Background SHAP Fill Bar */}
                <div
                  aria-hidden="true"
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    bottom: 0,
                    width: `${widthPct}%`,
                    backgroundColor: isRisk ? 'rgba(244, 63, 94, 0.14)' : 'rgba(16, 185, 129, 0.14)',
                    borderRadius: '8px',
                    pointerEvents: 'none',
                    transition: 'width 0.3s ease'
                  }}
                />

                {/* Bottom Accent Line */}
                <div
                  aria-hidden="true"
                  style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    height: '3px',
                    width: `${widthPct}%`,
                    backgroundColor: isRisk ? '#f43f5e' : '#10b981',
                    borderRadius: '0 2px 2px 0',
                    pointerEvents: 'none',
                    transition: 'width 0.3s ease'
                  }}
                />

                {/* Left Title & Patient Metric */}
                <div style={{ flex: 1, minWidth: 0, zIndex: 1 }}>
                  <div style={{ fontWeight: '600', fontSize: '0.88rem', color: 'var(--text, #f8fafc)', lineHeight: 1.3 }}>
                    {title}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted, #94a3b8)', marginTop: '3px' }}>
                    <strong>Value:</strong> {displayValue || 'N/A'}
                  </div>
                </div>

                {/* Right Accessible Directional SHAP Badge */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '0.82rem',
                  fontWeight: '700',
                  color: impactTextColor,
                  fontFamily: 'monospace',
                  backgroundColor: isRisk ? 'rgba(225, 29, 72, 0.25)' : 'rgba(5, 150, 105, 0.25)',
                  padding: '5px 10px',
                  borderRadius: '6px',
                  border: `1px solid ${isRisk ? 'rgba(244, 63, 94, 0.35)' : 'rgba(16, 185, 129, 0.35)'}`,
                  whiteSpace: 'nowrap',
                  zIndex: 1,
                  flexShrink: 0
                }}>
                  <span>{isRisk ? '▲' : '▼'}</span>
                  <span>{impactFormatted}</span>
                  <span style={{ fontSize: '0.74rem', fontWeight: '600', opacity: 0.95 }}>
                    ({isRisk ? 'Increases Risk' : 'Reduces Risk'})
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
