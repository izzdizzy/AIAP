/**
 * Reusable Feature Importance Horizontal Bar Component
 * Used across CAD, Readmission, and Diabetes result views to display SHAP risk factors visually.
 * Formats every factor value into exact standardized contribution text (e.g. "Higher contribution (+0.597)" or "Lower contribution (-0.27)")
 * aligned to the right edge of each factor bar.
 */

export default function FeatureImportanceBar({ factors = [], maxItems = 6 }) {
  if (!factors || factors.length === 0) return null;

  const normalizedFactors = factors.slice(0, maxItems).map((item, idx) => {
    let label = `Factor ${idx + 1}`;
    let val = 0.2;
    let rawDisplay = '';
    let direction = 'positive';

    if (typeof item === 'object' && item !== null) {
      label = item.label || item.feature || item.name || label;
      val = item.impact ?? item.importance ?? item.shap_value ?? item.value ?? 0;
      rawDisplay = item.displayValue ?? '';
      direction = item.direction || (val < 0 ? 'negative' : 'positive');
    } else if (typeof item === 'string') {
      label = item;
      val = 0.2;
    }

    let displayValue = rawDisplay;

    // Standardize displayValue format if not already containing "contribution"
    if (!displayValue || (!displayValue.includes('contribution') && typeof val === 'number')) {
      const numStr = Math.abs(val) < 0.01 && val !== 0 ? val.toExponential(2) : Math.abs(val).toFixed(3);
      if (val >= 0) {
        displayValue = `Higher contribution (+${numStr})`;
        direction = 'positive';
      } else {
        displayValue = `Lower contribution (-${numStr})`;
        direction = 'negative';
      }
    } else if (displayValue && !displayValue.includes('contribution')) {
      if (direction === 'negative' || val < 0) {
        displayValue = `Lower contribution (${displayValue})`;
      } else {
        displayValue = `Higher contribution (${displayValue})`;
      }
    }

    return {
      label,
      value: Math.abs(val),
      displayValue,
      direction
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
