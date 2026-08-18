import React from 'react';
import { DIABETES_FACTOR_LABELS } from '../utils/diabetesMappings';

const MODIFIABLE = new Set([
  'BMI', 'HighBP', 'HighChol', 'PhysActivity', 'Smoker',
  'Fruits', 'Veggies', 'GenHlth', 'HvyAlcoholConsump'
]);

const FIELD_COPY = {
  GenHlth: 'Improving overall health through sleep, diet and activity lowers this driver.',
  HighBP: 'Blood pressure can often be lowered through diet, exercise and medication.',
  BMI: 'Gradual weight management directly reduces this contribution.',
  HighChol: 'Cholesterol responds well to dietary changes and treatment.',
  PhysActivity: 'Regular activity — even brisk walking — reduces diabetes risk.',
  Smoker: 'Quitting smoking improves insulin sensitivity over time.',
  Fruits: 'Daily fruit intake supports better blood sugar regulation.',
  Veggies: 'Vegetables help manage weight and blood sugar.',
  HvyAlcoholConsump: 'Reducing alcohol intake supports metabolic health.',
  Age: 'Age is a fixed factor — but it makes the modifiable ones matter more.',
  Sex: 'A fixed biological factor in the model.',
  DiffWalk: 'Mobility limits activity; physiotherapy or low-impact exercise can help.',
  HeartDiseaseorAttack: 'Existing heart conditions raise baseline risk — managing them helps.',
  Stroke: 'A prior stroke raises baseline risk — ongoing care matters most here.'
};

function normalizeFactors(factors) {
  return (factors || []).map((f) => {
    if (typeof f === 'string') {
      return { feature: f, impact: 0 };
    }
    return {
      feature: f.feature || f.name || 'Factor',
      impact: f.impact ?? f.shap_value ?? f.importance ?? 0
    };
  });
}

function FactorRow({ factor, maxAbs }) {
  const label = DIABETES_FACTOR_LABELS[factor.feature] || factor.feature;
  const isProtective = factor.impact < 0;
  const widthPct = maxAbs > 0 ? Math.max(6, (Math.abs(factor.impact) / maxAbs) * 100) : 6;

  return (
    <div className="dia-factor-row">
      <div style={{ minWidth: '180px' }}>
        <div style={{ fontSize: '0.88rem', fontWeight: 600 }}>{label}</div>
        <div className="dia-muted" style={{ fontSize: '0.78rem' }}>
          {FIELD_COPY[factor.feature] || ''}
        </div>
      </div>
      <div className="dia-factor-bar-track">
        <div
          className={`dia-factor-bar-fill${isProtective ? ' dia-factor-bar-fill--protective' : ''}`}
          style={{ width: `${widthPct}%` }}
        />
      </div>
      <span
        className="dia-muted"
        style={{ fontSize: '0.8rem', minWidth: '64px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}
      >
        {isProtective ? 'protective' : `+${Math.abs(factor.impact).toFixed(2)}`}
      </span>
    </div>
  );
}

/**
 * Groups a prediction's top factors into what the user can change vs what
 * they cannot, with plain-language guidance for each.
 * variant: 'full' shows both groups with copy; 'compact' shows a single list.
 */
export default function RiskFactorBreakdown({ factors, variant = 'full' }) {
  const normalized = normalizeFactors(factors);
  if (normalized.length === 0) {
    return <p className="dia-muted">No factor details available for this assessment.</p>;
  }

  const maxAbs = Math.max(...normalized.map((f) => Math.abs(f.impact)));

  if (variant === 'compact') {
    return (
      <div>
        {normalized.map((f) => (
          <FactorRow key={f.feature} factor={f} maxAbs={maxAbs} />
        ))}
      </div>
    );
  }

  const modifiable = normalized.filter((f) => MODIFIABLE.has(f.feature));
  const fixed = normalized.filter((f) => !MODIFIABLE.has(f.feature));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--dia-sp-6)' }}>
      {modifiable.length > 0 && (
        <div>
          <p className="dia-eyebrow" style={{ marginBottom: 'var(--dia-sp-2)' }}>
            Within your control
          </p>
          {modifiable.map((f) => (
            <FactorRow key={f.feature} factor={f} maxAbs={maxAbs} />
          ))}
        </div>
      )}
      {fixed.length > 0 && (
        <div>
          <p className="dia-eyebrow" style={{ marginBottom: 'var(--dia-sp-2)' }}>
            Fixed factors
          </p>
          {fixed.map((f) => (
            <FactorRow key={f.feature} factor={f} maxAbs={maxAbs} />
          ))}
        </div>
      )}
    </div>
  );
}
