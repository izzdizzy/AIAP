/**
 * Reusable Feature Importance Horizontal Bar Component
 * Used across CAD, Readmission, and Diabetes result views to display top risk factors visually.
 */

export default function FeatureImportanceBar({ factors = [], maxItems = 6 }) {
  if (!factors || factors.length === 0) return null;

  const normalizedFactors = factors.slice(0, maxItems).map((item, idx) => {
    if (typeof item === 'object' && item !== null) {
      const val = item.value ?? item.importance ?? item.shap_value ?? 0;
      return {
        label: item.label || item.feature || `Factor ${idx + 1}`,
        value: typeof val === 'number' ? val : 0.5,
        displayValue: item.displayValue ?? String(item.value ?? item.importance ?? ''),
        direction: item.direction || (val < 0 ? 'negative' : 'positive')
      };
    }

    if (typeof item === 'string') {
      if (item.includes('=')) {
        const [k, v] = item.split('=');
        return {
          label: k.trim(),
          value: 0.6,
          displayValue: v.trim(),
          direction: 'positive'
        };
      }
      return {
        label: item,
        value: 0.5,
        displayValue: '',
        direction: 'positive'
      };
    }

    return { label: String(item), value: 0.5, displayValue: '', direction: 'positive' };
  });

  return (
    <div className="feature-bar-container">
      {normalizedFactors.map((fact, i) => (
        <div key={i} className="feature-bar-item">
          <div className="feature-bar-header">
            <span className="feature-bar-title">{fact.label}</span>
            <span className="feature-bar-value">{fact.displayValue}</span>
          </div>
          <div className="feature-bar-track">
            <div
              className={`feature-bar-fill ${
                fact.direction === 'negative' ? 'feature-bar-fill--negative' : 'feature-bar-fill--positive'
              }`}
              style={{ width: `${Math.min(Math.abs(fact.value) * 100, 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
