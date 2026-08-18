import React from 'react';
import { READMISSION_FEATURE_LABELS } from '../features/readmission/utils/readmissionConfig';
import { DIABETES_FEATURE_LABELS } from '../features/diabetes/utils/diabetesConfig';

const CAD_FEATURE_LABELS = {
  age: 'Age',
  sex: 'Biological Sex',
  cp: 'Chest Pain Type',
  trestbps: 'Resting Blood Pressure',
  chol: 'Serum Cholesterol',
  fbs: 'Fasting Blood Sugar',
  restecg: 'Resting ECG Findings',
  thalach: 'Max Heart Rate',
  exang: 'Exercise Induced Angina',
  oldpeak: 'ST Depression (Oldpeak)',
  slope: 'ST Slope',
  ca: 'Major Vessels Count',
  thal: 'Thalassemia'
};

const FEATURE_NAME_MAP = {
  ...CAD_FEATURE_LABELS,
  ...READMISSION_FEATURE_LABELS,
  ...DIABETES_FEATURE_LABELS
};

function formatFeatureLabel(key) {
  if (!key) return '';
  if (FEATURE_NAME_MAP[key]) return FEATURE_NAME_MAP[key];
  return String(key)
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\b\w/g, char => char.toUpperCase());
}

/**
 * Reusable Feature Importance Horizontal Bar Component
 * Used across CAD, Readmission, and Diabetes result views to display SHAP risk factors visually.
 * Formats every factor value into exact standardized contribution text (e.g. "Higher contribution (+0.597)" or "Lower contribution (-0.27)")
 * aligned to the right edge of each factor bar.
 */
export default function FeatureImportanceBar({ factors = [], maxItems = 6 }) {
  if (!factors || factors.length === 0) return null;

  const normalizedFactors = factors.slice(0, maxItems).map((item, idx) => {
    let rawLabel = `Factor ${idx + 1}`;
    let val = 0.2;
    let direction = 'positive';

    if (typeof item === 'object' && item !== null) {
      rawLabel = item.label || item.feature || item.name || rawLabel;
      // Prefer explicit signed impact/shap_value over absolute value
      if (typeof item.impact === 'number') {
        val = item.impact;
      } else if (typeof item.shap_value === 'number') {
        val = item.shap_value;
      } else if (typeof item.value === 'number') {
        val = item.value;
      } else if (typeof item.importance === 'number') {
        val = item.importance;
      }

      if (item.direction) {
        direction = item.direction;
      } else {
        direction = val < 0 ? 'negative' : 'positive';
      }
    } else if (typeof item === 'string') {
      rawLabel = item;
      val = 0.2;
    }

    // Map raw variable key to human-readable label
    const label = formatFeatureLabel(rawLabel);

    // Standardize displayValue format
    const numStr = Math.abs(val) < 0.01 && val !== 0 ? Math.abs(val).toExponential(2) : Math.abs(val).toFixed(3);
    const displayValue = val >= 0 || direction === 'positive'
      ? `Higher contribution (+${numStr})`
      : `Lower contribution (-${numStr})`;

    return {
      label,
      value: Math.abs(val),
      displayValue,
      direction: val >= 0 ? (direction || 'positive') : 'negative'
    };
  });

  return (
    <div className="feature-bar-container">
      {normalizedFactors.map((fact, i) => (
        <div key={i} className="feature-bar-item">
          <div className="feature-bar-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
            <span className="feature-bar-title">{fact.label}</span>
            <span className="feature-bar-value" style={{ marginLeft: 'auto', textAlign: 'right', fontWeight: 600 }}>
              {fact.displayValue}
            </span>
          </div>
          <div className="feature-bar-track">
            <div
              className={`feature-bar-fill ${
                fact.direction === 'negative' ? 'feature-bar-fill--negative' : 'feature-bar-fill--positive'
              }`}
              style={{ width: `${Math.min(fact.value * 100, 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
