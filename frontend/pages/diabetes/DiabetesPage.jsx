/**
 * Diabetes Risk Classifier Page
 * 
 * A standalone page for assessing diabetes risk based on health profile inputs.
 * Uses the FastAPI backend at /diabetes endpoints.
 */

import { useState, useEffect } from 'react';
import { checkHealth, predictRisk, explainRisk } from '../../services/diabetes/api';

// CSS styles scoped to .diabetes-app namespace to prevent style bleeding
const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#f3f6f4',
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  },
  header: {
    background: '#ffffff',
    borderBottom: '1px solid #d9e3df',
    padding: '18px 24px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    position: 'sticky',
    top: 0,
    zIndex: 10,
  },
  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: '11px',
  },
  brandMark: {
    width: '34px',
    height: '34px',
    borderRadius: '9px',
    background: 'linear-gradient(135deg, #0f766e, #0b544e)',
    display: 'grid',
    placeItems: 'center',
    color: '#fff',
    fontWeight: 600,
    fontSize: '18px',
  },
  wrap: {
    maxWidth: '1080px',
    margin: '0 auto',
    padding: '32px 24px 80px',
  },
  intro: {
    marginBottom: '28px',
    maxWidth: '620px',
  },
  eyebrow: {
    fontSize: '12px',
    textTransform: 'uppercase',
    letterSpacing: '0.14em',
    color: '#0f766e',
    fontWeight: 600,
    marginBottom: '10px',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
    gap: '22px',
    alignItems: 'start',
  },
  card: {
    background: '#ffffff',
    border: '1px solid #d9e3df',
    borderRadius: '14px',
    boxShadow: '0 1px 2px rgba(18,33,31,.04), 0 8px 24px rgba(18,33,31,.06)',
    padding: '24px',
  },
  field: {
    marginBottom: '15px',
  },
  label: {
    display: 'block',
    fontSize: '13px',
    fontWeight: 500,
    marginBottom: '6px',
  },
  select: {
    width: '100%',
    padding: '9px 11px',
    fontSize: '14px',
    border: '1px solid #d9e3df',
    borderRadius: '9px',
    background: '#fff',
  },
  input: {
    width: '100%',
    padding: '9px 11px',
    fontSize: '14px',
    border: '1px solid #d9e3df',
    borderRadius: '9px',
    background: '#fff',
  },
  row2: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '12px',
  },
  btn: {
    width: '100%',
    marginTop: '8px',
    padding: '13px',
    fontSize: '15px',
    fontWeight: 600,
    color: '#fff',
    background: '#0f766e',
    border: 'none',
    borderRadius: '10px',
    cursor: 'pointer',
  },
  btnGhost: {
    background: 'transparent',
    color: '#0f766e',
    border: '1px solid #d9e3df',
    marginTop: '10px',
    padding: '13px',
    width: '100%',
    borderRadius: '10px',
    cursor: 'pointer',
  },
  resultEmpty: {
    textAlign: 'center',
    color: '#3d514d',
    padding: '40px 20px',
  },
  gaugeWrap: {
    textAlign: 'center',
    padding: '8px 0 4px',
  },
  bandPill: {
    display: 'inline-block',
    padding: '5px 14px',
    borderRadius: '20px',
    fontSize: '13px',
    fontWeight: 600,
    margin: '10px 0 4px',
  },
  factors: {
    marginTop: '18px',
    borderTop: '1px solid #d9e3df',
    paddingTop: '16px',
  },
  explain: {
    marginTop: '18px',
    borderTop: '1px solid #d9e3df',
    paddingTop: '16px',
  },
  disclaimer: {
    marginTop: '22px',
    fontSize: '12px',
    color: '#3d514d',
    background: '#f3f6f4',
    padding: '12px 14px',
    borderRadius: '10px',
    border: '1px solid #d9e3df',
  },
  backBtn: {
    background: 'transparent',
    color: '#0f766e',
    border: '1px solid #d9e3df',
    padding: '8px 16px',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  conn: {
    display: 'flex',
    alignItems: 'center',
    gap: '7px',
    fontSize: '12.5px',
    color: '#3d514d',
    background: '#f3f6f4',
    padding: '6px 12px',
    borderRadius: '20px',
    border: '1px solid #d9e3df',
  },
  dot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    background: '#b6c2bd',
  },
  dotLive: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    background: '#2f8f6b',
    boxShadow: '0 0 0 3px #e5f3ec',
  },
};

const BAND_COLORS = {
  Low: { bg: '#e5f3ec', color: '#2f8f6b' },
  Moderate: { bg: '#fbf1dc', color: '#c98a1a' },
  High: { bg: '#f8e6df', color: '#c0492f' },
};

const FIELDS = [
  'HighBP', 'HighChol', 'CholCheck', 'BMI', 'Smoker', 'Stroke',
  'HeartDiseaseorAttack', 'PhysActivity', 'Fruits', 'Veggies', 'HvyAlcoholConsump',
  'AnyHealthcare', 'NoDocbcCost', 'GenHlth', 'MentHlth', 'PhysHlth', 'DiffWalk',
  'Sex', 'Age', 'Education', 'Income'
];

const DEFAULTS = {
  CholCheck: 1, Stroke: 0, HvyAlcoholConsump: 0, AnyHealthcare: 1,
  NoDocbcCost: 0, MentHlth: 2, PhysHlth: 3, Education: 4, Income: 5
};

export default function DiabetesPage({ onBackToLanding }) {
  const [live, setLive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [explaining, setExplaining] = useState(false);
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
  }

  async function handleAssess() {
    setLoading(true);
    try {
      const fullProfile = { ...DEFAULTS, ...profile };
      const result = await predictRisk(fullProfile);
      setPrediction(result);
    } catch (error) {
      alert('Prediction failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleExplain() {
    if (!prediction) return;
    setExplaining(true);
    try {
      const fullProfile = { ...DEFAULTS, ...profile };
      const result = await explainRisk(fullProfile);
      setExplanation(result.explanation);
    } catch (error) {
      alert('Explanation failed: ' + error.message);
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
  }

  const renderBandPill = () => {
    if (!prediction) return null;
    const colors = BAND_COLORS[prediction.risk_band] || BAND_COLORS.Low;
    return (
      <span style={{ ...styles.bandPill, background: colors.bg, color: colors.color }}>
        {prediction.risk_band} risk · {prediction.risk_label}
      </span>
    );
  };

  return (
    <div className="diabetes-app" style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <div style={styles.brand}>
          <div style={styles.brandMark}>D</div>
          <div>
            <h1 style={{ fontSize: '19px', fontWeight: 600, letterSpacing: '-.01em' }}>
              Diabetes Risk Classifier
            </h1>
            <span style={{ color: '#3d514d', fontSize: '12.5px', display: 'block', marginTop: '-2px' }}>
              Personal Chronic Disease Risk Monitor
            </span>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={styles.conn}>
            <span style={live ? styles.dotLive : styles.dot}></span>
            <span>{live ? 'Backend connected' : 'Demo mode (backend offline)'}</span>
          </div>
          <button onClick={onBackToLanding} style={styles.backBtn}>
            ← Back
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div style={styles.wrap}>
        <div style={styles.intro}>
          <div style={styles.eyebrow}>Diabetes module</div>
          <h2 style={{ fontFamily: "'Fraunces', Georgia, serif", fontWeight: 500, fontSize: '30px', lineHeight: 1.15, marginBottom: '10px' }}>
            Know your risk between clinic visits.
          </h2>
          <p style={{ color: '#3d514d', fontSize: '15px' }}>
            Enter your health profile to see your diabetes risk, understand what's driving it,
            and get guidance on what to do next. This is a screening aid, not a diagnosis.
          </p>
        </div>

        <div style={styles.grid}>
          {/* Input Card */}
          <div style={styles.card}>
            <h3 style={{ fontFamily: "'Fraunces', Georgia, serif", fontWeight: 500, fontSize: '18px', marginBottom: '4px' }}>
              Your health profile
            </h3>
            <p style={{ color: '#3d514d', fontSize: '13px', marginBottom: '18px' }}>
              All fields use the same scales as your health record.
            </p>

            <div style={styles.row2}>
              <div style={styles.field}>
                <label style={styles.label}>General health</label>
                <select
                  id="GenHlth"
                  style={styles.select}
                  value={profile.GenHlth || 3}
                  onChange={(e) => handleChange('GenHlth', e.target.value)}
                >
                  <option value="1">1 — Excellent</option>
                  <option value="2">2 — Very good</option>
                  <option value="3">3 — Good</option>
                  <option value="4">4 — Fair</option>
                  <option value="5">5 — Poor</option>
                </select>
              </div>
              <div style={styles.field}>
                <label style={styles.label}>BMI</label>
                <input
                  type="number"
                  id="BMI"
                  style={styles.input}
                  value={profile.BMI || 28}
                  min="10"
                  max="100"
                  step="0.1"
                  onChange={(e) => handleChange('BMI', e.target.value)}
                />
              </div>
            </div>

            <div style={styles.row2}>
              <div style={styles.field}>
                <label style={styles.label}>Age band</label>
                <select
                  id="Age"
                  style={styles.select}
                  value={profile.Age || 9}
                  onChange={(e) => handleChange('Age', e.target.value)}
                >
                  <option value="1">18–24</option>
                  <option value="2">25–29</option>
                  <option value="3">30–34</option>
                  <option value="4">35–39</option>
                  <option value="5">40–44</option>
                  <option value="6">45–49</option>
                  <option value="7">50–54</option>
                  <option value="8">55–59</option>
                  <option value="9">60–64</option>
                  <option value="10">65–69</option>
                  <option value="11">70–74</option>
                  <option value="12">75–79</option>
                  <option value="13">80+</option>
                </select>
              </div>
              <div style={styles.field}>
                <label style={styles.label}>Biological sex</label>
                <select
                  id="Sex"
                  style={styles.select}
                  value={profile.Sex !== undefined ? profile.Sex : 1}
                  onChange={(e) => handleChange('Sex', e.target.value)}
                >
                  <option value="0">Female</option>
                  <option value="1">Male</option>
                </select>
              </div>
            </div>

            <div style={styles.row2}>
              <div style={styles.field}>
                <label style={styles.label}>High blood pressure</label>
                <select
                  style={styles.select}
                  value={profile.HighBP !== undefined ? profile.HighBP : 1}
                  onChange={(e) => handleChange('HighBP', e.target.value)}
                >
                  <option value="0">No</option>
                  <option value="1">Yes</option>
                </select>
              </div>
              <div style={styles.field}>
                <label style={styles.label}>High cholesterol</label>
                <select
                  style={styles.select}
                  value={profile.HighChol !== undefined ? profile.HighChol : 1}
                  onChange={(e) => handleChange('HighChol', e.target.value)}
                >
                  <option value="0">No</option>
                  <option value="1">Yes</option>
                </select>
              </div>
            </div>

            <div style={styles.row2}>
              <div style={styles.field}>
                <label style={styles.label}>Physically active</label>
                <select
                  style={styles.select}
                  value={profile.PhysActivity !== undefined ? profile.PhysActivity : 1}
                  onChange={(e) => handleChange('PhysActivity', e.target.value)}
                >
                  <option value="1">Yes</option>
                  <option value="0">No</option>
                </select>
              </div>
              <div style={styles.field}>
                <label style={styles.label}>Difficulty walking</label>
                <select
                  style={styles.select}
                  value={profile.DiffWalk !== undefined ? profile.DiffWalk : 1}
                  onChange={(e) => handleChange('DiffWalk', e.target.value)}
                >
                  <option value="0">No</option>
                  <option value="1">Yes</option>
                </select>
              </div>
            </div>

            <div style={styles.row2}>
              <div style={styles.field}>
                <label style={styles.label}>Smoker (100+ in life)</label>
                <select
                  style={styles.select}
                  value={profile.Smoker !== undefined ? profile.Smoker : 1}
                  onChange={(e) => handleChange('Smoker', e.target.value)}
                >
                  <option value="0">No</option>
                  <option value="1">Yes</option>
                </select>
              </div>
              <div style={styles.field}>
                <label style={styles.label}>Heart disease / attack</label>
                <select
                  style={styles.select}
                  value={profile.HeartDiseaseorAttack !== undefined ? profile.HeartDiseaseorAttack : 0}
                  onChange={(e) => handleChange('HeartDiseaseorAttack', e.target.value)}
                >
                  <option value="0">No</option>
                  <option value="1">Yes</option>
                </select>
              </div>
            </div>

            <div style={styles.row2}>
              <div style={styles.field}>
                <label style={styles.label}>Eats fruit daily</label>
                <select
                  style={styles.select}
                  value={profile.Fruits !== undefined ? profile.Fruits : 0}
                  onChange={(e) => handleChange('Fruits', e.target.value)}
                >
                  <option value="1">Yes</option>
                  <option value="0">No</option>
                </select>
              </div>
              <div style={styles.field}>
                <label style={styles.label}>Eats veg daily</label>
                <select
                  style={styles.select}
                  value={profile.Veggies !== undefined ? profile.Veggies : 1}
                  onChange={(e) => handleChange('Veggies', e.target.value)}
                >
                  <option value="1">Yes</option>
                  <option value="0">No</option>
                </select>
              </div>
            </div>

            <button
              style={{ ...styles.btn, opacity: loading ? 0.6 : 1 }}
              onClick={handleAssess}
              disabled={loading}
            >
              {loading ? 'Assessing…' : 'Assess my risk'}
            </button>
            <button style={styles.btnGhost} onClick={loadSample}>
              Fill sample profile
            </button>
          </div>

          {/* Result Card */}
          <div style={styles.card}>
            {!prediction ? (
              <div style={styles.resultEmpty}>
                <svg width="46" height="46" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                </svg>
                <p>Your risk assessment will appear here.</p>
              </div>
            ) : (
              <div>
                <div style={styles.gaugeWrap}>
                  <div style={{ fontSize: '34px', fontWeight: 600, fontFamily: "'Fraunces', Georgia, serif" }}>
                    {Math.round(prediction.risk_probability * 100)}%
                  </div>
                  <div style={{ fontSize: '13px', color: '#3d514d' }}>probability of being at risk</div>
                  {renderBandPill()}
                </div>

                <div style={styles.factors}>
                  <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '10px' }}>
                    What's influencing this most
                  </h4>
                  <div>
                    {prediction.top_factors.map((factor, idx) => {
                      const [key, val] = factor.split(' = ');
                      const labels = {
                        GenHlth: 'General health', HighBP: 'High blood pressure', BMI: 'BMI',
                        HighChol: 'High cholesterol', Age: 'Age band', DiffWalk: 'Difficulty walking'
                      };
                      return (
                        <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13.5px', padding: '6px 0', color: '#3d514d' }}>
                          <span>{labels[key] || key}</span>
                          <b style={{ color: '#12211f', fontWeight: 500 }}>{val}</b>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div style={styles.explain}>
                  <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '7px' }}>
                    Personalised explanation
                    <span style={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '.1em', background: '#0f766e', color: '#fff', padding: '2px 7px', borderRadius: '5px', fontWeight: 600 }}>
                      Gen AI
                    </span>
                  </h4>
                  {explaining ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#3d514d', fontSize: '14px' }}>
                      <div style={{ width: '16px', height: '16px', border: '2px solid #d9e3df', borderTopColor: '#0f766e', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }}></div>
                      Generating your explanation…
                    </div>
                  ) : explanation ? (
                    <div style={{ fontSize: '14px', color: '#3d514d', whiteSpace: 'pre-wrap' }}>
                      {explanation.split('\n\n').map((p, i) => <p key={i} style={{ marginBottom: '10px' }}>{p.replace(/\n/g, '<br>')}</p>)}
                    </div>
                  ) : (
                    <button style={styles.btnGhost} onClick={handleExplain}>
                      Generate AI Explanation
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        <div style={styles.disclaimer}>
          <strong>Important:</strong> This is a screening tool that estimates statistical risk from your health
          profile. It does not diagnose any condition. For medical concerns, consult a GP, polyclinic, or specialist.
        </div>
      </div>

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        .diabetes-app select:focus, .diabetes-app input:focus {
          outline: none;
          border-color: #0f766e;
          box-shadow: 0 0 0 3px #e5f3ec;
        }
        .diabetes-app button:hover {
          opacity: 0.9;
        }
      `}</style>
    </div>
  );
}
