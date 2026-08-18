import { useState, useEffect } from 'react';
import { checkHealth, predictRisk, explainRisk } from '../../services/diabetes/api';
import { DIABETES_FIELD_OPTIONS, DIABETES_FACTOR_LABELS } from '../../utils/diabetesMappings';

const DEFAULTS = {
  CholCheck: 1, Stroke: 0, HvyAlcoholConsump: 0, AnyHealthcare: 1,
  NoDocbcCost: 0, MentHlth: 2, PhysHlth: 3, Education: 4, Income: 5
};

export default function DiabetesPage({ onBackToLanding }) {
  const [live, setLive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [explaining, setExplaining] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [profile, setProfile] = useState({});
  const [prediction, setPrediction] = useState(null);
  const [explanation, setExplanation] = useState('');

  useEffect(() => {
    checkHealth().then(result => {
      setLive(result.status === 'ok' && result.model_loaded);
    });
  }, []);

  function handleChange(field, value) {
    setProfile(prev => ({ ...prev, [field]: Number(value) }));
    if (errorMessage) setErrorMessage(null);
  }

  async function handleAssess() {
    setLoading(true);
    setErrorMessage(null);
    try {
      const fullProfile = { ...DEFAULTS, ...profile };
      const result = await predictRisk(fullProfile);
      setPrediction(result);
    } catch (error) {
      setErrorMessage('Prediction request failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleExplain() {
    if (!prediction) return;
    setExplaining(true);
    setErrorMessage(null);
    try {
      const fullProfile = { ...DEFAULTS, ...profile };
      const result = await explainRisk(fullProfile);
      setExplanation(result.explanation);
    } catch (error) {
      setErrorMessage('Explanation generation failed: ' + error.message);
    } finally {
      setExplaining(false);
    }
  }

  function loadSample() {
    const sample = {
      GenHlth: 4, BMI: 34, Age: 9, Sex: 1, HighBP: 1, HighChol: 1,
      PhysActivity: 0, DiffWalk: 1, Smoker: 1, HeartDiseaseorAttack: 0,
      Fruits: 0, Veggies: 1
    };
    setProfile(sample);
    setErrorMessage(null);
  }

  const renderBandPill = () => {
    if (!prediction) return null;
    const band = (prediction.risk_band || 'Low').toLowerCase();
    const pillClass = band.includes('high')
      ? 'risk-pill--high'
      : band.includes('mod')
      ? 'risk-pill--moderate'
      : 'risk-pill--low';

    return (
      <span className={`risk-pill ${pillClass}`}>
        {prediction.risk_band} Risk · {prediction.risk_label}
      </span>
    );
  };

  return (
    <div className="page-stack">
      {/* Module Sub-Header / Intro */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <p className="eyebrow">Endocrine Health Module</p>
          <h2 style={{ fontSize: '1.8rem', margin: '0 0 8px 0', color: 'var(--text)' }}>
            Diabetes Chronic Risk Classifier
          </h2>
          <p style={{ margin: 0, color: 'var(--text-muted)', maxWidth: '640px' }}>
            Evaluate individual health profile factors to gauge diabetes likelihood, understand key contributing factors, and receive AI-backed health guidance.
          </p>
        </div>

        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 14px',
          borderRadius: '999px',
          background: 'var(--surface-muted)',
          border: '1px solid var(--border)',
          fontSize: '0.85rem',
          color: 'var(--text-muted)'
        }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: live ? 'var(--risk-low-text)' : 'var(--text-muted)'
          }} />
          <span>{live ? 'Service Online' : 'Demo Mode (Offline)'}</span>
        </div>
      </div>

      {errorMessage && (
        <div className="alert-banner alert-banner--danger" role="alert">
          <strong>Error:</strong> {errorMessage}
        </div>
      )}

      {/* Main Form & Results Grid */}
      <div className="assessment-layout" style={{ gridTemplateColumns: 'minmax(0, 1.1fr) minmax(0, 0.9fr)', gap: '20px' }}>
        {/* Form Inputs Card */}
        <div className="section-card">
          <div className="section-card__header">
            <h2>Patient Health Profile</h2>
            <p>Input health parameters aligned with standard clinical records.</p>
          </div>

          <div className="section-card__body" style={{ display: 'grid', gap: '16px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              <div>
                <label className="form-field__label" htmlFor="GenHlth">General Health</label>
                <select
                  id="GenHlth"
                  className="nav-link"
                  style={{ width: '100%', borderRadius: '10px', padding: '10px' }}
                  value={profile.GenHlth || 3}
                  onChange={(e) => handleChange('GenHlth', e.target.value)}
                >
                  {DIABETES_FIELD_OPTIONS.GenHlth.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="form-field__label" htmlFor="BMI">Body Mass Index (BMI)</label>
                <input
                  id="BMI"
                  type="number"
                  className="nav-link"
                  style={{ width: '100%', borderRadius: '10px', padding: '10px' }}
                  value={profile.BMI || 28}
                  min="10"
                  max="100"
                  step="0.1"
                  onChange={(e) => handleChange('BMI', e.target.value)}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              <div>
                <label className="form-field__label" htmlFor="Age">Age Group</label>
                <select
                  id="Age"
                  className="nav-link"
                  style={{ width: '100%', borderRadius: '10px', padding: '10px' }}
                  value={profile.Age || 9}
                  onChange={(e) => handleChange('Age', e.target.value)}
                >
                  {DIABETES_FIELD_OPTIONS.Age.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="form-field__label" htmlFor="Sex">Biological Sex</label>
                <select
                  id="Sex"
                  className="nav-link"
                  style={{ width: '100%', borderRadius: '10px', padding: '10px' }}
                  value={profile.Sex !== undefined ? profile.Sex : 1}
                  onChange={(e) => handleChange('Sex', e.target.value)}
                >
                  {DIABETES_FIELD_OPTIONS.Sex.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              <div>
                <label className="form-field__label" htmlFor="HighBP">High Blood Pressure</label>
                <select
                  id="HighBP"
                  className="nav-link"
                  style={{ width: '100%', borderRadius: '10px', padding: '10px' }}
                  value={profile.HighBP !== undefined ? profile.HighBP : 1}
                  onChange={(e) => handleChange('HighBP', e.target.value)}
                >
                  {DIABETES_FIELD_OPTIONS.YesNo.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="form-field__label" htmlFor="HighChol">High Cholesterol</label>
                <select
                  id="HighChol"
                  className="nav-link"
                  style={{ width: '100%', borderRadius: '10px', padding: '10px' }}
                  value={profile.HighChol !== undefined ? profile.HighChol : 1}
                  onChange={(e) => handleChange('HighChol', e.target.value)}
                >
                  {DIABETES_FIELD_OPTIONS.YesNo.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              <div>
                <label className="form-field__label" htmlFor="PhysActivity">Physically Active</label>
                <select
                  id="PhysActivity"
                  className="nav-link"
                  style={{ width: '100%', borderRadius: '10px', padding: '10px' }}
                  value={profile.PhysActivity !== undefined ? profile.PhysActivity : 1}
                  onChange={(e) => handleChange('PhysActivity', e.target.value)}
                >
                  {DIABETES_FIELD_OPTIONS.YesNoInverted.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="form-field__label" htmlFor="DiffWalk">Difficulty Walking</label>
                <select
                  id="DiffWalk"
                  className="nav-link"
                  style={{ width: '100%', borderRadius: '10px', padding: '10px' }}
                  value={profile.DiffWalk !== undefined ? profile.DiffWalk : 1}
                  onChange={(e) => handleChange('DiffWalk', e.target.value)}
                >
                  {DIABETES_FIELD_OPTIONS.YesNo.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              <div>
                <label className="form-field__label" htmlFor="Smoker">Smoker (100+ lifetime)</label>
                <select
                  id="Smoker"
                  className="nav-link"
                  style={{ width: '100%', borderRadius: '10px', padding: '10px' }}
                  value={profile.Smoker !== undefined ? profile.Smoker : 1}
                  onChange={(e) => handleChange('Smoker', e.target.value)}
                >
                  {DIABETES_FIELD_OPTIONS.YesNo.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="form-field__label" htmlFor="HeartDiseaseorAttack">Heart Disease / Attack</label>
                <select
                  id="HeartDiseaseorAttack"
                  className="nav-link"
                  style={{ width: '100%', borderRadius: '10px', padding: '10px' }}
                  value={profile.HeartDiseaseorAttack !== undefined ? profile.HeartDiseaseorAttack : 0}
                  onChange={(e) => handleChange('HeartDiseaseorAttack', e.target.value)}
                >
                  {DIABETES_FIELD_OPTIONS.YesNo.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              <div>
                <label className="form-field__label" htmlFor="Fruits">Daily Fruit Consumption</label>
                <select
                  id="Fruits"
                  className="nav-link"
                  style={{ width: '100%', borderRadius: '10px', padding: '10px' }}
                  value={profile.Fruits !== undefined ? profile.Fruits : 0}
                  onChange={(e) => handleChange('Fruits', e.target.value)}
                >
                  {DIABETES_FIELD_OPTIONS.YesNoInverted.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="form-field__label" htmlFor="Veggies">Daily Veggie Consumption</label>
                <select
                  id="Veggies"
                  className="nav-link"
                  style={{ width: '100%', borderRadius: '10px', padding: '10px' }}
                  value={profile.Veggies !== undefined ? profile.Veggies : 1}
                  onChange={(e) => handleChange('Veggies', e.target.value)}
                >
                  {DIABETES_FIELD_OPTIONS.YesNoInverted.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-actions" style={{ marginTop: '12px' }}>
              <button
                type="button"
                className="primary-button"
                style={{ flex: 1 }}
                onClick={handleAssess}
                disabled={loading}
              >
                {loading ? 'Calculating Risk…' : 'Assess Risk'}
              </button>
              <button
                type="button"
                className="primary-button primary-button--ghost"
                onClick={loadSample}
              >
                Load Sample Data
              </button>
            </div>
          </div>
        </div>

        {/* Results Card */}
        <div className="result-card" style={{ padding: '24px' }}>
          {!prediction ? (
            <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '48px 20px' }}>
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ margin: '0 auto 12px auto', opacity: 0.6 }}>
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
              <h3 style={{ margin: '0 0 6px 0', color: 'var(--text)' }}>No Assessment Executed</h3>
              <p style={{ fontSize: '0.9rem', margin: 0 }}>
                Adjust patient health profile parameters and click "Assess Risk" to generate diabetes prediction results.
              </p>
            </div>
          ) : (
            <div style={{ display: 'grid', gap: '20px' }}>
              <div style={{ textAlign: 'center', borderBottom: '1px solid var(--border)', paddingBottom: '18px' }}>
                <div style={{ fontSize: '2.8rem', fontWeight: 700, color: 'var(--text)' }}>
                  {Math.round(prediction.risk_probability * 100)}%
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
                  Predicted Diabetes Likelihood
                </div>
                {renderBandPill()}
              </div>

              {/* Top Factors Section */}
              <div>
                <h4 style={{ fontSize: '0.95rem', margin: '0 0 10px 0', color: 'var(--text)' }}>
                  Top Risk Drivers
                </h4>
                <div style={{ display: 'grid', gap: '8px' }}>
                  {prediction.top_factors.map((factor, idx) => {
                    const [key, val] = factor.split(' = ');
                    const label = DIABETES_FACTOR_LABELS[key] || key;
                    return (
                      <div
                        key={idx}
                        style={{
                          display: 'flex',
                          justify: 'space-between',
                          padding: '8px 12px',
                          background: 'var(--surface-muted)',
                          borderRadius: '8px',
                          border: '1px solid var(--border)',
                          fontSize: '0.88rem'
                        }}
                      >
                        <span style={{ color: 'var(--text-muted)' }}>{label}</span>
                        <strong style={{ color: 'var(--text)' }}>{val}</strong>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* AI Explanation Section */}
              <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <h4 style={{ fontSize: '0.95rem', margin: 0, color: 'var(--text)' }}>
                    Personalized AI Explanation
                  </h4>
                  <span className="risk-pill risk-pill--low" style={{ fontSize: '0.72rem', padding: '2px 8px' }}>
                    GenAI
                  </span>
                </div>

                {explaining ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                    <span className="typing-dot" style={{ background: 'var(--accent)' }} />
                    Generating Clinical AI Explanation…
                  </div>
                ) : explanation ? (
                  <div style={{
                    fontSize: '0.88rem',
                    color: 'var(--text)',
                    background: 'var(--surface-muted)',
                    padding: '14px',
                    borderRadius: '12px',
                    border: '1px solid var(--border)',
                    lineHeight: '1.5',
                    whiteSpace: 'pre-wrap'
                  }}>
                    {explanation}
                  </div>
                ) : (
                  <button
                    type="button"
                    className="primary-button primary-button--ghost"
                    style={{ width: '100%' }}
                    onClick={handleExplain}
                  >
                    Generate AI Explanation
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <div style={{
        fontSize: '0.82rem',
        color: 'var(--text-muted)',
        background: 'var(--surface-muted)',
        padding: '12px 16px',
        borderRadius: '12px',
        border: '1px solid var(--border)',
        marginTop: '12px'
      }}>
        <strong>Clinical Disclaimer:</strong> This risk assessment is a statistical screening decision-support tool. It does not replace formal clinical diagnosis. Please consult a licensed medical provider for diagnostic evaluation.
      </div>
    </div>
  );
}
